"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - URLs & basic test data access
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import pytest

from core.fixture.shared import config


# ═══════════════════════════════════════════════════════════════
# SERVICE URL FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def frontend_url() -> str:
    """获取前端服务 URL"""
    return config.get_service_url("frontend")


@pytest.fixture(scope="session")
def backend_url() -> str:
    """获取后端服务 URL"""
    return config.get_service_url("backend")


@pytest.fixture(scope="session")
def current_environment() -> str:
    """获取当前环境名称"""
    return config.get_environment()


# ═══════════════════════════════════════════════════════════════
# TEST DATA FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_config():
    """测试配置 fixture"""
    return config


@pytest.fixture(scope="session")
def accounts_pool():
    """测试账号池 fixture - 获取完整账号池"""
    data = config.load_test_data("accounts")
    if data and "test_account_pool" in data:
        return data["test_account_pool"]
    return []


@pytest.fixture(scope="function")
def test_data():
    """
    通用测试数据加载器 fixture

    使用方式:
        def test_xxx(test_data):
            orders = test_data("orders")
            products = test_data("products")
    """

    def _load_data(name: str):
        return config.load_test_data(name)

    return _load_data


