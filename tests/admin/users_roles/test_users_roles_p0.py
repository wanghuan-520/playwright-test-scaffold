# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：角色管理页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- 角色列表显示

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_roles_page import AdminRolesPage
from tests.admin.users_roles._helpers import (
    assert_not_redirected_to_login,
    step_shot,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# P0 - 页面加载
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_roles_page_load - 页面可打开且核心控件可见")
def test_p0_roles_page_load(auth_page: Page):
    """
    验证：
    1. 页面可导航到 /admin/roles
    2. 页面标题 "Roles" 可见
    3. Create Role 按钮可见
    4. 角色卡片可见
    """
    logger = TestLogger("test_p0_roles_page_load")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        step_shot(page_obj, "step_navigate")
    
    with allure.step("验证页面加载成功"):
        assert page_obj.is_loaded(), "页面未加载完成"
    
    with allure.step("验证核心控件可见"):
        assert page_obj.is_visible(page_obj.CREATE_ROLE_BUTTON, timeout=5000), "Create Role 按钮不可见"
        step_shot(page_obj, "step_verify_controls")
    
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_roles_list_display - 角色列表显示")
def test_p0_roles_list_display(auth_page: Page):
    """
    验证：
    1. member 和 admin 角色存在
    2. 角色卡片显示用户数量
    """
    logger = TestLogger("test_p0_roles_list_display")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("等待角色列表加载"):
        roles_loaded = page_obj.wait_for_roles_loaded(timeout=10000)
        step_shot(page_obj, "step_roles_list")
        
        if not roles_loaded:
            allure.attach("角色列表未加载，可能是后端 API 问题", "api_issue")
            assert False, "角色列表未加载（后端 API 问题）"
    
    with allure.step("验证角色列表"):
        role_count = page_obj.get_role_count()
        allure.attach(f"角色数量: {role_count}", "role_count")
        assert role_count >= 2, "至少应该有 member 和 admin 两个角色"
    
    with allure.step("验证 member 和 admin 角色存在"):
        assert page_obj.is_visible(page_obj.MEMBER_ROLE_CARD, timeout=3000), "member 角色不可见"
        assert page_obj.is_visible(page_obj.ADMIN_ROLE_CARD, timeout=3000), "admin 角色不可见"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P0 - 权限控制
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P0
@allure.feature("Admin Roles")
@allure.story("P0 - 权限控制")
@allure.title("test_p0_non_admin_access_denied - 非 admin 用户无法访问")
def test_p0_non_admin_access_denied(browser):
    """
    验证：
    1. 非 admin 用户（普通 member）访问 /admin/roles 返回 403
    
    实现说明：
    - 使用普通 member 账号登录
    - 访问 /admin/roles
    - 验证显示 403 Access Denied
    """
    from core.fixture.shared import config, data_manager
    
    logger = TestLogger("test_p0_non_admin_access_denied")
    logger.start()
    
    frontend_url = config.get_service_url('frontend')
    
    # 获取普通账号（非 admin）
    member_account = data_manager.get_test_account(
        "test_p0_roles_non_admin_access", 
        account_type="default"  # 使用普通 member 账号
    )
    
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
        
        with allure.step("访问 /admin/roles"):
            page.goto(f"{frontend_url}/admin/roles", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1500)
            
            # 截图
            screenshot = page.screenshot(full_page=True)
            allure.attach(screenshot, "step_access_denied", allure.attachment_type.PNG)
        
        with allure.step("验证非 admin 用户无法访问 /admin/roles"):
            current_url = page.url or ""
            page_text = page.text_content("body") or ""
            
            # 方式1：被重定向到登录页（前端路由守卫）
            redirected_to_login = "/login" in current_url and "/admin/roles" not in current_url
            # 方式2：显示 403 / Access Denied 页面
            has_403 = "403" in page_text
            has_access_denied = "access denied" in page_text.lower()
            has_permission_error = "permission" in page_text.lower() or "unauthorized" in page_text.lower()
            
            allure.attach(
                f"当前URL: {current_url}\n"
                f"重定向到登录页: {redirected_to_login}\n"
                f"403: {has_403}, Access Denied: {has_access_denied}, Permission: {has_permission_error}",
                "验证结果",
                allure.attachment_type.TEXT,
            )
            
            assert redirected_to_login or has_403 or has_access_denied or has_permission_error, \
                f"非 admin 用户应该无法访问 /admin/roles（预期: 重定向到登录页 或 403），当前页面: {current_url}"
        
        logger.end(success=True)
        
    finally:
        # 清理
        try:
            data_manager.cleanup_after_test("test_p0_roles_non_admin_access", success=True)
        except Exception:
            pass
        ctx.close()
