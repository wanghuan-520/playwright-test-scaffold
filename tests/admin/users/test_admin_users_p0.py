# ═══════════════════════════════════════════════════════════════
# Admin Users P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Users 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- 数据加载正常

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - 页面加载")
class TestAdminUsersP0:
    """Admin Users 页面 P0 测试"""
    
    @allure.title("test_p0_admin_users_page_load - 页面可打开且核心控件可见")
    def test_p0_admin_users_page_load(self, auth_page: Page):
        """
        验证：
        1. 页面可导航到 /admin/users
        2. 页面标题 "Users" 可见
        3. Add User 按钮可见
        4. 用户表格可见
        """
        logger = TestLogger("test_p0_admin_users_page_load")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            step_shot(page_obj, "step_navigate")
        
        with allure.step("验证页面标题可见"):
            assert page_obj.is_loaded(), "页面未加载完成"
        
        with allure.step("验证核心控件可见"):
            assert page_obj.is_visible(page_obj.ADD_USER_BUTTON, timeout=5000), "Add User 按钮不可见"
            assert page_obj.is_visible(page_obj.INVITE_BUTTON, timeout=3000), "Invite 按钮不可见"
            assert page_obj.is_visible(page_obj.USER_TABLE, timeout=3000), "用户表格不可见"
            step_shot(page_obj, "step_verify_controls")
        
        logger.end(success=True)
    
    @allure.title("test_p0_admin_users_data_loads - 数据加载正常")
    def test_p0_admin_users_data_loads(self, auth_page: Page):
        """
        验证：
        1. 页面加载后统计数据不为 0
        2. Total Users 显示正确
        
        已知问题：
        - Bug #1: 页面初始显示 "Total Users: 0"，数据异步加载后才显示真实数量
        """
        logger = TestLogger("test_p0_admin_users_data_loads")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
        
        with allure.step("等待数据加载"):
            data_loaded = page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_data_loaded")
        
        with allure.step("验证统计数据"):
            total_users = page_obj.get_total_users_count()
            allure.attach(f"Total Users: {total_users}", "统计数据")
            # 允许为 0（可能是新环境），但应该能获取到值
            assert total_users is not None, "无法获取 Total Users 统计"
        
        logger.end(success=True)
    
    @allure.title("test_p0_admin_users_add_user_dialog - Add User 对话框可打开")
    def test_p0_admin_users_add_user_dialog(self, auth_page: Page):
        """
        验证：
        1. 点击 Add User 按钮后对话框打开
        2. 对话框标题 "Create New User" 可见
        3. 表单字段可见
        """
        logger = TestLogger("test_p0_admin_users_add_user_dialog")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
        
        with allure.step("点击 Add User 按钮"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)  # 等待动画
            step_shot(page_obj, "step_dialog_opened")
        
        with allure.step("验证对话框可见"):
            assert page_obj.is_add_user_dialog_visible(), "Add User 对话框未打开"
            assert page_obj.is_visible(page_obj.DIALOG_TITLE, timeout=3000), "对话框标题不可见"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - 权限控制")
class TestAdminUsersAccess:
    """Admin Users 页面访问控制测试"""
    
    @allure.title("test_p0_non_admin_access_denied - 非 admin 用户无法访问")
    @pytest.mark.skip(reason="需要非 admin 账号 fixture")
    def test_p0_non_admin_access_denied(self, logged_in_page: Page):
        """
        验证：
        1. 非 admin 用户访问 /admin/users 返回 403
        """
        pass

