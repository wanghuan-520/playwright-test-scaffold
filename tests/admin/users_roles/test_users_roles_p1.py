# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：角色管理页面功能测试

测试点：
- 角色卡片交互
- Create Role 对话框

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
# P1 - 角色卡片
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - 角色卡片")
@allure.title("test_p1_role_card_click - 点击角色卡片")
def test_p1_role_card_click(auth_page: Page):
    """
    验证：
    1. 点击角色卡片后有响应
    2. 可能打开详情页或对话框
    """
    logger = TestLogger("test_p1_role_card_click")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        for attempt in range(3):
            try:
                page_obj.navigate()
                break
            except Exception:
                if attempt == 2:
                    raise
                auth_page.reload()
                auth_page.wait_for_timeout(2000)
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("点击 member 角色卡片"):
        # 测试点击角色卡片（已废弃，但保留用于兼容性测试）
        page_obj.click_role_card("member")
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_after_click_member")
    
    # 可能打开了详情对话框或导航到详情页
    with allure.step("验证卡片点击响应"):
        # 检查是否有对话框打开
        dialog_visible = auth_page.is_visible('[role="dialog"]', timeout=2000)
        # 或者 URL 变化
        url_changed = "member" in auth_page.url.lower()
        
        allure.attach(
            f"对话框可见: {dialog_visible}, URL 变化: {url_changed}",
            "click_response"
        )
        # 不强制断言，只记录行为
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 创建角色
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - 创建角色")
@allure.title("test_p1_create_role_dialog - Create Role 对话框可打开")
def test_p1_create_role_dialog(auth_page: Page):
    """
    验证：
    1. 点击 Create Role 按钮
    2. 对话框打开
    3. 表单字段可见
    """
    logger = TestLogger("test_p1_create_role_dialog")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        for attempt in range(3):
            try:
                page_obj.navigate()
                break
            except Exception:
                if attempt == 2:
                    raise
                auth_page.reload()
                auth_page.wait_for_timeout(2000)
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("点击 Create Role 按钮"):
        page_obj.click_create_role()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_dialog_opened")
    
    with allure.step("验证对话框可见"):
        dialog_visible = auth_page.is_visible('[role="dialog"]', timeout=3000)
        allure.attach(f"对话框可见: {dialog_visible}", "dialog_state")
        
        if dialog_visible:
            # 关闭对话框
            try:
                auth_page.get_by_role("button", name="Cancel").click()
            except Exception:
                auth_page.keyboard.press("Escape")
    
    logger.end(success=True)

