"""
账号预检：结果模型与编排逻辑。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from utils.account_precheck_http import _abp_cookie_login_and_roles
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)
_TRUE_VALUES = {"1", "true", "True", "yes", "YES"}


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


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip() in _TRUE_VALUES


def _should_lock_account(reason: str, lock_not_admin: bool) -> bool:
    return reason in {"invalid_credentials", "lockout"} or (reason.startswith("not_admin(") and lock_not_admin)


def _apply_precheck_result_to_account(
    *,
    account: Dict[str, Any],
    result: PrecheckResult,
    summary_ts: str,
    lock_not_admin: bool,
) -> None:
    account["in_use"] = False
    account.pop("test_name", None)
    account["last_checked"] = summary_ts
    account["roles"] = result.roles

    if result.ok:
        account["is_locked"] = False
        account.pop("locked_reason", None)
        account.pop("precheck_note", None)
        return

    if _should_lock_account(result.reason, lock_not_admin):
        account["is_locked"] = True
        account["locked_reason"] = f"precheck:{result.reason}"[:300]
        account.pop("precheck_note", None)
        return

    account["precheck_note"] = f"{result.reason}"[:300]


def check_one_account(
    # 兼容参数：保留 frontend_url，避免外部调用方签名破坏。
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
    """
    identifier = (email or username).strip()
    if not identifier or not password:
        return PrecheckResult(username=username, email=email, ok=False, reason="missing_credentials", roles=[], authenticated=False)

    requires_admin = personal_settings_path.startswith("/admin")
    if not backend_url:
        return PrecheckResult(username=username, email=email, ok=False, reason="missing_backend_url", roles=[], authenticated=False)

    ok, reason, roles, authenticated = _abp_cookie_login_and_roles(
        backend_url=backend_url, identifier=identifier, password=password
    )
    if not ok:
        return PrecheckResult(username=username, email=email, ok=False, reason=reason, roles=roles, authenticated=authenticated)

    if require_admin_for_admin_path and requires_admin and (not _looks_like_admin_role(roles)):
        return PrecheckResult(
            username=username,
            email=email,
            ok=False,
            reason=f"not_admin(roles={roles})",
            roles=roles,
            authenticated=True,
        )
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
    with dm._process_file_lock(), dm._account_pool_lock:
        data = dm._load_account_pool()
        pool: List[Dict[str, Any]] = data.get("test_account_pool", [])

    results: List[PrecheckResult] = []
    usable: List[PrecheckResult] = []
    require_admin = _env_flag("PRECHECK_REQUIRE_ADMIN")

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
            require_admin_for_admin_path=require_admin,
            backend_url=backend_url,
        )
        results.append(r)
        if r.ok:
            usable.append(r)
        elif r.reason in {"missing_backend_url"}:
            raise RuntimeError(f"precheck config error: {r.reason}")

        logger.info(f"[precheck] {username:>12} ok={r.ok} roles={r.roles} reason={r.reason}")
        if need_usable > 0 and len(usable) >= need_usable:
            break

    reasons: Dict[str, int] = {}
    for r in results:
        reasons[r.reason] = reasons.get(r.reason, 0) + 1

    summary = {
        "ts": _now_iso(),
        "frontend": frontend_url,
        "personal_settings_path": personal_settings_path,
        "need_usable": need_usable,
        "checked": len(results),
        "usable": len(usable),
        "reasons": reasons,
        "usable_accounts": [{"username": r.username, "email": r.email, "roles": r.roles} for r in usable],
    }

    if update_pool:
        with dm._process_file_lock(), dm._account_pool_lock:
            data2 = dm._load_account_pool()
            pool2: List[Dict[str, Any]] = data2.get("test_account_pool", [])
            by_user = {str(a.get("username")): a for a in pool2}

            for r in results:
                a = by_user.get(r.username)
                if not a:
                    continue
                _apply_precheck_result_to_account(
                    account=a,
                    result=r,
                    summary_ts=summary["ts"],
                    lock_not_admin=lock_not_admin,
                )

            dm._save_account_pool(data2, lock_acquired=True)

    return summary
