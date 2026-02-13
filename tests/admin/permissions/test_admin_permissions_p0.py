# ═══════════════════════════════════════════════════════════════
# Admin Permissions P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Permissions 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- Tab 切换正常
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import step_shot, navigate_and_wait
from utils.logger import TestLogger


# ---------------------------------------------------------------------------
# P0 用例：模块级函数，与 P1 一致，Allure 报告不多类名一层
# ---------------------------------------------------------------------------

@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_admin_permissions_page_load - 页面可打开且核心控件可见")
def test_p0_admin_permissions_page_load(auth_page: Page):
    """
    验证：
    1. 页面可导航到 /admin/permissions
    2. 页面标题 "Permissions" 可见
    3. Tab 选项卡可见
    4. 角色选择器可见
    """
    logger = TestLogger("test_p0_admin_permissions_page_load")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_navigate")

    with allure.step("验证页面标题可见"):
        assert page_obj.is_loaded(), "页面未加载完成"

    with allure.step("验证核心控件可见"):
        assert page_obj.is_visible(page_obj.ROLE_PERMISSIONS_TAB, timeout=5000), "Role Permissions Tab 不可见"
        member_btn = auth_page.get_by_role("button", name="member", exact=True)
        assert member_btn.is_visible(), "member 角色按钮不可见"
        step_shot(page_obj, "step_verify_controls")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P0 - 页面加载")
@allure.title("test_p0_admin_permissions_tab_switch - Tab 切换正常")
def test_p0_admin_permissions_tab_switch(auth_page: Page):
    """
    验证：
    1. 可以切换到 User Permissions Tab
    2. 可以切换回 Role Permissions Tab
    """
    logger = TestLogger("test_p0_admin_permissions_tab_switch")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_initial")

    with allure.step("切换到 User Permissions Tab"):
        page_obj.switch_to_user_permissions()
        auth_page.wait_for_timeout(2000)
        step_shot(page_obj, "step_user_permissions_tab")

    with allure.step("切换回 Role Permissions Tab"):
        page_obj.switch_to_role_permissions()
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_role_permissions_tab")

    logger.end(success=True)

