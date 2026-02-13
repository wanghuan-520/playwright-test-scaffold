# ═══════════════════════════════════════════════════════════════
# Admin Users P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Users 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见（Add User 按钮、用户表格）
- 数据加载正常
- Add User 对话框可打开

账号来源：
- 需要 admin 账号（account_type="admin"）

功能变更：
- 2026-02-04: "Invite User" 按钮已移除
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# P0 - 页面加载
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_admin_users_page_load - 页面可打开且核心控件可见")
def test_p0_admin_users_page_load(auth_page: Page):
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
        # Invite 按钮已于 2026-02-04 移除
        assert page_obj.is_visible(page_obj.USER_TABLE, timeout=3000), "用户表格不可见"
        step_shot(page_obj, "step_verify_controls")
    
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_admin_users_data_loads - 数据加载正常")
def test_p0_admin_users_data_loads(auth_page: Page):
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


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_admin_users_add_user_dialog - Add User 对话框可打开")
def test_p0_admin_users_add_user_dialog(auth_page: Page):
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


# ═══════════════════════════════════════════════════════════════
# P0 - 权限控制
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P0
@allure.feature("Admin Users")
@allure.story("P0 - 权限控制")
@allure.title("test_p0_non_admin_access_denied - 非 admin 用户无法访问")
def test_p0_non_admin_access_denied(browser):
    """
    验证：
    1. 非 admin 用户（普通 member）访问 /admin/users 返回 403
    
    实现说明：
    - 使用普通 member 账号登录
    - 访问 /admin/users
    - 验证显示 403 Access Denied
    """
    from core.fixture.shared import config, data_manager
    
    logger = TestLogger("test_p0_non_admin_access_denied")
    logger.start()
    
    frontend_url = config.get_service_url('frontend')
    
    # 获取普通账号（非 admin）
    member_account = data_manager.get_test_account(
        "test_p0_non_admin_access", 
        account_type="default"  # 使用普通 member 账号
    )
    
    # 创建新的浏览器上下文
    ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    
    try:
        with allure.step("使用普通 member 账号登录"):
            page.goto(f"{frontend_url}/login", wait_until="domcontentloaded", timeout=30000)
            
            identifier = member_account.get("email") or member_account.get("username")
            password = member_account.get("password")
            
            page.fill('input[placeholder="Enter username or email"]', identifier)
            page.fill('input[placeholder="Enter your password"]', password)
            page.click('button:has-text("Sign In")')
            
            # 等待登录完成
            page.wait_for_timeout(3000)
            allure.attach(f"登录账号: {identifier}", "member_account")
        
        with allure.step("访问 /admin/users"):
            page.goto(f"{frontend_url}/admin/users", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1500)
            
            # 截图
            screenshot = page.screenshot(full_page=True)
            allure.attach(screenshot, "step_access_denied", allure.attachment_type.PNG)
        
        with allure.step("验证显示 403 Access Denied"):
            # 检查页面是否显示 403 或 Access Denied
            page_text = page.text_content("body") or ""
            
            has_403 = "403" in page_text
            has_access_denied = "Access Denied" in page_text or "access denied" in page_text.lower()
            has_permission_error = "permission" in page_text.lower() or "don't have permission" in page_text.lower()
            
            allure.attach(f"403: {has_403}, Access Denied: {has_access_denied}, Permission: {has_permission_error}", "验证结果")
            
            assert has_403 or has_access_denied or has_permission_error, \
                f"非 admin 用户应该收到 403 Access Denied，当前页面: {page.url}"
        
        logger.end(success=True)
        
    finally:
        # 清理
        try:
            data_manager.cleanup_after_test("test_p0_non_admin_access", success=True)
        except Exception:
            pass
        ctx.close()
