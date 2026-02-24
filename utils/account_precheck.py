"""
Account pool precheck CLI + 兼容导出。
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional

from utils.account_precheck_http import _abp_cookie_login_and_roles
from utils.account_precheck_runner import PrecheckResult, check_one_account, precheck_account_pool
from utils.config import ConfigManager

__all__ = [
    "PrecheckResult",
    "check_one_account",
    "precheck_account_pool",
    "_abp_cookie_login_and_roles",
    "main",
]


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

