# ═══════════════════════════════════════════════════════════════
# Framework Tests - Conftest
# ═══════════════════════════════════════════════════════════════
"""框架单元测试专用 conftest

提供：
- 通用 fixtures
- 测试环境隔离
"""

import pytest
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_data_dir(tmp_path):
    """创建临时数据目录"""
    data_dir = tmp_path / "test-data"
    data_dir.mkdir()
    return data_dir

