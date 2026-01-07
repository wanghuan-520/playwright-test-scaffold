#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin Users Tests - Local Conftest
确保使用账号池中的 10 个 admin 账号
"""

import pytest
from pages.login_page import LoginPage
from pages.admin_users_page import AdminUsersPage
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def admin_account_pool():
    """
    获取所有可用的 admin 账号
    
    Returns:
        list: admin 账号列表
    """
    dm = DataManager()
    pool_data = dm._load_account_pool()
    accounts = pool_data.get("test_account_pool", [])
    
    # 过滤出所有 admin 账号
    admin_accounts = [
        acc for acc in accounts 
        if acc.get("role") == "admin"
    ]
    
    logger.info(f"账号池中共有 {len(admin_accounts)} 个 admin 账号")
    
    if not admin_accounts:
        pytest.fail("账号池中没有 admin 账号，请检查配置")
    
    return admin_accounts


@pytest.fixture
def admin_page(page, admin_account_pool, request):
    """
    使用 admin 账号登录的页面
    
    每个测试会从 admin 账号池中获取一个账号并登录
    不依赖父级 auth_storage_state，确保使用 admin 权限
    
    Args:
        page: Playwright page 实例
        admin_account_pool: admin 账号池
        request: pytest request 对象
        
    Yields:
        AdminUsersPage: 已登录的 AdminUsersPage 实例
    """
    # 获取第一个可用的 admin 账号
    account = None
    for acc in admin_account_pool:
        if not acc.get("in_use") and not acc.get("is_locked"):
            account = acc
            break
    
    if not account:
        # 如果所有账号都在使用中，使用第一个（并行测试场景）
        account = admin_account_pool[0]
        logger.warning(f"所有 admin 账号都在使用中，复用账号: {account['username']}")
    
    logger.info(f"测试 {request.node.name} 使用 admin 账号: {account['username']}")
    
    # 登录
    try:
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(
            username=account["username"], 
            password=account["password"]
        )
        logger.info(f"✅ Admin 账号登录成功: {account['username']}")
        
        # 返回 AdminUsersPage 实例
        admin_users_page = AdminUsersPage(page)
        
        yield admin_users_page
        
    except Exception as e:
        logger.error(f"❌ Admin 账号登录失败: {account['username']}, 错误: {e}")
        raise
    
    finally:
        # 测试结束后不需要清理（账号会被 DataManager 自动管理）
        logger.debug(f"测试 {request.node.name} 完成，使用的账号: {account['username']}")


@pytest.fixture
def admin_users_page(admin_page):
    """
    AdminUsersPage fixture（兼容现有测试）
    
    直接返回 admin_page，保持向后兼容
    """
    return admin_page

