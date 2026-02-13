# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Role Permissions Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Role Permissions 对话框功能测试

测试点：
- Role Permissions 对话框打开/关闭
- 权限勾选/取消勾选
- Grant All / Revoke All 功能
- 保存权限修改

⚠️ 重要：所有权限操作类测试必须使用临时创建的测试角色，
   禁止修改 admin、member 等系统角色的权限。

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

import time

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_roles_page import AdminRolesPage
from tests.admin.users_roles._helpers import (
    assert_not_redirected_to_login,
    step_shot,
    delete_test_role,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# 辅助：创建临时测试角色
# ═══════════════════════════════════════════════════════════════

def _create_temp_role(auth_page: Page, page_obj: AdminRolesPage) -> str:
    """创建一个临时测试角色，返回角色名称"""
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"perm_test_{unique_suffix}"

    page_obj.navigate()
    page_obj.wait_for_roles_loaded(timeout=10000)
    page_obj.click_create_role()
    page_obj.wait_for_create_role_dialog(timeout=5000)
    auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)

    with auth_page.expect_response(
        lambda r: r.url.endswith("/api/identity/roles") and r.status in [200, 201],
        timeout=10000,
    ):
        page_obj.submit_create_role()

    auth_page.wait_for_timeout(2000)
    # 刷新页面确保角色可见
    page_obj.navigate()
    page_obj.wait_for_roles_loaded(timeout=10000)
    return role_name


# ═══════════════════════════════════════════════════════════════
# P1 - Role Permissions 对话框基础功能
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_role_permissions_dialog_open - Role Permissions 对话框打开")
def test_p1_role_permissions_dialog_open(auth_page: Page):
    """验证：Role Permissions 对话框可以打开（使用临时角色）"""
    logger = TestLogger("test_p1_role_permissions_dialog_open")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    role_name = None

    try:
        with allure.step("创建临时测试角色"):
            role_name = _create_temp_role(auth_page, page_obj)
            allure.attach(f"临时角色: {role_name}", "temp_role", allure.attachment_type.TEXT)

        with allure.step("打开 Role Permissions 对话框"):
            page_obj.open_role_permissions_dialog(role_name)
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("验证对话框打开"):
            has_dialog = auth_page.is_visible('[role="dialog"]', timeout=5000)
            assert has_dialog, "Role Permissions 对话框未打开"

            dialog_text = auth_page.locator('[role="dialog"]').first.text_content() or ""
            has_permissions = "permission" in dialog_text.lower() or "checkbox" in dialog_text.lower()
            dialog_title = auth_page.locator('[role="dialog"] h2, [role="dialog"] h3').first.text_content() or ""
            allure.attach(f"对话框标题: {dialog_title}", "dialog_info", allure.attachment_type.TEXT)
            assert has_permissions, f"对话框应该包含权限相关内容，实际标题: {dialog_title}"

        with allure.step("验证权限复选框存在"):
            checkboxes = page_obj.get_permission_checkboxes()
            checkbox_count = len(checkboxes)
            assert checkbox_count > 0, f"应该至少有一个权限复选框，实际: {checkbox_count}"
            allure.attach(f"权限复选框数量: {checkbox_count}", "checkbox_count", allure.attachment_type.TEXT)

        with allure.step("关闭对话框"):
            try:
                page_obj.cancel_role_permissions()
            except Exception:
                auth_page.keyboard.press("Escape")

        logger.end(success=True)

    finally:
        if role_name:
            delete_test_role(page_obj, role_name)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_role_permissions_toggle - 权限勾选/取消勾选")
def test_p1_role_permissions_toggle(auth_page: Page):
    """验证：可以勾选和取消勾选权限（使用临时角色，不修改系统角色）"""
    logger = TestLogger("test_p1_role_permissions_toggle")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    role_name = None

    try:
        with allure.step("创建临时测试角色"):
            role_name = _create_temp_role(auth_page, page_obj)

        with allure.step("打开 Role Permissions 对话框"):
            page_obj.open_role_permissions_dialog(role_name)
            auth_page.wait_for_timeout(1000)
            page_obj.wait_for_role_permissions_dialog(timeout=5000)
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("获取第一个权限复选框"):
            dialog = auth_page.locator('[role="dialog"]').first
            checkboxes = dialog.locator('input[type="checkbox"]').all()

            if len(checkboxes) == 0:
                assert False, "对话框中未找到权限复选框"

            first_checkbox = checkboxes[0]
            initial_state = first_checkbox.is_checked()
            allure.attach(f"第一个权限复选框初始状态: {initial_state}", "initial_state", allure.attachment_type.TEXT)

        with allure.step("切换第一个权限复选框状态"):
            first_checkbox.click()
            auth_page.wait_for_timeout(500)
            new_state = first_checkbox.is_checked()
            assert new_state != initial_state, f"权限复选框状态应该切换，初始: {initial_state}, 切换后: {new_state}"
            step_shot(page_obj, "step_toggled")

        with allure.step("恢复原状态"):
            first_checkbox.click()
            auth_page.wait_for_timeout(500)
            restored_state = first_checkbox.is_checked()
            assert restored_state == initial_state, f"应该恢复原状态，期望: {initial_state}, 实际: {restored_state}"

        with allure.step("关闭对话框（不保存）"):
            try:
                page_obj.cancel_role_permissions()
            except Exception:
                auth_page.keyboard.press("Escape")

        logger.end(success=True)

    finally:
        if role_name:
            delete_test_role(page_obj, role_name)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_role_permissions_save - 保存权限修改")
def test_p1_role_permissions_save(auth_page: Page):
    """验证：可以保存权限修改（使用临时角色，不修改系统角色）"""
    logger = TestLogger("test_p1_role_permissions_save")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    role_name = None

    try:
        with allure.step("创建临时测试角色"):
            role_name = _create_temp_role(auth_page, page_obj)

        with allure.step("打开 Role Permissions 对话框"):
            page_obj.open_role_permissions_dialog(role_name)
            auth_page.wait_for_timeout(1000)
            page_obj.wait_for_role_permissions_dialog(timeout=5000)
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("记录初始权限状态"):
            checkboxes = page_obj.get_permission_checkboxes()
            initial_checked = sum(1 for cb in checkboxes if cb.is_checked())
            allure.attach(f"初始选中: {initial_checked}/{len(checkboxes)}", "initial_state", allure.attachment_type.TEXT)

        with allure.step("切换第一个权限的状态"):
            if len(checkboxes) == 0:
                assert False, "没有可用的权限复选框"

            first_checkbox = checkboxes[0]
            first_initial = first_checkbox.is_checked()
            first_checkbox.click()
            auth_page.wait_for_timeout(300)
            first_new = first_checkbox.is_checked()
            assert first_new != first_initial, "权限状态应该切换"
            step_shot(page_obj, "step_permission_toggled")

        with allure.step("保存权限修改"):
            save_button = auth_page.locator(page_obj.ROLE_PERMISSIONS_SAVE_BUTTON).first
            if save_button.is_visible(timeout=2000):
                save_button.click()
                auth_page.wait_for_timeout(2000)
                step_shot(page_obj, "step_saved")
            else:
                assert False, "Save 按钮不可见"

        with allure.step("验证对话框已关闭"):
            auth_page.wait_for_timeout(1000)
            dialog_closed = not auth_page.is_visible('[role="dialog"]', timeout=3000)
            assert dialog_closed, "保存后对话框应该关闭"

        logger.end(success=True)

    finally:
        # 清理临时角色（无论测试结果如何）
        if role_name:
            delete_test_role(page_obj, role_name)
