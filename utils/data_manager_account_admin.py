"""
DataManager 账号管理扩展能力。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional


class DataManagerAccountAdmin:
    """为 DataManager 提供账号状态维护方法。"""

    def mark_account_locked(self, username: str, reason: str = "") -> bool:
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            for account in pool:
                if account.get("username") == username:
                    account["is_locked"] = True
                    account["in_use"] = False
                    account["locked_reason"] = (reason or "")[:300]
                    self._save_account_pool(data, lock_acquired=True)
                    self._logger.warning(
                        f"账号已标记为不可用: {username} reason={account.get('locked_reason')}"
                    )
                    return True
            return False

    def reset_account_password(self, username: str, new_password: str) -> bool:
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            for account in pool:
                if account.get("username") != username:
                    continue
                if "initial_password" not in account:
                    account["initial_password"] = account["password"]
                account["password"] = new_password
                account["is_locked"] = False
                account.pop("locked_reason", None)
                self._save_account_pool(data, lock_acquired=True)
                self._logger.info(f"已重置账号密码: {username}")
                return True
            self._logger.warning(f"未找到账号: {username}")
            return False

    def restore_account_to_initial_state(self, username: str) -> bool:
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            for account in pool:
                if account.get("username") != username:
                    continue
                if "initial_password" in account:
                    account["password"] = account["initial_password"]
                    self._logger.info(f"恢复账号 {username} 的密码到初始值")
                account["in_use"] = False
                account["is_locked"] = False
                account.pop("locked_reason", None)
                account.pop("test_name", None)
                self._save_account_pool(data, lock_acquired=True)
                self._logger.info(f"账号 {username} 已恢复到初始状态")
                return True
            self._logger.warning(f"未找到账号: {username}")
            return False

    def get_test_account_info(self, test_name: str) -> Optional[Dict[str, str]]:
        return self._test_accounts.get(test_name)

    def _touch_last_used(self, account: dict) -> None:
        account["last_used"] = datetime.now().isoformat()
