"""
# ═══════════════════════════════════════════════════════════════
# Account Pool Precheck (xdist-safe)
# ═══════════════════════════════════════════════════════════════

目的：
- 跑前预检账号池：自动验证是否能登录、打印 roles、把无效/不满足本套用例要求的账号标记出来
- 避免 pytest-xdist 并发时在 setup 阶段盲撞账号池（导致大量 setup error/超时）

实现原则：
- **可检证**：输出清晰摘要（可重定向到 logs）
- **不误伤**：只在“明确无效/明确不满足要求”时标记 is_locked
- **进程安全**：更新账号池文件时使用 DataManager 的进程锁
"""

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import json as _json
import http.cookiejar
import ssl
import urllib.request
import urllib.error
from urllib.parse import urlencode

from utils.config import ConfigManager
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PrecheckResult:
    username: str
    email: str
    ok: bool
    reason: str
    roles: List[str]
    authenticated: bool


def _looks_like_admin_role(roles: List[str]) -> bool:
    r = {str(x).lower() for x in (roles or [])}
    return bool(r & {"admin", "administrator", "superadmin"})


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _http_post_form(url: str, data: Dict[str, str], headers: Optional[Dict[str, str]] = None, timeout_s: int = 15) -> Tuple[int, str]:
    ctx = ssl._create_unverified_context()
    body = urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("content-type", "application/x-www-form-urlencoded")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _http_post_json(
    url: str,
    payload: Dict[str, Any],
    *,
    opener: Optional[urllib.request.OpenerDirector] = None,
    timeout_s: int = 20,
) -> Tuple[int, str]:
    ctx = ssl._create_unverified_context()
    body = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("content-type", "application/json")
    try:
        if opener is None:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
                raw = r.read()
                return r.status, raw.decode("utf-8", "ignore")
        with opener.open(req, timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout_s: int = 15) -> Tuple[int, str]:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _abp_application_configuration(
    backend_url: str,
    *,
    access_token: Optional[str] = None,
    opener: Optional[urllib.request.OpenerDirector] = None,
) -> Tuple[bool, List[str], bool, str]:
    """
    拉取 ABP application-configuration 并提取 roles。
    返回 (ok, roles, authenticated, reason)
    """
    url = f"{backend_url.rstrip('/')}/api/abp/application-configuration"
    headers = {"authorization": f"Bearer {access_token}"} if access_token else None
    if opener is None:
        st, body = _http_get(url, headers=headers, timeout_s=20)
    else:
        # opener（带 cookie）时必须走 opener.open 才会携带 cookie
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, method="GET")
        try:
            with opener.open(req, timeout=20) as r:
                raw = r.read()
                st, body = r.status, raw.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            raw = b""
            try:
                raw = e.read()
            except Exception:
                pass
            st, body = e.code, raw.decode("utf-8", "ignore")
    if st != 200:
        return False, [], False, f"abp_cfg_status={st}"
    try:
        j = _json.loads(body)
        cu = j.get("currentUser") or {}
        authenticated = bool(cu.get("isAuthenticated"))
        roles = cu.get("roles") or []
        return True, [str(x) for x in roles], authenticated, "ok"
    except Exception:
        return False, [], False, "abp_cfg_parse_error"

def _classify_abp_login_result(body_text: str) -> str:
    """
    /api/account/login 与 /api/account/check-password 返回 AbpLoginResult:
      {"result": <int>, "description": "<text>"}
    """
    try:
        j = _json.loads(body_text or "{}")
    except Exception:
        j = {}
    desc = str(j.get("description") or "")
    blob = desc.lower()
    if "invalidusernameorpassword" in blob:
        return "invalid_credentials"
    if "lockedout" in blob:
        return "lockout"
    if desc:
        return f"login_{desc}"
    return "login_unknown"


def _abp_cookie_login_and_roles(
    *,
    backend_url: str,
    identifier: str,
    password: str,
) -> Tuple[bool, str, List[str], bool]:
    """
    不依赖 OIDC client：
    1) POST /api/account/login（JSON）
    2) 复用 cookie GET /api/abp/application-configuration，读取 roles
    """
    ctx = ssl._create_unverified_context()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
    )

    login_url = f"{backend_url.rstrip('/')}/api/account/login"
    payload = {"userNameOrEmailAddress": identifier, "password": password, "rememberMe": False}
    st, body = _http_post_json(login_url, payload, opener=opener, timeout_s=20)
    if st != 200:
        return False, f"login_status={st}", [], False

    reason = _classify_abp_login_result(body)
    # 经验：成功一般是 Success；其它都当失败
    if reason != "login_Success":
        return False, reason, [], False

    ok_cfg, roles, authenticated, reason_cfg = _abp_application_configuration(backend_url, opener=opener)
    if not ok_cfg:
        return False, reason_cfg, roles, authenticated
    if not authenticated:
        return False, "not_authenticated", roles, False
    return True, "ok", roles, True


def check_one_account(
    frontend_url: str,
    personal_settings_path: str,
    username: str,
    email: str,
    password: str,
    require_admin_for_admin_path: bool = False,
    backend_url: str = "",
) -> PrecheckResult:
    """
    验证单个账号：
    - 能否通过后端 /api/account/login 登录（cookie）
    - 能否从 /api/abp/application-configuration 读取 currentUser.roles
    - /admin 路由是否需要 admin 账号：以实际环境为准（默认不强制）
    """
    identifier = (email or username).strip()
    if not identifier or not password:
        return PrecheckResult(username=username, email=email, ok=False, reason="missing_credentials", roles=[], authenticated=False)

    requires_admin = personal_settings_path.startswith("/admin")

    if not backend_url:
        return PrecheckResult(username=username, email=email, ok=False, reason="missing_backend_url", roles=[], authenticated=False)

    ok, reason, roles, authenticated = _abp_cookie_login_and_roles(backend_url=backend_url, identifier=identifier, password=password)
    if not ok:
        return PrecheckResult(username=username, email=email, ok=False, reason=reason, roles=roles, authenticated=authenticated)

    if require_admin_for_admin_path and requires_admin and (not _looks_like_admin_role(roles)):
        return PrecheckResult(username=username, email=email, ok=False, reason=f"not_admin(roles={roles})", roles=roles, authenticated=True)

    return PrecheckResult(username=username, email=email, ok=True, reason="ok", roles=roles, authenticated=True)


def precheck_account_pool(
    *,
    frontend_url: str,
    personal_settings_path: str,
    need_usable: int,
    update_pool: bool,
    lock_not_admin: bool,
    backend_url: str,
) -> Dict[str, Any]:
    """
    预检账号池并（可选）回写标记：
    - invalid_credentials / lockout -> is_locked=True
    - not_admin -> 可选 is_locked=True（避免被 admin 测试复用）
    """
    dm = DataManager()

    # 读取账号池（进程锁）
    with dm._process_file_lock(), dm._account_pool_lock:
        data = dm._load_account_pool()
        pool: List[Dict[str, Any]] = data.get("test_account_pool", [])

    results: List[PrecheckResult] = []
    usable: List[PrecheckResult] = []

    for acc in pool:
        username = str(acc.get("username") or "")
        email = str(acc.get("email") or "")
        password = str(acc.get("password") or "")

        r = check_one_account(
            frontend_url=frontend_url,
            personal_settings_path=personal_settings_path,
            username=username,
            email=email,
            password=password,
            require_admin_for_admin_path=(
                os.getenv("PRECHECK_REQUIRE_ADMIN", "").strip() in {"1", "true", "True", "yes", "YES"}
            ),
            backend_url=backend_url,
        )
        results.append(r)
        if r.ok:
            usable.append(r)
        else:
            # 配置类问题（不是账号问题）尽快中止，避免“误伤”账号池/浪费时间
            if r.reason in {"missing_backend_url"}:
                raise RuntimeError(f"precheck config error: {r.reason}")
        logger.info(f"[precheck] {username:>12} ok={r.ok} roles={r.roles} reason={r.reason}")

        if need_usable > 0 and len(usable) >= need_usable:
            break

    summary = {
        "ts": _now_iso(),
        "frontend": frontend_url,
        "personal_settings_path": personal_settings_path,
        "need_usable": need_usable,
        "checked": len(results),
        "usable": len([r for r in results if r.ok]),
        "reasons": {},
        "usable_accounts": [{"username": r.username, "email": r.email, "roles": r.roles} for r in usable],
    }

    reasons: Dict[str, int] = {}
    for r in results:
        reasons[r.reason] = reasons.get(r.reason, 0) + 1
    summary["reasons"] = reasons

    if update_pool:
        with dm._process_file_lock(), dm._account_pool_lock:
            data2 = dm._load_account_pool()
            pool2: List[Dict[str, Any]] = data2.get("test_account_pool", [])
            by_user = {str(a.get("username")): a for a in pool2}

            for r in results:
                a = by_user.get(r.username)
                if not a:
                    continue
                # 统一清理运行态字段，避免残留污染
                a["in_use"] = False
                if "test_name" in a:
                    del a["test_name"]
                a["last_checked"] = summary["ts"]

                if r.ok:
                    a["is_locked"] = False
                    if "locked_reason" in a:
                        del a["locked_reason"]
                    a["roles"] = r.roles
                    continue

                # 需要锁定的场景
                lock = False
                if r.reason in {"invalid_credentials", "lockout"}:
                    lock = True
                if r.reason.startswith("not_admin(") and lock_not_admin:
                    lock = True

                if lock:
                    a["is_locked"] = True
                    a["locked_reason"] = f"precheck:{r.reason}"[:300]
                else:
                    # 不锁：只记录原因，留给后续人工或其它测试使用
                    a["roles"] = r.roles
                    a["precheck_note"] = f"{r.reason}"[:300]

            dm._save_account_pool(data2, lock_acquired=True)

    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Account pool precheck (login/roles) and optional update.")
    parser.add_argument("--frontend", default="", help="Frontend base url (default from config). e.g. https://localhost:3000")
    parser.add_argument("--backend", default="", help="Backend base url (default from config). e.g. https://localhost:44320")
    parser.add_argument("--path", dest="personal_settings_path", default=os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile"))
    parser.add_argument("--need", type=int, default=int(os.getenv("PRECHECK_NEED", "4")), help="Stop after finding N usable accounts.")
    parser.add_argument("--no-update", action="store_true", help="Do not write back to account pool json.")
    parser.add_argument("--no-lock-not-admin", action="store_true", help="Do not lock non-admin accounts.")
    args = parser.parse_args(argv)

    cfg = ConfigManager()
    frontend = (args.frontend or cfg.get_service_url("frontend") or "").rstrip("/")
    backend = (args.backend or cfg.get_service_url("backend") or "").rstrip("/")
    if not frontend:
        print("❌ frontend url is empty. Provide --frontend or configure environments.dev.frontend.url")
        return 2
    if not backend:
        print("❌ backend url is empty. Provide --backend or configure environments.dev.backend.url")
        return 2
    try:
        summary = precheck_account_pool(
            frontend_url=frontend,
            backend_url=backend,
            personal_settings_path=args.personal_settings_path,
            need_usable=max(args.need, 0),
            update_pool=not args.no_update,
            lock_not_admin=not args.no_lock_not_admin,
        )
    except RuntimeError as e:
        print(f"❌ precheck failed: {e}")
        print("   请检查 backend url 配置是否正确。")
        return 2

    print("\n=== precheck summary ===")
    for k, v in summary.items():
        if k == "usable_accounts":
            continue
        print(f"{k}: {v}")
    print("usable_accounts:")
    for a in summary["usable_accounts"]:
        print(f"  - {a['username']} roles={a.get('roles')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

