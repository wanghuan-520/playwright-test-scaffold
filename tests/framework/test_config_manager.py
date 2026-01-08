# ═══════════════════════════════════════════════════════════════
# ConfigManager Unit Tests
# ═══════════════════════════════════════════════════════════════
"""ConfigManager 单元测试

测试目标：
- 配置加载（YAML + 环境变量）
- 默认值回退
- 环境切换
- 服务 URL 获取
"""

import os
import pytest
import tempfile
from pathlib import Path


class TestConfigManager:
    """ConfigManager 测试套件"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        from utils.config import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config_data = None
        yield
        ConfigManager._instance = None
        ConfigManager._config_data = None

    # ═══════════════════════════════════════════════════════════════
    # 配置加载测试
    # ═══════════════════════════════════════════════════════════════

    def test_default_config_when_file_missing(self):
        """配置文件不存在时使用默认配置"""
        from utils.config import ConfigManager

        # 重置后创建实例（使用默认路径，但不存在）
        ConfigManager._config_data = None
        config = ConfigManager.__new__(ConfigManager)
        ConfigManager._instance = config
        config._ConfigManager__init_called = False
        ConfigManager._config_data = config._get_default_config()
        
        assert config.get("project.name") == "Test Project"
        assert config.get("project.version") == "1.0.0"

    def test_singleton_pattern(self):
        """单例模式验证"""
        from utils.config import ConfigManager

        config1 = ConfigManager()
        config2 = ConfigManager()
        
        assert config1 is config2

    def test_get_default_value(self):
        """获取不存在的键返回默认值"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    # ═══════════════════════════════════════════════════════════════
    # 值转换测试
    # ═══════════════════════════════════════════════════════════════

    def test_convert_boolean_true(self):
        """布尔值转换：true"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        assert config._convert_value("true") is True
        assert config._convert_value("True") is True
        assert config._convert_value("yes") is True
        assert config._convert_value("1") is True

    def test_convert_boolean_false(self):
        """布尔值转换：false"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        assert config._convert_value("false") is False
        assert config._convert_value("False") is False
        assert config._convert_value("no") is False
        assert config._convert_value("0") is False

    def test_convert_integer(self):
        """整数转换"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        assert config._convert_value("42") == 42
        assert config._convert_value("100") == 100

    def test_convert_float(self):
        """浮点数转换"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        assert config._convert_value("3.14") == 3.14
        assert config._convert_value("0.5") == 0.5

    # ═══════════════════════════════════════════════════════════════
    # 环境变量覆盖测试
    # ═══════════════════════════════════════════════════════════════

    def test_environment_variable_override(self):
        """环境变量覆盖配置"""
        from utils.config import ConfigManager

        os.environ["BROWSER_HEADLESS"] = "false"
        try:
            config = ConfigManager()
            assert config.get("browser.headless") is False
        finally:
            del os.environ["BROWSER_HEADLESS"]

    # ═══════════════════════════════════════════════════════════════
    # 服务 URL 测试
    # ═══════════════════════════════════════════════════════════════

    def test_get_service_url(self):
        """获取服务 URL"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        frontend_url = config.get_service_url("frontend")
        # 默认配置中的前端 URL
        assert frontend_url is not None
        assert "localhost" in frontend_url or frontend_url == ""

    def test_get_environment(self):
        """获取当前环境"""
        from utils.config import ConfigManager

        config = ConfigManager()
        
        env = config.get_environment()
        assert env in ["dev", "staging", "prod", None]
