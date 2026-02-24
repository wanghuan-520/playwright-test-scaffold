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
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture(scope="session", autouse=True)
def disable_service_precheck_for_framework_tests():
    """
    框架单元测试默认关闭服务预检。

    目的：
    - framework 测试关注框架代码行为，不应依赖本地 frontend/backend 是否在线
    - 避免 root autouse fixture 触发 fail-fast 导致单测直接退出
    """
    old_precheck_services = os.environ.get("PRECHECK_SERVICES")
    old_precheck_http = os.environ.get("PRECHECK_HTTP")

    os.environ["PRECHECK_SERVICES"] = "0"
    os.environ["PRECHECK_HTTP"] = "0"
    yield

    if old_precheck_services is None:
        os.environ.pop("PRECHECK_SERVICES", None)
    else:
        os.environ["PRECHECK_SERVICES"] = old_precheck_services

    if old_precheck_http is None:
        os.environ.pop("PRECHECK_HTTP", None)
    else:
        os.environ["PRECHECK_HTTP"] = old_precheck_http


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

