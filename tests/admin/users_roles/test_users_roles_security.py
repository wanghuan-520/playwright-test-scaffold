# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - Security Tests
# ═══════════════════════════════════════════════════════════════
"""
Security 级别测试：角色管理页面安全测试

测试点：
- XSS 防护
- SQLi 防护
- 未授权访问

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
from utils.config import ConfigManager


# ═══════════════════════════════════════════════════════════════
# Security - XSS 防护
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Roles")
@allure.story("Security - XSS 防护")
@allure.title("test_security_xss_no_dialog - XSS payload 不应触发 dialog")
def test_security_xss_no_dialog(auth_page: Page):
    """
    验证：
    1. XSS payload 输入到搜索框
    2. 不触发 alert/confirm/prompt 对话框
    3. 页面不崩溃
    """
    logger = TestLogger("test_security_xss_no_dialog")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    dialog_triggered = {"value": False}
    
    def on_dialog(dialog):
        dialog_triggered["value"] = True
        dialog.dismiss()
    
    auth_page.on("dialog", on_dialog)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
    
    payloads = [
        "<img src=x onerror=alert(1)>",
        "' OR 1=1 --",
        "<script>alert(1)</script>",
    ]
    
    with allure.step("注入 XSS/SQLi payload"):
        # 如果页面有搜索框
        search_box = auth_page.locator('role=searchbox').first
        if search_box.count() > 0:
            for payload in payloads:
                try:
                    search_box.fill(payload)
                    auth_page.wait_for_timeout(200)
                except Exception:
                    pass
        step_shot(page_obj, "step_xss_payload")
    
    with allure.step("验证 XSS 未执行"):
        assert dialog_triggered["value"] is False, "XSS payload 触发了 dialog"
        assert page_obj.is_loaded(), "页面应该正常加载"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Security - 未授权访问
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.security
@allure.feature("Admin Roles")
@allure.story("Security - 未授权访问")
@allure.title("test_security_unauth_redirect - 未登录访问应重定向到登录页")
def test_security_unauth_redirect(unauth_page: Page):
    """
    验证：
    1. 未登录状态访问 /admin/roles
    2. 应重定向到登录页
    """
    logger = TestLogger("test_security_unauth_redirect")
    logger.start()
    
    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{base}/admin/roles"
    
    page = unauth_page
    
    with allure.step("未登录状态访问 /admin/roles"):
        page.goto(url, wait_until="commit", timeout=60000)
        page.wait_for_timeout(2000)
    
    with allure.step("验证重定向到登录页"):
        current = page.url or ""
        
        # 检查是否重定向到登录页或显示 403
        is_login_redirect = "/login" in current.lower() or "/auth/login" in current.lower()
        page_text = page.text_content("body") or ""
        is_403 = "403" in page_text or "Access Denied" in page_text
        
        allure.attach(f"当前 URL: {current}", "current_url")
        
        screenshot = page.screenshot(full_page=True)
        allure.attach(screenshot, "step_unauth_access", allure.attachment_type.PNG)
        
        assert is_login_redirect or is_403, \
            f"未登录应重定向到登录页或显示 403，当前: {current}"
    
    logger.end(success=True)
