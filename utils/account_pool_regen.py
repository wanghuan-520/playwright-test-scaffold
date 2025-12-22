"""
# ═══════════════════════════════════════════════════════════════
# Account Pool Regenerator (backend register)
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 使用后端注册接口批量生成测试账号
# - 直接重建 test-data/test_account_pool.json（旧文件做时间戳备份）
#
# 设计要点：
# - 只依赖公开接口：POST /api/account/register
# - 生成强密码（尽量满足 ABP Identity 默认策略）
# - 失败可检证：打印每个账号注册结果与失败原因
#
"""

import argparse
import json
import os
import random
import shutil
import ssl
import string
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.config import ConfigManager


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _ssl_ctx() -> ssl.SSLContext:
    # 本地 https 自签，预期跳过校验
    return ssl._create_unverified_context()


def _post_json(url: str, payload: Dict[str, Any], timeout_s: int = 20) -> Tuple[int, str]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _rand_suffix(k: int = 6) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(k))


def _strong_password() -> str:
    # 尽量覆盖：大写/小写/数字/特殊字符，且长度足够
    return "Aa1!Aa1!Aa1!"


def _register_one(
    *,
    backend_url: str,
    app_name: str,
    username: str,
    email: str,
    password: str,
) -> Tuple[bool, str]:
    url = f"{backend_url.rstrip('/')}/api/account/register"
    payload = {"userName": username, "emailAddress": email, "password": password, "appName": app_name}
    st, body = _post_json(url, payload, timeout_s=25)
    if st == 200:
        return True, "ok"
    # 兜底：返回体通常是 RemoteServiceErrorResponse
    reason = f"status={st}"
    if body:
        reason = f"{reason} body={body[:300]}"
    return False, reason


def _write_pool_file(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}.{int(time.time()*1000)}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 简单校验：确保非空
    parsed = json.loads(tmp.read_text(encoding="utf-8"))
    if not parsed.get("test_account_pool"):
        raise RuntimeError("refuse to write empty test_account_pool")
    os.replace(str(tmp), str(path))


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Regenerate test account pool via backend register API.")
    p.add_argument("--count", type=int, default=int(os.getenv("POOL_SIZE", "20")), help="How many accounts to create.")
    p.add_argument("--prefix", default=os.getenv("POOL_PREFIX", "qatest__"), help="Username prefix.")
    p.add_argument("--domain", default=os.getenv("POOL_EMAIL_DOMAIN", "testmail.com"), help="Email domain.")
    p.add_argument("--app-name", default=os.getenv("POOL_APP_NAME", "Aevatar"), help="RegisterDto.appName.")
    p.add_argument("--password", default=os.getenv("POOL_PASSWORD", _strong_password()), help="Password for all accounts.")
    p.add_argument("--out", default="", help="Pool json output path (default from config).")
    args = p.parse_args(argv)

    cfg = ConfigManager()
    backend = (cfg.get_service_url("backend") or "").rstrip("/")
    if not backend:
        print("❌ backend url is empty (config.environments.dev.backend.url)")
        return 2

    out_path = Path(args.out or cfg.get_test_data_path("accounts"))
    if out_path.exists():
        backup = out_path.with_suffix(out_path.suffix + f".backup.{_now_ts()}")
        try:
            shutil.copy2(out_path, backup)
            print(f"ℹ️  backup: {backup}")
        except Exception as e:
            print(f"⚠️  backup failed: {type(e).__name__}: {e}")

    want = max(int(args.count), 1)
    created: List[Dict[str, Any]] = []
    failures: List[str] = []

    # 避免与历史账号冲突：加上时间戳段
    seed = datetime.now().strftime("%m%d%H%M")

    i = 0
    attempts = 0
    while len(created) < want and attempts < want * 5:
        attempts += 1
        i += 1
        uname = f"{args.prefix}{seed}{i:03d}_{_rand_suffix(3)}"
        email = f"{uname}@{args.domain}"
        ok, reason = _register_one(
            backend_url=backend,
            app_name=args.app_name,
            username=uname,
            email=email,
            password=args.password,
        )
        if ok:
            print(f"✅ register ok: {uname}")
            created.append(
                {
                    "username": uname,
                    "email": email,
                    "password": args.password,
                    "initial_password": args.password,
                    "in_use": False,
                    "is_locked": False,
                    "last_used": None,
                }
            )
        else:
            print(f"❌ register failed: {uname} {reason}")
            failures.append(f"{uname}: {reason}")

    if len(created) < want:
        print(f"❌ only created {len(created)}/{want}. See failures above.")
        return 1

    pool_config = {
        "pool_size": want,
        "auto_register_fallback": True,
        "cleanup_after_test": True,
        "account_prefix": str(args.prefix),
        "account_lock_wait_time": 300,
        "max_retry_on_lock": 3,
    }
    data = {"test_account_pool": created, "pool_config": pool_config}
    _write_pool_file(out_path, data)
    print(f"✅ wrote pool file: {out_path} accounts={len(created)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

