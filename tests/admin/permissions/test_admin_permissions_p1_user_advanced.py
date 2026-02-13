# ═══════════════════════════════════════════════════════════════
# Admin Permissions - P1 User Permissions 补充测试
# ═══════════════════════════════════════════════════════════════
"""
补充场景（Review 发现的 Gap）：
1. 用户搜索无结果：搜索不存在的用户名 → 列表为空
2. User Tab 权限搜索：右侧 searchbox 过滤权限
3. User Tab Collapse All / Expand All
4. User Tab Save 按钮状态：disabled → enabled → disabled
5. 切换用户 granted 对比：admin 用户 vs 普通用户
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import step_shot, navigate_and_wait
from utils.logger import TestLogger

SAFE_TOGGLE_PERMISSION = "Permission:Sessions"


def _switch_to_user_tab(page_obj: AdminPermissionsPage, auth_page: Page) -> None:
    page_obj.switch_to_user_permissions()


# ═══════════════════════════════════════════════════════════════
# P1 - 用户搜索无结果
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions 补充")
@allure.title("test_p1_user_search_no_results - 搜索不存在的用户")
def test_p1_user_search_no_results(auth_page: Page):
    """
    验证：
    1. 搜索 "zzz_nonexist_999" → 用户列表为空
    2. 清空搜索 → 用户列表恢复
    """
    logger = TestLogger("test_p1_user_search_no_results")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab_loaded")

    with allure.step("记录初始用户数"):
        initial_count = page_obj.get_items_count()
        allure.attach(f"初始用户数: {initial_count}", "initial",
                      allure.attachment_type.TEXT)
        assert initial_count > 0, "初始应有用户"

    with allure.step("搜索不存在的用户"):
        page_obj.search_user("zzz_nonexist_999")
        step_shot(page_obj, "step_no_results")

    with allure.step("验证搜索结果为空"):
        result_count = page_obj.get_items_count()
        allure.attach(f"搜索结果: {result_count} items", "search_results",
                      allure.attachment_type.TEXT)
        assert result_count == 0, \
            f"搜索不存在用户后应为 0 items，实际: {result_count}"

    with allure.step("清空搜索恢复"):
        page_obj.clear_user_search()
        auth_page.wait_for_timeout(1000)
        restored_count = page_obj.get_items_count()
        allure.attach(f"恢复后用户数: {restored_count}", "restored",
                      allure.attachment_type.TEXT)
        assert restored_count > 0, "清空搜索后用户应恢复"
        step_shot(page_obj, "step_search_restored")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - User Tab 权限搜索
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions 补充")
@allure.title("test_p1_user_tab_search_permissions - User Tab 右侧权限搜索")
def test_p1_user_tab_search_permissions(auth_page: Page):
    """
    验证（User Tab 右侧 searchbox 与 Role Tab 对称）：
    1. 选择 admin 用户
    2. 搜索 "Sessions" → checkbox 减少
    3. 清空搜索 → 恢复
    """
    logger = TestLogger("test_p1_user_tab_search_permissions")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("选择 admin 用户"):
        page_obj.search_user("admin")
        auth_page.wait_for_timeout(1000)
        admin_btn = auth_page.get_by_role("button", name="admin", exact=True)
        if admin_btn.count() > 0:
            admin_btn.first.click()
            auth_page.wait_for_timeout(1500)
        page_obj.clear_user_search()
        step_shot(page_obj, "step_admin_user_selected")

    with allure.step("记录搜索前 checkbox 数量"):
        before = page_obj.get_visible_checkbox_count()
        allure.attach(f"搜索前: {before}", "before", allure.attachment_type.TEXT)
        assert before > 0, "应有可见 checkbox"
        step_shot(page_obj, "step_before_search", full_page=True)

    with allure.step("搜索 'Sessions'"):
        page_obj.search_permissions("Sessions")
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_search_sessions")

    with allure.step("验证搜索过滤生效"):
        after = page_obj.get_visible_checkbox_count()
        allure.attach(f"搜索后: {after}", "after", allure.attachment_type.TEXT)
        assert after < before, \
            f"搜索后 checkbox 应减少: {before} -> {after}"

    with allure.step("清空搜索恢复"):
        page_obj.clear_permission_search()
        auth_page.wait_for_timeout(1000)
        restored = page_obj.get_visible_checkbox_count()
        allure.attach(f"清空后: {restored}", "restored", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_search_cleared")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - User Tab Collapse All / Expand All
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions 补充")
@allure.title("test_p1_user_tab_collapse_expand - User Tab 折叠/展开")
def test_p1_user_tab_collapse_expand(auth_page: Page):
    """
    验证（User Tab 右侧 Collapse/Expand 与 Role Tab 对称）：
    1. Collapse All → checkbox 全部隐藏
    2. Expand All → checkbox 恢复可见
    """
    logger = TestLogger("test_p1_user_tab_collapse_expand")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab_loaded", full_page=True)

    with allure.step("记录初始 checkbox 数量"):
        initial = page_obj.get_visible_checkbox_count()
        allure.attach(f"初始: {initial}", "initial", allure.attachment_type.TEXT)
        assert initial > 0, "初始应有可见 checkbox"

    with allure.step("Collapse All"):
        page_obj.click_collapse_all()
        collapsed = page_obj.get_visible_checkbox_count()
        allure.attach(f"折叠后: {collapsed}", "collapsed", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_collapsed")
        assert collapsed == 0, f"折叠后应无 checkbox，实际: {collapsed}"

    with allure.step("Expand All"):
        page_obj.click_expand_all()
        expanded = page_obj.get_visible_checkbox_count()
        allure.attach(f"展开后: {expanded}", "expanded", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_expanded", full_page=True)
        assert expanded > 0, "展开后应有可见 checkbox"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - User Tab Save 按钮状态
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions 补充")
@allure.title("test_p1_user_tab_save_button_state - User Tab Save 状态流转")
def test_p1_user_tab_save_button_state(auth_page: Page):
    """
    验证：
    1. 初始 Save disabled
    2. Toggle 权限 → Save enabled + unsaved 标识
    3. 取消 toggle → Save disabled
    """
    logger = TestLogger("test_p1_user_tab_save_button_state")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("验证初始 Save disabled"):
        assert not page_obj.is_save_button_enabled(), "Save 初始应 disabled"
        step_shot(page_obj, "step_save_disabled")

    with allure.step("Toggle Permission:Sessions"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_toggled_save_enabled")

    with allure.step("验证 Save enabled + unsaved"):
        assert page_obj.is_save_button_enabled(), "修改后 Save 应 enabled"
        assert page_obj.has_unsaved_changes(), "应显示 unsaved 标识"

    with allure.step("取消 toggle 恢复"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_restored")

    with allure.step("验证 Save 恢复 disabled"):
        save_state = page_obj.is_save_button_enabled()
        allure.attach(f"恢复后 Save enabled: {save_state}", "restored",
                      allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 切换用户 granted 对比
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions 补充")
@allure.title("test_p1_user_granted_comparison - admin 与 member 用户 granted 对比")
def test_p1_user_granted_comparison(auth_page: Page):
    """
    验证：
    1. 选择 admin 用户（admin 角色）→ granted = 48（全授权）
    2. 选择 member 用户（member 角色，如 haylee）→ granted < 48
    3. admin > member（admin 角色继承全部权限）
    """
    logger = TestLogger("test_p1_user_granted_comparison")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab_loaded")

    with allure.step("选择 TestAdmin1（admin 角色，列表前部无需搜索）"):
        # TestAdmin1 在列表前部直接可见，不需要搜索
        page_obj.select_user("TestAdmin1")
        admin_granted = page_obj.get_granted_number()
        allure.attach(f"TestAdmin1 (admin 角色) granted: {admin_granted}", "admin_granted",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_admin_user")

    with allure.step("选择 loadtest_user_001（member 角色）"):
        page_obj.select_user("loadtest_user_001")
        member_granted = page_obj.get_granted_number()
        allure.attach(f"loadtest_user_001 (member 角色) granted: {member_granted}", "member_granted",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_member_user")

    with allure.step("验证 admin > member"):
        allure.attach(
            f"admin 用户: {admin_granted} granted\n"
            f"member 用户: {member_granted} granted\n"
            f"差异: {admin_granted - member_granted}",
            "comparison", allure.attachment_type.TEXT,
        )
        assert admin_granted > member_granted, \
            f"admin({admin_granted}) 应 > member({member_granted})"

    with allure.step("验证 admin = 48（全授权）"):
        assert admin_granted == 48, \
            f"admin 用户应全授权(48)，实际: {admin_granted}"

    logger.end(success=True)
