# ═══════════════════════════════════════════════════════════════
# Admin Permissions - P1 Role Permissions Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Role Permissions Tab 功能测试

元素定位：全部经过 Playwright MCP（2026-02-09）重新验证

角色数据规则（稳定性保障）：
- admin / member 角色：只读验证，绝不修改
- 自定义角色（如 "1"）：可修改，Save 后必须 restore
- 所有 Grant All / Revoke All 测试默认不保存

页面结构（via MCP 2026-02-11）：
  Role Permissions Tab（默认选中）
  左侧：Select Role -> 角色按钮列表 (3 items: "test", "member", "admin")
  右侧：{roleName} Permissions / {N} granted
        [Grant All] [Revoke All] [Collapse All] [Save(disabled)]
        searchbox "Search permissions..."
        7 个权限分组（accordion）：
          身份标识管理 0/11, 设置管理 0/3,
          Permission:Sessions 0/10, Permission:Knowledge 0/6,
          Permission:Platform 0/5, Permission:Agents 0/7,
          Permission:Comments 0/6   → 共 48 权限
"""

from __future__ import annotations

import re
import allure
import pytest
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import (
    assert_not_redirected_to_login,
    step_shot,
    navigate_and_wait,
    TOAST_SELECTORS,
    get_toast_text,
)
from utils.logger import TestLogger


# ── 辅助常量 ──────────────────────────────────────────────────
# 自定义角色名称（MCP 2026-02-11 确认存在，0 granted）
CUSTOM_ROLE = "test"
TOTAL_PERMISSIONS = 48       # 7 组共 48 个权限
TOTAL_GROUPS = 7
# 用于 toggle 测试的安全权限名称
SAFE_TOGGLE_PERMISSION = "Permission:Sessions"


def _find_custom_role(page_obj: AdminPermissionsPage, auth_page: Page) -> str | None:
    """查找一个非 admin / 非 member 的自定义角色"""
    page_obj.get_permission_group_names()  # 确保页面已加载
    # 优先检查默认自定义角色
    for name in [CUSTOM_ROLE, "1", "custom"]:
        btn = auth_page.get_by_role("button", name=name, exact=True)
        if btn.count() > 0 and btn.is_visible():
            return name
    return None


# ═══════════════════════════════════════════════════════════════
# P1 - 角色列表展示
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_role_list_displayed - 角色列表展示")
def test_p1_role_list_displayed(auth_page: Page):
    """
    验证：
    1. Role Permissions Tab 默认选中
    2. 左侧面板显示 "Select Role" 标题和角色数量
    3. member 和 admin 角色按钮可见
    """
    logger = TestLogger("test_p1_role_list_displayed")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面并等待加载"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded")

    with allure.step("验证 Role Permissions Tab 默认选中"):
        assert page_obj.is_role_permissions_tab_selected(), \
            "Role Permissions Tab 应该默认选中"

    with allure.step("验证 Select Role 标题和角色数量可见"):
        assert page_obj.is_visible(page_obj.ROLE_SELECTOR, timeout=3000), \
            "Select Role 标题不可见"
        # MCP 确认有 "3 items" 文本
        items_locator = auth_page.locator('text=/\\d+ items?/')
        assert items_locator.count() > 0, "角色数量文本不可见"
        items_text = items_locator.first.text_content() or ""
        allure.attach(f"角色数量: {items_text}", "role_count", allure.attachment_type.TEXT)

    with allure.step("验证 member 和 admin 角色按钮可见"):
        member_btn = auth_page.get_by_role("button", name="member", exact=True)
        admin_btn = auth_page.get_by_role("button", name="admin", exact=True)
        assert member_btn.is_visible(), "member 角色按钮不可见"
        assert admin_btn.is_visible(), "admin 角色按钮不可见"
        step_shot(page_obj, "step_role_list")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 角色选择与权限加载
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_select_role_loads_permissions - 切换角色加载权限")
def test_p1_select_role_loads_permissions(auth_page: Page):
    """
    验证：
    1. 选择 admin 角色 -> 显示 "48 granted"
    2. 选择 member 角色 -> granted 数量不同
    3. 权限分组和 granted 文本正确更新
    """
    logger = TestLogger("test_p1_select_role_loads_permissions")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择 admin 角色"):
        page_obj.select_admin_role()
        step_shot(page_obj, "step_admin_selected")

    with allure.step("验证 admin 权限统计"):
        granted_text = page_obj.get_granted_count_text()
        allure.attach(f"admin granted: {granted_text}", "admin_granted", allure.attachment_type.TEXT)
        assert "granted" in granted_text, f"应显示 granted 统计，实际: {granted_text}"
        admin_count = page_obj.get_granted_number()
        assert admin_count > 0, f"admin 应有权限，实际: {admin_count}"

    with allure.step("选择 member 角色"):
        page_obj.select_member_role()
        step_shot(page_obj, "step_member_selected")

    with allure.step("验证 member 权限统计"):
        member_granted = page_obj.get_granted_count_text()
        allure.attach(f"member granted: {member_granted}", "member_granted", allure.attachment_type.TEXT)
        assert "granted" in member_granted, f"应显示 granted 统计，实际: {member_granted}"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_admin_role_all_permissions_granted - admin 角色全部授权")
def test_p1_admin_role_all_permissions_granted(auth_page: Page):
    """
    验证：
    1. 选择 admin 角色
    2. 所有权限分组显示 x/x（全部授权）
    """
    logger = TestLogger("test_p1_admin_role_all_permissions_granted")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择 admin 角色"):
        page_obj.select_admin_role()
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_admin_selected", full_page=True)

    with allure.step("验证每个分组均为全部授权"):
        group_names = page_obj.get_permission_group_names()
        allure.attach("\n".join(group_names), "all_groups", allure.attachment_type.TEXT)
        assert len(group_names) > 0, "应有权限分组"

        all_full = True
        for name in group_names:
            # 提取 "x/y" 部分，如 "身份标识管理 11/11" -> "11/11"
            match = re.search(r'(\d+)/(\d+)', name)
            if match:
                granted, total = int(match.group(1)), int(match.group(2))
                if granted != total:
                    all_full = False
                    allure.attach(f"未全授权: {name}", f"incomplete_{name[:15]}",
                                  allure.attachment_type.TEXT)

        assert all_full, "admin 角色所有权限分组应全部授权 (x/x)"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 权限分组展开/折叠
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_permission_groups_displayed - 权限分组展示")
def test_p1_permission_groups_displayed(auth_page: Page):
    """
    验证：
    1. 权限分组以手风琴形式展示，数量 >= 7
    2. 每个分组显示 "分组名 x/y" 格式
    3. 包含 身份标识管理 分组
    """
    logger = TestLogger("test_p1_permission_groups_displayed")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded", full_page=True)

    with allure.step("获取权限分组列表"):
        group_names = page_obj.get_permission_group_names()
        assert len(group_names) > 0, "权限分组列表不应为空"
        allure.attach(
            f"分组数量: {len(group_names)}\n" + "\n".join(group_names),
            "permission_groups", allure.attachment_type.TEXT,
        )

    with allure.step("验证包含核心权限分组"):
        all_text = " ".join(group_names)
        assert "身份标识管理" in all_text or "Identity" in all_text, \
            f"应包含身份标识管理分组，实际: {all_text[:200]}"

    with allure.step("验证分组名称含 x/y 格式"):
        for name in group_names:
            assert re.search(r'\d+/\d+', name), \
                f"分组名应含 x/y 格式，实际: {name}"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_collapse_expand_all - Collapse All / Expand All")
def test_p1_collapse_expand_all(auth_page: Page):
    """
    验证：
    1. Collapse All -> checkbox 全部隐藏，按钮变为 Expand All
    2. Expand All -> checkbox 全部可见，按钮变回 Collapse All
    """
    logger = TestLogger("test_p1_collapse_expand_all")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("记录初始可见 checkbox 数量"):
        initial_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"初始: {initial_count}", "initial_count", allure.attachment_type.TEXT)
        assert initial_count > 0, "初始应有可见 checkbox（默认展开）"

    with allure.step("点击 Collapse All"):
        page_obj.click_collapse_all()
        step_shot(page_obj, "step_collapsed")

    with allure.step("验证 Collapse All 后无可见 checkbox"):
        collapsed_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"折叠后: {collapsed_count}", "collapsed_count", allure.attachment_type.TEXT)
        assert collapsed_count == 0, \
            f"Collapse All 后不应有可见 checkbox，实际: {collapsed_count}"

    with allure.step("验证按钮变为 Expand All"):
        assert page_obj.is_visible(page_obj.EXPAND_ALL_BUTTON, timeout=2000), \
            "按钮应变为 Expand All"

    with allure.step("点击 Expand All"):
        page_obj.click_expand_all()
        step_shot(page_obj, "step_expanded")

    with allure.step("验证 Expand All 后 checkbox 可见"):
        expanded_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"展开后: {expanded_count}", "expanded_count", allure.attachment_type.TEXT)
        assert expanded_count > 0, "Expand All 后应有可见 checkbox"

    with allure.step("验证按钮变回 Collapse All"):
        assert page_obj.is_visible(page_obj.COLLAPSE_ALL_BUTTON, timeout=2000), \
            "按钮应变回 Collapse All"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_toggle_single_group - 单个分组展开/折叠")
def test_p1_toggle_single_group(auth_page: Page):
    """
    验证：
    1. 先 Collapse All
    2. 展开 "设置管理" 分组 -> 有 3 个 checkbox 可见
    3. 再次点击折叠 -> checkbox 隐藏
    """
    logger = TestLogger("test_p1_toggle_single_group")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("Collapse All"):
        page_obj.click_collapse_all()

    with allure.step("展开 设置管理 分组"):
        page_obj.toggle_permission_group("设置管理")
        step_shot(page_obj, "step_settings_expanded")

    with allure.step("验证 设置管理 下有 checkbox 可见"):
        visible = page_obj.get_visible_checkbox_count()
        allure.attach(f"可见 checkbox: {visible}", "visible_count", allure.attachment_type.TEXT)
        # 设置管理有 3 个权限：邮件、邮件测试、时区
        assert visible > 0, "展开分组后应有可见 checkbox"

    with allure.step("折叠 设置管理 分组"):
        page_obj.toggle_permission_group("设置管理")
        auth_page.wait_for_timeout(300)

    with allure.step("验证折叠后无可见 checkbox"):
        collapsed = page_obj.get_visible_checkbox_count()
        assert collapsed == 0, f"折叠后不应有可见 checkbox，实际: {collapsed}"
        step_shot(page_obj, "step_settings_collapsed")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Checkbox 勾选与统计（不保存）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_checkbox_toggle_updates_stats - 勾选权限更新统计")
def test_p1_checkbox_toggle_updates_stats(auth_page: Page):
    """
    验证（使用自定义角色 "1"，0 granted 初始状态）：
    1. 选择自定义角色
    2. 勾选一个权限 -> granted +1，出现 unsaved，Save 变 enabled
    3. 取消勾选 -> 恢复原状
    注意：不点击 Save，通过刷新页面丢弃修改
    """
    logger = TestLogger("test_p1_checkbox_toggle_updates_stats")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择自定义角色"):
        role_name = _find_custom_role(page_obj, auth_page)
        if not role_name:
            pytest.skip("无可用自定义角色（需要非 admin/member 的角色）")
        page_obj.select_role(role_name)
        step_shot(page_obj, "step_role_selected")

    with allure.step("记录初始 granted 数量"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted: {initial}", "initial", allure.attachment_type.TEXT)

    with allure.step("验证 Save 按钮初始为 disabled"):
        assert not page_obj.is_save_button_enabled(), "Save 初始应 disabled"

    with allure.step("勾选 Permission:Sessions 权限"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_checked")

    with allure.step("验证 granted 变化"):
        after_check = page_obj.get_granted_number()
        allure.attach(f"勾选后 granted: {after_check}", "after_check", allure.attachment_type.TEXT)
        assert after_check != initial, \
            f"granted 应变化: 初始={initial} 勾选后={after_check}"

    with allure.step("验证出现 unsaved 标识"):
        assert page_obj.has_unsaved_changes(), "应出现 unsaved 标识"

    with allure.step("验证 Save 按钮变为 enabled"):
        assert page_obj.is_save_button_enabled(), "Save 应变为 enabled"

    with allure.step("取消勾选恢复"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(500)
        restored = page_obj.get_granted_number()
        allure.attach(f"恢复后 granted: {restored}", "restored", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_restored")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Grant All / Revoke All（不保存）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_grant_all_revoke_all - Grant All 和 Revoke All")
def test_p1_grant_all_revoke_all(auth_page: Page):
    """
    验证（使用自定义角色，不保存）：
    1. 选择自定义角色
    2. Grant All -> granted = 48
    3. Revoke All -> granted = 0
    4. 不保存，刷新页面丢弃修改
    """
    logger = TestLogger("test_p1_grant_all_revoke_all")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择自定义角色"):
        role_name = _find_custom_role(page_obj, auth_page)
        if not role_name:
            pytest.skip("无可用自定义角色")
        page_obj.select_role(role_name)
        step_shot(page_obj, "step_role_selected")

    with allure.step("记录初始 granted"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted: {initial}", "initial", allure.attachment_type.TEXT)

    with allure.step("点击 Grant All"):
        page_obj.click_grant_all()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_grant_all", full_page=True)

    with allure.step("验证 Grant All 生效"):
        after_grant = page_obj.get_granted_number()
        allure.attach(f"Grant All 后: {after_grant}", "after_grant", allure.attachment_type.TEXT)
        assert after_grant == TOTAL_PERMISSIONS, \
            f"Grant All 后应为 {TOTAL_PERMISSIONS}，实际: {after_grant}"

    with allure.step("点击 Revoke All"):
        page_obj.click_revoke_all()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_revoke_all", full_page=True)

    with allure.step("验证 Revoke All 生效"):
        after_revoke = page_obj.get_granted_number()
        allure.attach(f"Revoke All 后: {after_revoke}", "after_revoke", allure.attachment_type.TEXT)
        assert after_revoke == 0, \
            f"Revoke All 后应为 0 granted，实际: {after_revoke}"

    # 不保存，刷新丢弃
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 搜索权限
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_search_permissions - 搜索权限过滤")
def test_p1_search_permissions(auth_page: Page):
    """
    验证（使用 admin 角色，只读）：
    1. 搜索 "Sessions" -> 可见 checkbox 减少
    2. 清空搜索 -> 恢复全部
    """
    logger = TestLogger("test_p1_search_permissions")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择 admin 角色（权限最多便于验证搜索）"):
        page_obj.select_admin_role()
        auth_page.wait_for_timeout(1000)

    with allure.step("记录搜索前可见 checkbox 数量"):
        before_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"搜索前: {before_count}", "before", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_before_search")

    with allure.step("搜索 'Sessions'"):
        page_obj.search_permissions("Sessions")
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_search_sessions")

    with allure.step("验证搜索过滤生效"):
        after_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"搜索后: {after_count}", "after", allure.attachment_type.TEXT)
        # 搜索后可见 checkbox 应减少（只显示 Sessions 相关）
        assert after_count < before_count, \
            f"搜索后 checkbox 应减少: {before_count} -> {after_count}"

    with allure.step("清空搜索恢复"):
        page_obj.clear_permission_search()
        auth_page.wait_for_timeout(1000)
        restored_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"清空后: {restored_count}", "restored", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_search_cleared")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Save 按钮状态
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_save_button_state - Save 按钮启用/禁用状态")
def test_p1_save_button_state(auth_page: Page):
    """
    验证（使用自定义角色，不保存）：
    1. 初始 Save disabled
    2. 勾选权限 -> Save enabled
    3. 取消勾选 -> Save disabled
    """
    logger = TestLogger("test_p1_save_button_state")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择自定义角色"):
        role_name = _find_custom_role(page_obj, auth_page)
        if not role_name:
            pytest.skip("无可用自定义角色")
        page_obj.select_role(role_name)

    with allure.step("验证初始 Save disabled"):
        assert not page_obj.is_save_button_enabled(), "Save 初始应 disabled"
        step_shot(page_obj, "step_save_disabled")

    with allure.step("勾选 Permission:Sessions"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(300)

    with allure.step("验证 Save 变为 enabled"):
        assert page_obj.is_save_button_enabled(), "有修改后 Save 应 enabled"
        step_shot(page_obj, "step_save_enabled")

    with allure.step("取消勾选恢复"):
        page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
        auth_page.wait_for_timeout(500)

    with allure.step("验证 Save 恢复为 disabled"):
        save_after = page_obj.is_save_button_enabled()
        allure.attach(f"恢复后 Save enabled: {save_after}", "save_restored",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_save_restored")

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Save + Restore（实际保存并恢复，验证持久化）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions")
@allure.title("test_p1_role_permission_save_and_restore - 保存权限并恢复")
def test_p1_role_permission_save_and_restore(auth_page: Page):
    """
    验证（使用自定义角色，保存后恢复原状）：
    1. 选择自定义角色（如 "1"），记录初始状态
    2. 勾选 "Permission:Sessions" -> Save
    3. 验证 API 返回成功
    4. 刷新页面，验证持久化
    5. 取消勾选 "Permission:Sessions" -> Save 恢复
    """
    logger = TestLogger("test_p1_role_permission_save_and_restore")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    permission_was_toggled = False
    role_name = None

    try:
        with allure.step("导航到 Permissions 页面"):
            navigate_and_wait(page_obj, auth_page)

        with allure.step("选择自定义角色"):
            role_name = _find_custom_role(page_obj, auth_page)
            if not role_name:
                pytest.skip("无可用自定义角色")
            page_obj.select_role(role_name)

        with allure.step("记录初始 Permission:Sessions 状态"):
            initial_checked = page_obj.is_permission_checked(SAFE_TOGGLE_PERMISSION)
            initial_granted = page_obj.get_granted_number()
            allure.attach(
                f"初始 {SAFE_TOGGLE_PERMISSION}: {'checked' if initial_checked else 'unchecked'}\n"
                f"初始 granted: {initial_granted}",
                "initial_state", allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_initial")

        with allure.step("勾选 Permission:Sessions"):
            page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
            auth_page.wait_for_timeout(500)
            # 验证 toggle 生效
            new_checked = page_obj.is_permission_checked(SAFE_TOGGLE_PERMISSION)
            assert new_checked != initial_checked, \
                f"toggle 未生效: 仍为 {'checked' if new_checked else 'unchecked'}"

        with allure.step("点击 Save 保存"):
            with auth_page.expect_response(
                lambda r: "/api/permission-management/permissions" in r.url
                and r.request.method == "PUT",
                timeout=15000,
            ) as resp_info:
                page_obj.click_save()

            resp = resp_info.value
            assert resp.status in [200, 204], f"Save API 失败: {resp.status}"
            permission_was_toggled = True
            allure.attach(f"Save API status: {resp.status}", "save_api",
                          allure.attachment_type.TEXT)

        with allure.step("等待 Save 完成"):
            # 等待 Save 按钮恢复 disabled（表示无未保存修改）
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_saved")

        with allure.step("刷新页面验证持久化"):
            auth_page.reload()
            page_obj.wait_for_permissions_loaded(timeout=20000)
            page_obj.select_role(role_name)

            persisted_checked = page_obj.is_permission_checked(SAFE_TOGGLE_PERMISSION)
            persisted_granted = page_obj.get_granted_number()
            allure.attach(
                f"持久化后 {SAFE_TOGGLE_PERMISSION}: {'checked' if persisted_checked else 'unchecked'}\n"
                f"持久化后 granted: {persisted_granted}",
                "persisted_state", allure.attachment_type.TEXT,
            )
            assert persisted_checked != initial_checked, \
                "刷新后权限应该已持久化"
            step_shot(page_obj, "step_persisted")

        with allure.step("恢复：取消勾选并保存"):
            page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
            auth_page.wait_for_timeout(500)

            with auth_page.expect_response(
                lambda r: "/api/permission-management/permissions" in r.url
                and r.request.method == "PUT",
                timeout=15000,
            ) as resp_restore:
                page_obj.click_save()

            resp_r = resp_restore.value
            assert resp_r.status in [200, 204], f"Restore Save 失败: {resp_r.status}"
            permission_was_toggled = False
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_restored")

        logger.end(success=True)

    finally:
        # 安全网：如果 toggle 了但未成功 restore，再尝试一次
        if permission_was_toggled and role_name:
            try:
                logger.warning("finally: 尝试恢复权限")
                auth_page.reload()
                page_obj.wait_for_permissions_loaded(timeout=20000)
                page_obj.select_role(role_name)
                auth_page.wait_for_timeout(1000)
                current = page_obj.is_permission_checked(SAFE_TOGGLE_PERMISSION)
                if current != initial_checked:
                    page_obj.toggle_permission_by_label(SAFE_TOGGLE_PERMISSION)
                    auth_page.wait_for_timeout(500)
                    page_obj.click_save()
                    auth_page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"finally restore 失败: {e}")
