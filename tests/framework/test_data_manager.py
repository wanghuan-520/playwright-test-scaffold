# ═══════════════════════════════════════════════════════════════
# DataManager Unit Tests
# ═══════════════════════════════════════════════════════════════
"""DataManager 单元测试

测试目标：
- 单例模式
- 账号池加载
- 账号分配逻辑
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestDataManagerSingleton:
    """DataManager 单例测试"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        from utils.data_manager import DataManager
        DataManager._instance = None
        yield
        DataManager._instance = None

    def test_singleton_pattern(self):
        """单例模式验证"""
        from utils.data_manager import DataManager

        dm1 = DataManager()
        dm2 = DataManager()
        
        assert dm1 is dm2

    def test_initialization(self):
        """初始化验证"""
        from utils.data_manager import DataManager

        dm = DataManager()
        
        assert dm._initialized is True
        assert hasattr(dm, 'account_pool_path')


class TestAccountPoolOperations:
    """账号池操作测试"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        from utils.data_manager import DataManager
        DataManager._instance = None
        yield
        DataManager._instance = None

    @pytest.fixture
    def temp_account_pool(self, tmp_path):
        """创建临时账号池文件"""
        data = {
            "test_account_pool": [
                {
                    "username": "user1",
                    "email": "user1@test.com",
                    "password": "pass1",
                    "in_use": False,
                    "is_locked": False
                },
                {
                    "username": "user2",
                    "email": "user2@test.com",
                    "password": "pass2",
                    "in_use": True,
                    "is_locked": False
                },
                {
                    "username": "user3",
                    "email": "user3@test.com",
                    "password": "pass3",
                    "in_use": False,
                    "is_locked": True
                }
            ],
            "pool_config": {}
        }
        filepath = tmp_path / "test_accounts.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return str(filepath)

    def test_load_account_pool(self, temp_account_pool):
        """加载账号池"""
        from utils.data_manager import DataManager

        dm = DataManager()
        dm.account_pool_path = temp_account_pool
        
        data = dm._load_account_pool()
        
        assert "test_account_pool" in data
        assert len(data["test_account_pool"]) == 3

    def test_load_nonexistent_account_pool(self):
        """加载不存在的账号池"""
        from utils.data_manager import DataManager

        dm = DataManager()
        dm.account_pool_path = "/nonexistent/path.json"
        
        data = dm._load_account_pool()
        
        assert data == {"test_account_pool": [], "pool_config": {}}

    def test_load_invalid_json(self, tmp_path):
        """加载无效 JSON"""
        from utils.data_manager import DataManager

        filepath = tmp_path / "invalid.json"
        with open(filepath, 'w') as f:
            f.write("{ invalid json }")

        dm = DataManager()
        dm.account_pool_path = str(filepath)
        
        data = dm._load_account_pool()
        
        assert data == {"test_account_pool": [], "pool_config": {}}


class TestAccountAllocation:
    """账号分配测试"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        from utils.data_manager import DataManager
        DataManager._instance = None
        yield
        DataManager._instance = None

    def test_test_accounts_dict_exists(self):
        """_test_accounts 字典存在"""
        from utils.data_manager import DataManager

        dm = DataManager()
        
        assert hasattr(dm, '_test_accounts')
        assert isinstance(dm._test_accounts, dict)
