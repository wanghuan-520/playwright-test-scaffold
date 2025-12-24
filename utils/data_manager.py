# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Data Manager
# ═══════════════════════════════════════════════════════════════
"""
数据管理工具 - 负责测试数据的分配、清理和管理

核心功能:
1. 数据分离 - 每个测试用例使用独立的测试数据
2. 数据清洗 - 测试前后自动清理数据状态
"""

import json
import os
import threading
import fcntl
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pathlib import Path
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class DataManager:
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
        try:
            with open(self.account_pool_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回的数据结构正确
                if "test_account_pool" not in data:
                    logger.warning(f"账号池文件格式异常，缺少test_account_pool字段")
                    return {"test_account_pool": [], "pool_config": {}}
                return data
        except FileNotFoundError:
            logger.error(f"账号池文件不存在: {self.account_pool_path}")
            return {"test_account_pool": [], "pool_config": {}}
        except json.JSONDecodeError as e:
            logger.error(f"账号池文件JSON格式错误: {e}")
            return {"test_account_pool": [], "pool_config": {}}
        except Exception as e:
            logger.error(f"加载账号池失败: {e}")
            return {"test_account_pool": [], "pool_config": {}}
    
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
                self._do_save_account_pool(data)
            else:
                # 需要获取锁
                with self._account_pool_lock:
                    self._do_save_account_pool(data)
        except Exception as e:
            logger.error(f"保存账号池失败: {e}")
    
    def _do_save_account_pool(self, data: Dict[str, Any]) -> None:
        """实际执行保存操作（必须在持有锁的情况下调用）"""
        # 验证数据完整性
        if "test_account_pool" not in data:
            logger.error(f"保存失败：数据缺少test_account_pool字段")
            return
        
        pool = data.get("test_account_pool", [])
        if len(pool) == 0:
            logger.warning(f"警告：尝试保存空的账号池，这可能是个错误")
            # 不保存空数据，避免清空账号池
            return
        
        # 创建备份
        backup_path = f"{self.account_pool_path}.backup"
        if os.path.exists(self.account_pool_path):
            import shutil
            try:
                shutil.copy2(self.account_pool_path, backup_path)
            except Exception as e:
                logger.warning(f"创建备份失败: {e}")
        
        # 保存数据（使用原子写入，防止文件损坏）
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.account_pool_path), exist_ok=True)
            
            # 使用进程PID区分临时文件，避免并发冲突
            import time
            temp_file = f"{self.account_pool_path}.tmp.{os.getpid()}.{int(time.time() * 1000000)}"
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 验证临时文件
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                test_pool = test_data.get('test_account_pool', [])
                if len(test_pool) == 0:
                    logger.warning(f"警告：临时文件账号池为空，不替换原文件")
                    os.remove(temp_file)
                    return
            except json.JSONDecodeError as e:
                logger.error(f"临时文件JSON格式错误，不替换原文件: {e}")
                os.remove(temp_file)
                raise
            
            # 验证通过，原子替换
            # 使用 os.replace 进行原子替换（POSIX 保证原子性）
            os.replace(temp_file, self.account_pool_path)
            logger.debug(f"账号池数据已保存（{len(pool)} 个账号）")
        except Exception as e:
            logger.error(f"保存账号池失败: {e}")
            # 清理临时文件（使用模式匹配清理所有可能的临时文件）
            import glob
            for tmp in glob.glob(f"{self.account_pool_path}.tmp.*"):
                try:
                    os.remove(tmp)
                except:
                    pass
            raise
    
    def get_test_account(self, test_name: str) -> Dict[str, str]:
        """
        为测试用例分配独立的测试账号
        
        Args:
            test_name: 测试用例名称（如 "test_p0_change_password_success"）
            
        Returns:
            测试账号信息（username, email, password）
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            # 查找未锁定且未使用的账号
            available_accounts = [
                acc for acc in pool 
                if not acc.get("is_locked", False) and not acc.get("in_use", False)
            ]
            
            if not available_accounts:
                # 如果没有可用账号，尝试清理残留状态
                logger.warning(f"没有可用账号，尝试清理残留状态...")
                current_time = datetime.now()
                stale_threshold = timedelta(minutes=5)  # 5分钟前的账号认为已过期
                
                for account in pool:
                    if account.get("in_use", False):
                        last_used_str = account.get("last_used")
                        if last_used_str:
                            try:
                                last_used = datetime.fromisoformat(last_used_str)
                                if current_time - last_used > stale_threshold:
                                    logger.warning(f"检测到残留账号状态，自动释放: {account.get('username')} (最后使用: {last_used_str})")
                                    account["in_use"] = False
                                    if "test_name" in account:
                                        del account["test_name"]
                                    available_accounts.append(account)
                            except (ValueError, TypeError):
                                logger.warning(f"账号 {account.get('username')} 时间格式异常，自动释放")
                                account["in_use"] = False
                                if "test_name" in account:
                                    del account["test_name"]
                                available_accounts.append(account)
                        else:
                            logger.warning(f"账号 {account.get('username')} 没有 last_used 时间，自动释放")
                            account["in_use"] = False
                            if "test_name" in account:
                                del account["test_name"]
                            available_accounts.append(account)
                
                # 保存清理后的状态
                if available_accounts:
                    self._save_account_pool(data, lock_acquired=True)
            
            # 再次查找可用账号
            # 选择策略：优先选“最久未使用”的账号，避免集中使用同一账号触发后端 lockout
            def _last_used_key(acc):
                last_used = acc.get("last_used")
                if not last_used:
                    # 从未使用过的账号优先（更均匀分摊，降低单账号 lockout 风险）
                    # 若账号确实未注册/不可用，应在失败时通过 mark_account_locked 锁定并跳过。
                    return datetime.min
                try:
                    return datetime.fromisoformat(last_used)
                except Exception:
                    return datetime.min

            candidates = [
                acc for acc in pool
                if not acc.get("is_locked", False) and not acc.get("in_use", False)
            ]
            candidates.sort(key=lambda a: (_last_used_key(a), a.get("username", "")))

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
            raise RuntimeError(f"没有可用的测试账号，测试用例: {test_name}。总账号数: {len(pool)}, 可用: {len(available_accounts)}")
    
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
                        keep_locked = bool(account.get("is_locked")) and bool(account.get("locked_reason"))

                        # 清理状态
                        account["in_use"] = False
                        if not keep_locked:
                            account["is_locked"] = False
                            if "locked_reason" in account:
                                del account["locked_reason"]
                        if "test_name" in account:
                            del account["test_name"]
                        
                        logger.info(f"测试前清理账号: {username} (测试用例: {test_name})")
                        break
                del self._test_accounts[test_name]
            
            # 2. 清理所有残留的 in_use 状态（防止测试异常退出导致账号未释放）
            current_time = datetime.now()
            stale_threshold = timedelta(minutes=30)  # 30分钟前的账号认为已过期
            
            for account in pool:
                if account.get("in_use", False):
                    last_used_str = account.get("last_used")
                    if last_used_str:
                        try:
                            last_used = datetime.fromisoformat(last_used_str)
                            if current_time - last_used > stale_threshold:
                                # 账号使用时间超过阈值，认为是残留状态，释放它
                                logger.warning(f"检测到残留的账号状态，释放账号: {account.get('username')} (最后使用: {last_used_str})")
                                account["in_use"] = False
                                if "test_name" in account:
                                    del account["test_name"]
                        except (ValueError, TypeError):
                            # 如果时间解析失败，也释放账号（可能是异常状态）
                            logger.warning(f"账号 {account.get('username')} 的时间格式异常，释放账号")
                            account["in_use"] = False
                            if "test_name" in account:
                                del account["test_name"]
                    else:
                        # 没有 last_used 时间，认为是异常状态，释放它
                        logger.warning(f"账号 {account.get('username')} 没有 last_used 时间，释放账号")
                        account["in_use"] = False
                        if "test_name" in account:
                            del account["test_name"]
            
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
                    keep_locked = bool(account.get("is_locked")) and bool(account.get("locked_reason"))

                    # 1. 释放账号状态
                    account["in_use"] = False
                    account["last_used"] = datetime.now().isoformat()
                    
                    # 2. 恢复账号到初始状态
                    if not keep_locked:
                        account["is_locked"] = False
                        if "locked_reason" in account:
                            del account["locked_reason"]
                    if "test_name" in account:
                        del account["test_name"]
                    
                    # 3. 恢复账号密码到初始值（如果被修改了）
                    # 注意：这里假设账号池中存储的密码就是初始密码
                    # 如果测试修改了密码，需要恢复到账号池中存储的初始密码
                    if "initial_password" in account:
                        # 如果账号池中有初始密码记录，恢复到初始密码
                        account["password"] = account["initial_password"]
                        logger.info(f"恢复账号 {username} 的密码到初始值")
                    elif account.get("password") != original_password:
                        # 如果当前密码与分配时的密码不同，恢复到原始密码
                        account["password"] = original_password
                        logger.info(f"恢复账号 {username} 的密码到原始值")
                    
                    # 4. 如果测试失败，记录警告
                    if not success:
                        logger.warning(f"测试失败，账号 {username} 可能需要手动检查")
                    
                    logger.info(f"测试后清理账号: {username} (测试用例: {test_name}, 成功: {success})")
                    logger.info(f"账号 {username} 已恢复到初始状态（in_use=False, is_locked=False, 密码已恢复）")
                    break
            
            # 移除测试用例的账号记录
            del self._test_accounts[test_name]
            
            # 保存账号池（已经持有锁，传入lock_acquired=True）
            self._save_account_pool(data, lock_acquired=True)
    
    def mark_account_locked(self, username: str, reason: str = "") -> bool:
        """
        标记账号为不可用（本地账号池层面）。
        
        场景：
        - 账号未在后端注册（Invalid username or password）
        - 账号被后端 lockout（too many invalid attempts）
        
        注意：这里只更新本地账号池状态，不会影响后端账号。
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            for account in pool:
                if account.get("username") == username:
                    account["is_locked"] = True
                    account["in_use"] = False
                    account["locked_reason"] = (reason or "")[:300]
                    self._save_account_pool(data, lock_acquired=True)
                    logger.warning(
                        f"账号已标记为不可用: {username} reason={account.get('locked_reason')}"
                    )
                    return True
            return False
    
    def reset_account_password(self, username: str, new_password: str) -> bool:
        """
        重置账号密码（用于测试后恢复）
        
        Args:
            username: 账号用户名
            new_password: 新密码
            
        Returns:
            是否成功
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            for account in pool:
                if account.get("username") == username:
                    # 如果账号没有初始密码记录，保存当前密码作为初始密码
                    if "initial_password" not in account:
                        account["initial_password"] = account["password"]
                    
                    account["password"] = new_password
                    account["is_locked"] = False
                    if "locked_reason" in account:
                        del account["locked_reason"]
                    
                    self._save_account_pool(data, lock_acquired=True)
                    logger.info(f"已重置账号密码: {username}")
                    return True
            
            logger.warning(f"未找到账号: {username}")
            return False
    
    def restore_account_to_initial_state(self, username: str) -> bool:
        """
        恢复账号到初始状态
        
        用于测试后确保账号恢复到初始状态，包括：
        1. 恢复密码到初始值
        2. 解锁账号
        3. 清除所有状态标记
        
        Args:
            username: 账号用户名
            
        Returns:
            是否成功
        """
        with self._process_file_lock(), self._account_pool_lock:
            data = self._load_account_pool()
            pool = data.get("test_account_pool", [])
            
            for account in pool:
                if account.get("username") == username:
                    # 恢复密码到初始值
                    if "initial_password" in account:
                        account["password"] = account["initial_password"]
                        logger.info(f"恢复账号 {username} 的密码到初始值")
                    
                    # 恢复状态
                    account["in_use"] = False
                    account["is_locked"] = False
                    if "locked_reason" in account:
                        del account["locked_reason"]
                    if "test_name" in account:
                        del account["test_name"]
                    
                    self._save_account_pool(data, lock_acquired=True)
                    logger.info(f"账号 {username} 已恢复到初始状态")
                    return True
            
            logger.warning(f"未找到账号: {username}")
            return False
    
    def get_test_account_info(self, test_name: str) -> Optional[Dict[str, str]]:
        """获取测试用例使用的账号信息"""
        return self._test_accounts.get(test_name)


#
# NOTE:
# - 本项目的 pytest 生命周期（账号分配/清洗/失败诊断）统一在 `core/fixtures.py` 中实现并由根 `conftest.py` 引入。
# - 这里曾经放过 pytest hook，但由于 `utils/` 不是 pytest 插件入口，容易产生“看起来生效但实际不生效”的幽灵 hook。
# - 因此：`utils/data_manager.py` 只保留 DataManager 作为纯工具类，不再承载 pytest hook。
