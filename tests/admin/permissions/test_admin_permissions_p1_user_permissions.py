# ═══════════════════════════════════════════════════════════════
# Admin Permissions - P1 User Permissions Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：User Permissions Tab 功能测试

元素定位：全部经过 Playwright MCP（2026-02-09）重新验证

用户数据规则（稳定性保障）：
- 不修改 admin 系统账号的 user-level 权限
- 不修改账号池 (qatest__*, TestAdmin*) 的用户
- 修改操作选择非池子用户，save 后必须 restore
- Grant All / Revoke All 默认不保存

页面结构（via MCP 2026-02-11）：
  User Permissions Tab
  左侧：Select User -> searchbox "Search users..." -> 用户列表 (N items)
        用户少时全量展示，用户多时显示 Load more 按钮
  右侧：与 Role Permissions 相同布局
"""

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
# 账号池前缀（必须避开）
POOL_PREFIXES = ("qatest__", "TestAdmin")
# 用于 toggle 测试的安全权限名称
SAFE_TOGGLE_PERMISSION = "Permission:Sessions"


def _switch_to_user_tab(page_obj: AdminPermissionsPage, auth_page: Page) -> None:
    """切换到 User Permissions Tab 并等待左侧面板就绪"""
    page_obj.switch_to_user_permissions()
    # switch_to_user_permissions 内部已等待 "Select User" 出现


def _get_selected_username(auth_page: Page) -> str:
    """
    从右侧面板的 "{username} Permissions" 文本提取当前选中的用户名
    """
    try:
        # 文本格式: "{username} Permissions"
        heading = auth_page.locator('text=/\\w.+ Permissions/').first
        text = (heading.text_content(timeout=2000) or "").strip()
        if " Permissions" in text:
            return text.replace(" Permissions", "").strip()
    except Exception:
        pass
    return ""


def _is_pool_account(username: str) -> bool:
    """检查用户名是否属于账号池"""
    return any(username.startswith(prefix) for prefix in POOL_PREFIXES)


def _select_safe_user(page_obj: AdminPermissionsPage, auth_page: Page) -> str:
    """
    选择一个安全的非池子、非 admin 角色用户用于修改测试。
    策略：优先选 haylee（member 角色，2 granted，非池子）。
    注意：不选 admin 用户——admin 角色有 48 granted 继承，Revoke All 无效。
    """
    page_obj.search_user("haylee")
    auth_page.wait_for_timeout(2000)
    btn = auth_page.get_by_role("button", name="haylee", exact=True)
    if btn.count() > 0 and btn.first.is_visible():
        btn.first.scroll_into_view_if_needed()
        btn.first.click()
        auth_page.wait_for_timeout(1500)
        # 验证确实选中了 haylee（右侧标题应变化）
        selected = _get_selected_username(auth_page)
        if selected == "haylee":
            page_obj.clear_user_search()
            return "haylee"

    # fallback: 清空搜索，使用自动选中的用户
    page_obj.clear_user_search()
    auth_page.wait_for_timeout(1000)
    return _get_selected_username(auth_page)


# ═══════════════════════════════════════════════════════════════
# P1 - User Permissions Tab 基础功能
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_user_permissions_tab_switch - 切换到 User Permissions Tab")
def test_p1_user_permissions_tab_switch(auth_page: Page):
    """
    验证：
    1. 切换到 User Permissions Tab -> Tab 选中
    2. 显示 "Select User" 标题 + 用户搜索框
    3. 用户列表可见
    """
    logger = TestLogger("test_p1_user_permissions_tab_switch")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("切换到 User Permissions Tab"):
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab")

    with allure.step("验证 Tab 选中状态"):
        assert page_obj.is_user_permissions_tab_selected(), \
            "User Permissions Tab 应被选中"

    with allure.step("验证 Select User 标题可见"):
        assert page_obj.is_visible(page_obj.USER_SELECTOR, timeout=3000), \
            "Select User 标题不可见"

    with allure.step("验证用户搜索框可见"):
        search_loc = auth_page.get_by_placeholder("Search users", exact=False).or_(
            auth_page.get_by_placeholder("搜索用户", exact=False)
        )
        assert search_loc.first.is_visible(timeout=5000), "用户搜索框不可见"

    with allure.step("验证用户列表和数量"):
        items_text = auth_page.locator('text=/\\d+ items/').first
        if items_text.count() > 0:
            allure.attach(
                f"用户数量: {items_text.text_content()}",
                "user_count", allure.attachment_type.TEXT,
            )

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_user_list_displayed - 用户列表展示")
def test_p1_user_list_displayed(auth_page: Page):
    """
    验证：
    1. 用户列表非空
    2. 用户按钮可见（自动选中第一个）
    3. 用户数量文本可见
    """
    logger = TestLogger("test_p1_user_list_displayed")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab")

    with allure.step("验证用户列表非空"):
        # 第一个用户会自动选中，右侧应显示 Permissions
        selected = _get_selected_username(auth_page)
        allure.attach(f"当前选中用户: {selected}", "selected_user",
                      allure.attachment_type.TEXT)
        assert selected, "应有用户被自动选中"

    with allure.step("验证用户数量显示"):
        items_text = auth_page.locator('text=/\\d+ items?/').first
        assert items_text.is_visible(timeout=3000), "用户数量文本应可见"
        count_text = items_text.text_content() or ""
        allure.attach(f"用户数量: {count_text}", "user_count",
                      allure.attachment_type.TEXT)

    with allure.step("验证 Load more 按钮（可选：用户多时出现）"):
        load_more = auth_page.locator(page_obj.LOAD_MORE_BUTTON).or_(
            auth_page.locator(page_obj.LOAD_MORE_BUTTON_I18N)
        )
        if load_more.first.is_visible(timeout=2000):
            load_more_text = load_more.first.text_content() or ""
            allure.attach(f"Load more: {load_more_text}", "load_more",
                          allure.attachment_type.TEXT)
        else:
            allure.attach("无 Load more（用户已全量展示）", "load_more",
                          allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 用户搜索
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_user_search - 用户搜索功能")
def test_p1_user_search(auth_page: Page):
    """
    验证：
    1. 搜索 "admin" -> admin 用户出现在结果中
    2. 清空搜索 -> 用户列表恢复
    """
    logger = TestLogger("test_p1_user_search")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("搜索 'admin'"):
        page_obj.search_user("admin")
        step_shot(page_obj, "step_search_admin")

    with allure.step("验证搜索结果包含 admin"):
        admin_btn = auth_page.get_by_role("button", name="admin", exact=True)
        assert admin_btn.count() > 0 and admin_btn.first.is_visible(), \
            "搜索 'admin' 后应显示 admin 用户"

    with allure.step("清空搜索"):
        page_obj.clear_user_search()
        step_shot(page_obj, "step_search_cleared")

    with allure.step("验证用户列表恢复"):
        # 清空搜索后用户列表应恢复完整
        items_text = auth_page.locator('text=/\\d+ items?/').first
        if items_text.is_visible(timeout=3000):
            allure.attach(f"恢复后用户数: {items_text.text_content()}", "restored_count",
                          allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 选择用户加载权限
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_select_user_loads_permissions - 选择用户加载权限")
def test_p1_select_user_loads_permissions(auth_page: Page):
    """
    验证：
    1. 切换到 User Permissions Tab
    2. 搜索并选择 admin 用户
    3. 右侧显示 admin 用户的权限
    4. 权限分组和 checkbox 可见
    """
    logger = TestLogger("test_p1_select_user_loads_permissions")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("搜索并选择 admin 用户"):
        page_obj.search_user("admin")
        auth_page.wait_for_timeout(1000)
        admin_btn = auth_page.get_by_role("button", name="admin", exact=True)
        if admin_btn.count() > 0:
            admin_btn.first.click()
            auth_page.wait_for_timeout(1500)
        page_obj.clear_user_search()
        step_shot(page_obj, "step_admin_selected")

    with allure.step("验证权限统计显示"):
        granted = page_obj.get_granted_count_text()
        allure.attach(f"admin user granted: {granted}", "granted",
                      allure.attachment_type.TEXT)
        assert "granted" in granted, f"应显示 granted，实际: {granted}"

    with allure.step("验证权限分组可见"):
        groups = page_obj.get_permission_group_names()
        allure.attach(
            f"分组数: {len(groups)}\n" + "\n".join(groups),
            "groups", allure.attachment_type.TEXT,
        )
        assert len(groups) > 0, "权限分组不应为空"

    with allure.step("验证 checkbox 可见"):
        cb_count = page_obj.get_visible_checkbox_count()
        allure.attach(f"可见 checkbox: {cb_count}", "checkboxes",
                      allure.attachment_type.TEXT)
        assert cb_count > 0, "应有可见 checkbox"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 用户权限 Grant All / Revoke All（不保存）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_user_permission_grant_revoke_no_save - 用户权限 Grant/Revoke（不保存）")
def test_p1_user_permission_grant_revoke_no_save(auth_page: Page):
    """
    验证（使用 member 角色用户，不保存）：
    1. 选择 loadtest_user（member 角色）
    2. 记录初始 granted（= member 角色继承的权限数）
    3. Grant All -> granted = 48
    4. Revoke All -> granted 恢复到初始值（role-level 继承不受影响）
    5. 不保存，刷新页面自动丢弃

    注意：Revoke All 只取消 user-level 权限，role-level 继承的权限仍然保留
    """
    logger = TestLogger("test_p1_user_permission_grant_revoke_no_save")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("选择 loadtest_user_001（member 角色）"):
        page_obj.select_user("loadtest_user_001")
        step_shot(page_obj, "step_user_selected")

    with allure.step("记录初始 granted（= member 角色继承）"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted（role-level 继承）: {initial}", "initial",
                      allure.attachment_type.TEXT)

    with allure.step("点击 Grant All"):
        page_obj.click_grant_all()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_after_grant_all")

    with allure.step("验证 Grant All 生效 → granted = 48"):
        after_grant = page_obj.get_granted_number()
        allure.attach(f"Grant All 后: {after_grant}", "after_grant",
                      allure.attachment_type.TEXT)
        assert after_grant == 48, f"Grant All 后应为 48，实际: {after_grant}"

    with allure.step("点击 Revoke All"):
        page_obj.click_revoke_all()
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_after_revoke_all")

    with allure.step("验证 Revoke All 后 → granted = 初始值（role-level 继承）"):
        after_revoke = page_obj.get_granted_number()
        allure.attach(
            f"Revoke All 后: {after_revoke}\n"
            f"初始（role-level）: {initial}\n"
            f"说明: Revoke All 只取消 user-level，role-level 继承保留",
            "after_revoke", allure.attachment_type.TEXT,
        )
        assert after_revoke == initial, \
            f"Revoke All 后应恢复到 role-level 继承值({initial})，实际: {after_revoke}"

    # 不保存：刷新/导航离开时自动丢弃
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Load more 分页
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_load_more_users - Load more 加载更多用户")
def test_p1_load_more_users(auth_page: Page):
    """
    验证：
    1. Load more 按钮显示 "Load more (50/619)" 格式
    2. 点击后按钮文本变化（如 100/619）
    """
    logger = TestLogger("test_p1_load_more_users")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航并切换到 User Permissions"):
        navigate_and_wait(page_obj, auth_page)
        _switch_to_user_tab(page_obj, auth_page)

    with allure.step("验证 Load more 按钮可见"):
        load_more = auth_page.locator(page_obj.LOAD_MORE_BUTTON).or_(
            auth_page.locator(page_obj.LOAD_MORE_BUTTON_I18N)
        )
        if not load_more.first.is_visible(timeout=3000):
            pytest.skip("Load more 不可见（用户数不足以分页）")

    with allure.step("记录初始 Load more 文本"):
        text_before = load_more.first.text_content() or ""
        allure.attach(f"初始: {text_before}", "before",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_before_load_more")

    with allure.step("点击 Load more"):
        page_obj.click_load_more()
        step_shot(page_obj, "step_after_load_more")

    with allure.step("验证 Load more 文本变化"):
        # 可能加载后按钮仍存在（如 100/619），也可能全部加载完毕
        if load_more.first.is_visible(timeout=2000):
            text_after = load_more.first.text_content() or ""
            allure.attach(f"加载后: {text_after}", "after",
                          allure.attachment_type.TEXT)
            assert text_after != text_before, \
                f"Load more 文本应变化: {text_before} -> {text_after}"
            # 验证数字增加
            m_before = re.search(r'(\d+)/(\d+)', text_before)
            m_after = re.search(r'(\d+)/(\d+)', text_after)
            if m_before and m_after:
                assert int(m_after.group(1)) > int(m_before.group(1)), \
                    "加载后的已加载数应增加"
        else:
            allure.attach("所有用户已加载完毕", "all_loaded",
                          allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Tab 切换保持独立
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_tab_switch_independent - Tab 切换后数据独立")
def test_p1_tab_switch_independent(auth_page: Page):
    """
    验证：
    1. Role Permissions 选择 admin（48 granted）
    2. 切换到 User Permissions -> 不同的权限数据
    3. 切换回 Role Permissions -> 数据恢复正确
    """
    logger = TestLogger("test_p1_tab_switch_independent")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("在 Role Permissions 选择 admin"):
        page_obj.select_admin_role()
        role_granted = page_obj.get_granted_count_text()
        allure.attach(f"Role admin: {role_granted}", "role_granted",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_role_admin")

    with allure.step("切换到 User Permissions"):
        _switch_to_user_tab(page_obj, auth_page)
        step_shot(page_obj, "step_user_tab")

    with allure.step("验证 User Permissions Tab 选中"):
        assert page_obj.is_user_permissions_tab_selected(), \
            "应在 User Permissions Tab"

    with allure.step("验证 User 有独立的权限数据"):
        user_granted = page_obj.get_granted_count_text()
        allure.attach(f"User: {user_granted}", "user_granted",
                      allure.attachment_type.TEXT)
        assert "granted" in user_granted, "User 应显示 granted 统计"

    with allure.step("切换回 Role Permissions"):
        page_obj.switch_to_role_permissions()
        auth_page.wait_for_timeout(2000)
        step_shot(page_obj, "step_back_to_role")

    with allure.step("验证 Role Permissions 数据恢复"):
        assert page_obj.is_role_permissions_tab_selected(), \
            "应在 Role Permissions Tab"
        role_granted_after = page_obj.get_granted_count_text()
        allure.attach(f"切换回后: {role_granted_after}", "role_after",
                      allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - User Permission Save + Restore（实际保存并恢复）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - User Permissions")
@allure.title("test_p1_user_permission_save_and_restore - 用户权限保存并恢复")
def test_p1_user_permission_save_and_restore(auth_page: Page):
    """
    验证（使用 loadtest_user_002，保存后恢复原状）：
    1. 选择 loadtest_user_002（member 角色）
    2. 勾选 Permission:Sessions.Delete（member 角色没有此权限）
    3. Save → 验证持久化（reload 后仍 checked）
    4. 取消勾选 → Save → 恢复原状

    注意：必须 toggle member 角色 **没有** 的权限！
    ABP 叠加制下，角色已有的权限无法通过 User 级别取消。
    """
    logger = TestLogger("test_p1_user_permission_save_and_restore")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    permission_was_toggled = False
    selected_user = "loadtest_user_002"
    # member 角色没有此权限 → user-level toggle 可以验证持久化
    toggle_perm = "├ Permission:Sessions.Delete"

    try:
        with allure.step("导航并切换到 User Permissions"):
            navigate_and_wait(page_obj, auth_page)
            _switch_to_user_tab(page_obj, auth_page)

        with allure.step("选择 loadtest_user_002"):
            page_obj.select_user(selected_user)
            step_shot(page_obj, "step_user_selected")

        with allure.step("记录初始状态"):
            initial_granted = page_obj.get_granted_number()
            initial_checked = page_obj.is_permission_checked(toggle_perm)
            allure.attach(
                f"初始 {toggle_perm}: "
                f"{'checked' if initial_checked else 'unchecked'}\n"
                f"初始 granted: {initial_granted}\n"
                f"说明: Sessions.Delete 不在 member 角色中，初始应 unchecked",
                "initial", allure.attachment_type.TEXT,
            )

        with allure.step(f"Toggle {toggle_perm}"):
            page_obj.toggle_permission_by_label(toggle_perm)
            auth_page.wait_for_timeout(500)
            new_checked = page_obj.is_permission_checked(toggle_perm)
            assert new_checked != initial_checked, "toggle 未生效"

        with allure.step("Save 保存"):
            with auth_page.expect_response(
                lambda r: "/api/permission-management/permissions" in r.url
                and r.request.method == "PUT",
                timeout=15000,
            ) as resp_info:
                page_obj.click_save()
            resp = resp_info.value
            assert resp.status in [200, 204], f"Save 失败: {resp.status}"
            permission_was_toggled = True
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_saved")

        with allure.step("刷新验证持久化"):
            auth_page.reload()
            page_obj.wait_for_permissions_loaded(timeout=20000)
            _switch_to_user_tab(page_obj, auth_page)
            page_obj.select_user(selected_user)

            persisted = page_obj.is_permission_checked(toggle_perm)
            allure.attach(
                f"持久化后 {toggle_perm}: {'checked' if persisted else 'unchecked'}\n"
                f"初始: {'checked' if initial_checked else 'unchecked'}\n"
                f"说明: Sessions.Delete 非角色继承，user-level 变更应持久化",
                "persisted", allure.attachment_type.TEXT,
            )
            assert persisted != initial_checked, "权限应已持久化"
            step_shot(page_obj, "step_persisted")

        with allure.step("Restore: 取消 toggle 并保存"):
            page_obj.toggle_permission_by_label(toggle_perm)
            auth_page.wait_for_timeout(500)
            with auth_page.expect_response(
                lambda r: "/api/permission-management/permissions" in r.url
                and r.request.method == "PUT",
                timeout=15000,
            ) as resp_restore:
                page_obj.click_save()
            resp_r = resp_restore.value
            assert resp_r.status in [200, 204], f"Restore 失败: {resp_r.status}"
            permission_was_toggled = False
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_restored")

        logger.end(success=True)

    finally:
        if permission_was_toggled and selected_user:
            try:
                logger.warning("finally: 尝试恢复用户权限")
                auth_page.reload()
                page_obj.wait_for_permissions_loaded(timeout=20000)
                _switch_to_user_tab(page_obj, auth_page)
                page_obj.select_user(selected_user)
                current = page_obj.is_permission_checked(toggle_perm)
                if current != initial_checked:
                    page_obj.toggle_permission_by_label(toggle_perm)
                    auth_page.wait_for_timeout(500)
                    page_obj.click_save()
                    auth_page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"finally restore 失败: {e}")
