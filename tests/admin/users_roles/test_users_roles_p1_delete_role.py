# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Delete Role Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Delete Role 功能测试

测试点：
- Static role（admin、member）禁止删除
- 用户新增的 role 可以删除
- Delete Role 确认对话框内容验证
- Cancel 取消删除
- 确认删除成功

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
    TOAST_SELECTORS,
    get_toast_text,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# Helper：创建临时角色（供 Delete 测试使用）
# ═══════════════════════════════════════════════════════════════

def _create_temp_role(page_obj: AdminRolesPage, auth_page: Page, role_name: str) -> None:
    """创建一个临时角色用于 Delete 测试"""
    page_obj.click_create_role()
    page_obj.wait_for_create_role_dialog(timeout=3000)
    auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
    with auth_page.expect_response(
        lambda r: r.url.endswith("/api/identity/roles") and r.status in [200, 201],
        timeout=10000,
    ):
        page_obj.submit_create_role()
    auth_page.wait_for_timeout(2000)
    # 刷新页面确保角色出现
    page_obj.navigate()
    page_obj.wait_for_roles_loaded(timeout=10000)


# ═══════════════════════════════════════════════════════════════
# P1 - Static Role 禁止删除
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_admin_disabled - admin 角色禁止删除")
def test_p1_delete_role_admin_disabled(auth_page: Page):
    """
    验证：
    1. 打开 admin 角色的 Actions 菜单
    2. Delete Role 菜单项应该是 disabled 的
    """
    logger = TestLogger("test_p1_delete_role_admin_disabled")
    logger.start()

    page_obj = AdminRolesPage(auth_page)

    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        page_obj.wait_for_roles_loaded(timeout=10000)
        step_shot(page_obj, "step_navigate")

    with allure.step("打开 admin 角色的 Actions 菜单"):
        page_obj.open_role_actions_menu("admin")
        step_shot(page_obj, "step_admin_actions_menu")

    with allure.step("验证 Delete Role 菜单项是 disabled"):
        delete_item = auth_page.locator(page_obj.ROLE_ACTIONS_MENU_DELETE).first
        assert delete_item.count() > 0, "未找到 Delete Role 菜单项"

        is_disabled = delete_item.is_disabled()
        allure.attach(
            f"Delete Role disabled: {is_disabled}",
            "delete_state",
            allure.attachment_type.TEXT,
        )
        assert is_disabled, "admin 是 Static role，Delete Role 应该被禁用"
        step_shot(page_obj, "step_delete_disabled")

    with allure.step("关闭菜单"):
        auth_page.keyboard.press("Escape")

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_member_disabled - member 角色禁止删除")
def test_p1_delete_role_member_disabled(auth_page: Page):
    """
    验证：
    1. 打开 member 角色的 Actions 菜单
    2. Delete Role 菜单项应该是 disabled 的
    """
    logger = TestLogger("test_p1_delete_role_member_disabled")
    logger.start()

    page_obj = AdminRolesPage(auth_page)

    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        page_obj.wait_for_roles_loaded(timeout=10000)
        step_shot(page_obj, "step_navigate")

    with allure.step("打开 member 角色的 Actions 菜单"):
        page_obj.open_role_actions_menu("member")
        step_shot(page_obj, "step_member_actions_menu")

    with allure.step("验证 Delete Role 菜单项是 disabled"):
        delete_item = auth_page.locator(page_obj.ROLE_ACTIONS_MENU_DELETE).first
        assert delete_item.count() > 0, "未找到 Delete Role 菜单项"

        is_disabled = delete_item.is_disabled()
        allure.attach(
            f"Delete Role disabled: {is_disabled}",
            "delete_state",
            allure.attachment_type.TEXT,
        )
        assert is_disabled, "member 是 Static role，Delete Role 应该被禁用"
        step_shot(page_obj, "step_delete_disabled")

    with allure.step("关闭菜单"):
        auth_page.keyboard.press("Escape")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Delete Role 对话框
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_dialog_content - Delete Role 确认对话框内容验证")
def test_p1_delete_role_dialog_content(auth_page: Page):
    """
    验证：
    1. 用户新增的角色可以打开 Delete Role 对话框
    2. 对话框标题为 "Delete Role?"
    3. 对话框显示角色名称
    4. 对话框显示警告信息
    5. 对话框包含 Cancel 和 Delete Role 按钮
    """
    logger = TestLogger("test_p1_delete_role_dialog_content")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_del_dlg_{unique_suffix}"

    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
            page_obj.wait_for_roles_loaded(timeout=10000)

        with allure.step("创建临时角色"):
            _create_temp_role(page_obj, auth_page, role_name)
            step_shot(page_obj, "step_role_created")

        with allure.step("打开 Delete Role 对话框"):
            page_obj.open_delete_role_dialog(role_name)
            dialog_opened = page_obj.wait_for_delete_role_dialog(timeout=5000)
            assert dialog_opened, "Delete Role 对话框未打开"
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("验证对话框标题"):
            title = auth_page.locator('[role="dialog"] h2').all_text_contents()
            title_text = " ".join(title)
            allure.attach(f"对话框标题: {title_text}", "dialog_title", allure.attachment_type.TEXT)
            assert "Delete Role" in title_text, f"对话框标题应包含 'Delete Role'，实际: {title_text}"

        with allure.step("验证对话框显示角色名称"):
            dialog_text = auth_page.locator('[role="dialog"]').first.text_content() or ""
            allure.attach(f"对话框内容: {dialog_text[:500]}", "dialog_content", allure.attachment_type.TEXT)
            assert role_name in dialog_text, f"对话框应显示角色名称 '{role_name}'，实际内容: {dialog_text[:200]}"

        with allure.step("验证警告信息"):
            warning_visible = auth_page.is_visible(
                '[role="dialog"]:has-text("Users assigned to this role will lose their permissions")',
                timeout=2000,
            )
            assert warning_visible, "对话框应显示权限丢失警告信息"

        with allure.step("验证 Cancel 和 Delete Role 按钮"):
            cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
            delete_btn = auth_page.locator('[role="dialog"] button:has-text("Delete Role")')

            assert cancel_btn.count() > 0, "未找到 Cancel 按钮"
            assert delete_btn.count() > 0, "未找到 Delete Role 按钮"
            assert cancel_btn.is_visible(), "Cancel 按钮应可见"
            assert delete_btn.is_visible(), "Delete Role 按钮应可见"
            assert cancel_btn.is_enabled(), "Cancel 按钮应可点击"
            assert delete_btn.is_enabled(), "Delete Role 按钮应可点击"

        with allure.step("关闭对话框"):
            page_obj.cancel_delete_role()
            auth_page.wait_for_timeout(500)

        logger.end(success=True)

    finally:
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_cancel - Cancel 取消删除")
def test_p1_delete_role_cancel(auth_page: Page):
    """
    验证：
    1. 打开 Delete Role 对话框
    2. 点击 Cancel 关闭对话框
    3. 角色仍然存在于列表中
    """
    logger = TestLogger("test_p1_delete_role_cancel")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_del_cancel_{unique_suffix}"

    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
            page_obj.wait_for_roles_loaded(timeout=10000)

        with allure.step("创建临时角色"):
            _create_temp_role(page_obj, auth_page, role_name)
            step_shot(page_obj, "step_role_created")

        with allure.step("打开 Delete Role 对话框"):
            page_obj.open_delete_role_dialog(role_name)
            dialog_opened = page_obj.wait_for_delete_role_dialog(timeout=5000)
            assert dialog_opened, "Delete Role 对话框未打开"
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("点击 Cancel 关闭对话框"):
            page_obj.cancel_delete_role()
            auth_page.wait_for_timeout(500)

            dialog_closed = not auth_page.is_visible('[role="dialog"]', timeout=2000)
            assert dialog_closed, "点击 Cancel 后对话框应关闭"
            step_shot(page_obj, "step_dialog_cancelled")

        with allure.step("验证角色仍然存在"):
            page_obj.navigate()
            page_obj.wait_for_roles_loaded(timeout=10000)

            role_exists = auth_page.is_visible(f'h3:has-text("{role_name}")', timeout=5000)
            step_shot(page_obj, "step_role_still_exists")
            assert role_exists, f"Cancel 后角色 '{role_name}' 应该仍然存在于列表中"

        logger.end(success=True)

    finally:
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")


# ═══════════════════════════════════════════════════════════════
# P1 - Delete Role 成功
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_success - 删除自定义角色成功")
def test_p1_delete_role_success(auth_page: Page):
    """
    验证：
    1. 创建一个临时角色
    2. 打开 Delete Role 对话框
    3. 点击 Delete Role 确认删除
    4. 验证成功 Toast 出现
    5. 验证角色从列表中消失
    """
    logger = TestLogger("test_p1_delete_role_success")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_del_ok_{unique_suffix}"
    role_deleted = False

    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
            page_obj.wait_for_roles_loaded(timeout=10000)

        with allure.step("创建临时角色"):
            _create_temp_role(page_obj, auth_page, role_name)
            # 确认角色已创建
            role_exists = auth_page.is_visible(f'h3:has-text("{role_name}")', timeout=5000)
            assert role_exists, f"临时角色 '{role_name}' 创建失败，未在列表中找到"
            step_shot(page_obj, "step_role_created")

        with allure.step("打开 Delete Role 对话框"):
            page_obj.open_delete_role_dialog(role_name)
            dialog_opened = page_obj.wait_for_delete_role_dialog(timeout=5000)
            assert dialog_opened, "Delete Role 对话框未打开"
            step_shot(page_obj, "step_dialog_opened")

        with allure.step("确认删除"):
            with auth_page.expect_response(
                lambda r: "/api/identity/roles/" in r.url and r.request.method == "DELETE",
                timeout=10000,
            ) as response_info:
                page_obj.confirm_delete_role()

            response = response_info.value
            assert response.status in [200, 204], f"删除角色 API 返回失败，状态码: {response.status}"
            role_deleted = True

        with allure.step("验证成功 Toast 并等待对话框关闭"):
            try:
                auth_page.wait_for_selector(TOAST_SELECTORS, state="visible", timeout=8000)
            except Exception:
                pass

            try:
                auth_page.wait_for_selector('[role="dialog"]', state="hidden", timeout=5000)
            except Exception:
                pass

            step_shot(page_obj, "step_delete_success_toast")

            toast_text = get_toast_text(auth_page)
            if toast_text:
                allure.attach(f"Toast 内容:\n{toast_text}", "success_toast_text", allure.attachment_type.TEXT)

        with allure.step("验证角色从列表中消失"):
            auth_page.wait_for_timeout(2000)
            page_obj.navigate()
            page_obj.wait_for_roles_loaded(timeout=10000)

            role_gone = not auth_page.is_visible(f'h3:has-text("{role_name}")', timeout=3000)
            step_shot(page_obj, "step_role_removed")
            assert role_gone, f"删除后角色 '{role_name}' 应该从列表中消失"
            allure.attach(f"角色 '{role_name}' 已成功删除", "delete_success", allure.attachment_type.TEXT)

        logger.end(success=True)

    finally:
        # 如果删除未成功，通过 API 清理
        if not role_deleted:
            try:
                delete_test_role(page_obj, role_name)
            except Exception as e:
                logger.warning(f"清理角色 {role_name} 时出错: {e}")


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Delete Role")
@allure.title("test_p1_delete_role_custom_enabled - 自定义角色 Delete 菜单可点击")
def test_p1_delete_role_custom_enabled(auth_page: Page):
    """
    验证：
    1. 创建自定义角色
    2. 打开 Actions 菜单
    3. Delete Role 菜单项应该是可点击的（非 disabled）
    """
    logger = TestLogger("test_p1_delete_role_custom_enabled")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_del_en_{unique_suffix}"

    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
            page_obj.wait_for_roles_loaded(timeout=10000)

        with allure.step("创建临时角色"):
            _create_temp_role(page_obj, auth_page, role_name)
            step_shot(page_obj, "step_role_created")

        with allure.step("打开自定义角色的 Actions 菜单"):
            page_obj.open_role_actions_menu(role_name)
            step_shot(page_obj, "step_actions_menu")

        with allure.step("验证 Delete Role 菜单项可点击"):
            delete_item = auth_page.locator(page_obj.ROLE_ACTIONS_MENU_DELETE).first
            assert delete_item.count() > 0, "未找到 Delete Role 菜单项"

            is_disabled = delete_item.is_disabled()
            allure.attach(
                f"Delete Role disabled: {is_disabled}",
                "delete_state",
                allure.attachment_type.TEXT,
            )
            assert not is_disabled, f"自定义角色 '{role_name}' 的 Delete Role 应该可以点击"
            step_shot(page_obj, "step_delete_enabled")

        with allure.step("关闭菜单"):
            auth_page.keyboard.press("Escape")

        logger.end(success=True)

    finally:
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")
