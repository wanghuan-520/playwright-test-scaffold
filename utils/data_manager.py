"""
数据管理工具 - 负责测试数据的分配、清理和管理

核心功能:
1. 数据分离 - 每个测试用例使用独立的测试数据
2. 数据清洗 - 测试前后自动清理数据状态
"""

import os
import threading
import fcntl
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict
from utils.config import ConfigManager
from utils.logger import get_logger
from utils.account_pool_io import load_account_pool, save_account_pool
from utils.data_manager_account_admin import DataManagerAccountAdmin

logger = get_logger(__name__)


class DataManager(DataManagerAccountAdmin):
    """数据管理器 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = ConfigManager()
        self.account_pool_path = self.config.get_test_data_path("accounts")
        self._logger = logger
        # 使用可重入锁（RLock）避免死锁
        self._account_pool_lock = threading.RLock()
        self._test_accounts = {}  # 存储每个测试用例使用的账号
        
        self._initialized = True
        logger.info("DataManager 初始化完成")

    @contextmanager
    def _process_file_lock(self):
        """
        进程级文件锁：解决 pytest-xdist 多进程并发读写账号池导致的竞态。

        注意：
        - threading.RLock 只能保护“同进程多线程”，无法保护“多进程”
        - 这里用 fcntl.flock 在 macOS/Linux 下提供互斥
        """
        lock_path = f"{self.account_pool_path}.lock"
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
        with open(lock_path, "w", encoding="utf-8") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                yield
            finally:
                try:
                    fcntl.flock(lf, fcntl.LOCK_UN)
                except Exception:
                    pass
    
    def _load_account_pool(self) -> Dict[str, Any]:
        """加载账号池数据"""
        return load_account_pool(self.account_pool_path, self._logger)
    
    def _save_account_pool(self, data: Dict[str, Any], lock_acquired: bool = False) -> None:
        """
        保存账号池数据
        
        Args:
            data: 要保存的数据
            lock_acquired: 是否已经持有锁（避免重复获取锁导致死锁）
        """
        try:
            # 如果已经持有锁，直接保存；否则获取锁后保存
            if lock_acquired:
                # 已经持有锁，直接保存
                save_account_pool(self.account_pool_path, data, self._logger)
            else:
                # 需要获取锁
                with self._account_pool_lock:
                    save_account_pool(self.account_pool_path, data, self._logger)
        except Exception as e:
            logger.error(f"保存账号池失败: {e}")

    def _matches_account_type(self, account: Dict[str, Any], account_type: str) -> bool:
        return account.get("account_type", "default") == account_type

    def _is_available_account(self, account: Dict[str, Any], account_type: str) -> bool:
        return (
            not account.get("is_locked", False)
            and not account.get("in_use", False)
            and self._matches_account_type(account, account_type)
        )

    def _release_usage_mark(self, account: Dict[str, Any]) -> None:
        account["in_use"] = False
        account.pop("test_name", None)

    def _cleanup_stale_in_use_accounts(self, pool: list[Dict[str, Any]], stale_minutes: int) -> int:
        current_time = datetime.now()
        stale_threshold = timedelta(minutes=stale_minutes)
        released = 0

        for account in pool:
            if not account.get("in_use", False):
                continue

            username = account.get("username")
            last_used_str = account.get("last_used")
            if not last_used_str:
                logger.warning(f"账号 {username} 没有 last_used 时间，自动释放")
                self._release_usage_mark(account)
                released += 1
                continue

            try:
                last_used = datetime.fromisoformat(last_used_str)
            except (ValueError, TypeError):
                logger.warning(f"账号 {username} 时间格式异常，自动释放")
                self._release_usage_mark(account)
                released += 1
                continue

            if current_time - last_used > stale_threshold:
                logger.warning(f"检测到残留账号状态，自动释放: {username} (最后使用: {last_used_str})")
                self._release_usage_mark(account)
                released += 1

        return released

    def _keep_locked(self, account: Dict[str, Any]) -> bool:
        return bool(account.get("is_locked")) and bool(account.get("locked_reason"))

    def _release_after_test(self, account: Dict[str, Any], *, keep_locked: bool) -> None:
        self._release_usage_mark(account)
        account["last_used"] = datetime.now().isoformat()
        if not keep_locked:
            account["is_locked"] = False
            account.pop("locked_reason", None)

    def _restore_password_if_needed(self, account: Dict[str, Any], *, original_password: str, username: str) -> None:
        if "initial_password" in account:
            account["password"] = account["initial_password"]
            logger.info(f"恢复账号 {username} 的密码到初始值")
            return
        if account.get("password") != original_password:
            account["password"] = original_password
            logger.info(f"恢复账号 {username} 的密码到原始值")

    def _last_used_key(self, account: Dict[str, Any]) -> datetime:
        last_used = account.get("last_used")
        if not last_used:
            return datetime.min
        try:
            return datetime.fromisoformat(last_used)
        except Exception:
            return datetime.min

    def _log_cleanup_after_test(self, *, username: str, test_name: str, success: bool) -> None:
        if not success:
            logger.warning(f"测试失败，账号 {username} 可能需要手动检查")
        logger.info(f"测试后清理账号: {username} (测试用例: {test_name}, 成功: {success})")
        logger.info(f"账号 {username} 已恢复到初始状态（in_use=False, is_locked=False, 密码已恢复）")
    
    def get_test_account(self, test_name: str, account_type: str = "default") -> Dict[str, str]:
        """
        为测试用例分配独立的测试账号
        
        Args:
            test_name: 测试用例名称（如 "test_p0_change_password_success"）
            account_type: 账号类型（"default" | "ui_login" | "auth"）
                - "default": 通用账号（兼容现有测试）
                - "ui_login": 专用于 logged_in_page fixture（UI 登录链路）
                - "auth": 专用于 auth_page fixture（API 登录链路）
            
        Returns:
            测试账号信息（username, email, password）
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            available_accounts = [acc for acc in pool if self._is_available_account(acc, account_type)]
            
            if not available_accounts:
                # 如果没有可用账号，尝试清理残留状态
                logger.warning(f"没有可用账号（类型: {account_type}），尝试清理残留状态...")
                released = self._cleanup_stale_in_use_accounts(pool, stale_minutes=5)
                available_accounts = [acc for acc in pool if self._is_available_account(acc, account_type)]
                if released > 0:
                    self._save_account_pool(data, lock_acquired=True)
            
            candidates = [
                acc for acc in pool
                if self._is_available_account(acc, account_type)
            ]
            candidates.sort(key=lambda a: (self._last_used_key(a), a.get("username", "")))

            for account in candidates:
                # 标记为使用中
                account["in_use"] = True
                account["last_used"] = datetime.now().isoformat()
                account["test_name"] = test_name

                # 保存账号池（已经持有锁，传入lock_acquired=True）
                self._save_account_pool(data, lock_acquired=True)

                # 记录测试用例使用的账号（保存原始密码，用于测试后恢复）
                account_copy = account.copy()
                # 保存初始密码，用于测试后恢复
                if "initial_password" not in account:
                    account["initial_password"] = account["password"]
                account_copy["initial_password"] = account["initial_password"]
                self._test_accounts[test_name] = account_copy

                logger.info(f"测试用例 {test_name} 分配账号: {account['username']}")
                return {
                    "username": account["username"],
                    "email": account["email"],
                    "password": account["password"]
                }
            
            # 如果还是没有可用账号，抛出异常
            err_msg = (
                f"没有可用的测试账号（类型: {account_type}）。"
                f"测试用例: {test_name}，总账号数: {len(pool)}，可用: {len(available_accounts)}"
            )
            raise RuntimeError(err_msg)
    
    def get_test_account_with_retry(
        self, 
        test_name: str, 
        account_type: str = "default",
        max_retries: int = 3,
        retry_delay_s: float = 0.5
    ) -> Dict[str, str]:
        """
        带重试的账号分配（并发环境下更稳定）
        
        Args:
            test_name: 测试用例名称
            account_type: 账号类型
            max_retries: 最大重试次数（默认 3）
            retry_delay_s: 重试延迟（秒，指数退避）
            
        Returns:
            测试账号信息
            
        Raises:
            RuntimeError: 重试耗尽后仍无可用账号
        """
        import time
        
        for attempt in range(max_retries):
            try:
                account = self.get_test_account(test_name, account_type=account_type)
                if attempt > 0:
                    logger.info(f"✅ 重试成功：第 {attempt + 1} 次尝试分配账号成功")
                return account
            except RuntimeError as e:
                if attempt < max_retries - 1:
                    delay = retry_delay_s * (2 ** attempt)  # 指数退避: 0.5s, 1s, 2s
                    logger.warning(
                        f"⚠️ 账号分配失败（类型: {account_type}），"
                        f"重试 {attempt + 1}/{max_retries}，等待 {delay:.1f}s... "
                        f"原因: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"❌ 账号分配失败：重试 {max_retries} 次后仍无可用账号（类型: {account_type}）")
                    raise
    
    def cleanup_before_test(self, test_name: str) -> None:
        """
        测试前数据清洗
        
        操作:
        1. 释放之前可能未释放的账号（清理残留的 in_use 状态）
        2. 解锁账号（如果被锁定）
        3. 重置账号状态
        4. 确保账号可用
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            # 1. 如果测试用例已有分配的账号，先清理
            if test_name in self._test_accounts:
                account_info = self._test_accounts[test_name]
                username = account_info.get("username")
                
                # 在账号池中找到该账号
                for account in pool:
                    if account.get("username") == username:
                        # 若账号已被明确标记为不可用（invalid_credentials / lockout 等），不要在测试前清理时“解锁”
                        keep_locked = self._keep_locked(account)

                        # 清理状态
                        self._release_usage_mark(account)
                        if not keep_locked:
                            account["is_locked"] = False
                            account.pop("locked_reason", None)
                        
                        logger.info(f"测试前清理账号: {username} (测试用例: {test_name})")
                        break
                del self._test_accounts[test_name]
            
            # 2. 清理所有残留的 in_use 状态（防止测试异常退出导致账号未释放）
            self._cleanup_stale_in_use_accounts(pool, stale_minutes=30)
            
            # 3. 不要在每条用例前“全量解锁”：
            # - is_locked 常用于标记 invalid_credentials / lockout 等不可用账号
            # - 每次清空会导致同一个坏账号被反复分配，造成大量 setup 失败与噪音
            
            # 保存账号池（已经持有锁，传入lock_acquired=True）
            self._save_account_pool(data, lock_acquired=True)
    
    def cleanup_after_test(self, test_name: str, success: bool = True) -> None:
        """
        测试后数据清洗
        
        确保账号恢复到初始状态，以便下次测试可以正常使用
        
        Args:
            test_name: 测试用例名称
            success: 测试是否成功
        """
        with self._process_file_lock(), self._account_pool_lock:
            if test_name not in self._test_accounts:
                logger.warning(f"测试用例 {test_name} 没有分配的账号，跳过清理")
                return
            
            account_info = self._test_accounts[test_name]
            username = account_info.get("username")
            original_password = account_info.get("password")  # 保存原始密码
            
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            # 在账号池中找到该账号
            for account in pool:
                if account.get("username") == username:
                    # 若账号已被明确标记为不可用（invalid/lockout 等），不要在测试后自动“解锁”
                    keep_locked = self._keep_locked(account)

                    # 1. 释放账号状态
                    self._release_after_test(account, keep_locked=keep_locked)
                    
                    # 2. 恢复账号密码到初始值（如果被修改）
                    self._restore_password_if_needed(
                        account,
                        original_password=original_password,
                        username=username,
                    )
                    
                    # 3. 统一收尾日志
                    self._log_cleanup_after_test(username=username, test_name=test_name, success=success)
                    break
            
            # 移除测试用例的账号记录
            del self._test_accounts[test_name]
            
            # 保存账号池（已经持有锁，传入lock_acquired=True）
            self._save_account_pool(data, lock_acquired=True)
    
#
# NOTE:
# - 本项目的 pytest 生命周期（账号分配/清洗/失败诊断）统一在 `core/fixtures.py` 中实现并由根 `conftest.py` 引入。
# - 这里曾经放过 pytest hook，但由于 `utils/` 不是 pytest 插件入口，容易产生“看起来生效但实际不生效”的幽灵 hook。
# - 因此：`utils/data_manager.py` 只保留 DataManager 作为纯工具类，不再承载 pytest hook。
