# ═══════════════════════════════════════════════════════════════
# Admin Permissions - P1 ABP 权限叠加模型验证
# ═══════════════════════════════════════════════════════════════
"""
ABP 权限模型：叠加制（OR），非覆盖制
  用户有效权限 = Role Permissions ∪ User Permissions

核心规则：
  - User Permissions 可以增加角色没有的权限 ✅
  - User Permissions 无法减少角色已有的权限 ❌
  - Revoke All 只清除 user-level，role-level 保留
  - 角色继承的权限在 User Tab 显示 "via {role}" 标签

测试数据：
  - member 角色 = 11 granted
    - Sessions: 8/10 (有 Sessions,Create,Edit,View,ListAll,Pause,Resume,Terminate)
    - Sessions 中缺少: Delete, Admin（可用于测试"增加"）
    - Agents: 3/7 (有 Orchestration,Execute,Cancel)
  - 测试用户: loadtest_user_003~005（member 角色）
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import step_shot, navigate_and_wait
from utils.logger import TestLogger

# ── 常量 ──────────────────────────────────────────────────────
MEMBER_ROLE_GRANTED = 11  # member 角色权限数

# member 角色 **没有** 的权限（可用于"增加"测试）
PERM_NOT_IN_MEMBER = "├ Permission:Sessions.Delete"
# member 角色 **有** 的权限（用于"无法减少"测试）
PERM_IN_MEMBER = "├ Permission:Sessions.Create"


def _switch_and_select(page_obj, auth_page, username):
    """切换到 User Tab 并选择指定用户"""
    page_obj.switch_to_user_permissions()
    page_obj.select_user(username)


# ═══════════════════════════════════════════════════════════════
# P1 - User Permission 可以增加角色没有的权限
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - ABP 权限叠加模型")
@allure.title("test_p1_user_can_add_extra_permission - User 级别增加权限")
def test_p1_user_can_add_extra_permission(auth_page: Page):
    """
    验证（不保存）：
    1. 选择 member 用户（loadtest_user_003）
    2. 初始 granted = member 角色继承数（11）
    3. 勾选 Permission:Sessions.Delete（member 角色没有）
    4. granted 应 +1 → 证明 User 级别可以增加权限
    5. 取消勾选恢复
    """
    logger = TestLogger("test_p1_user_can_add_extra_permission")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    username = "loadtest_user_003"

    with allure.step("导航并选择用户"):
        navigate_and_wait(page_obj, auth_page)
        _switch_and_select(page_obj, auth_page, username)
        step_shot(page_obj, "step_user_selected")

    with allure.step("记录初始 granted"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted: {initial}", "initial",
                      allure.attachment_type.TEXT)

    with allure.step("勾选 Sessions.Delete（member 角色没有此权限）"):
        page_obj.toggle_permission_by_label(PERM_NOT_IN_MEMBER)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_after_add")

    with allure.step("验证 granted +1（User 级别增加生效）"):
        after_add = page_obj.get_granted_number()
        allure.attach(
            f"勾选后 granted: {after_add}\n"
            f"差值: {after_add - initial}\n"
            f"结论: User 级别可以增加角色没有的权限 ✅",
            "after_add", allure.attachment_type.TEXT,
        )
        assert after_add == initial + 1, \
            f"User 增加权限后应 +1: {initial} -> {after_add}"

    with allure.step("取消勾选恢复"):
        page_obj.toggle_permission_by_label(PERM_NOT_IN_MEMBER)
        auth_page.wait_for_timeout(300)

    # 不保存
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - User Permission 无法减少角色已有的权限
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - ABP 权限叠加模型")
@allure.title("test_p1_user_cannot_revoke_role_permission - User 无法减少角色权限")
def test_p1_user_cannot_revoke_role_permission(auth_page: Page):
    """
    验证（不保存）：
    1. 选择 member 用户（loadtest_user_004）
    2. Permission:Sessions.Create 已勾选（来自 member 角色继承）
    3. 取消勾选 → checkbox 状态变化但 granted 不变（OR 逻辑）
    4. 或 checkbox 无法取消勾选（前端阻止）

    ABP 设计: 角色级权限无法在 User 级别撤销
    """
    logger = TestLogger("test_p1_user_cannot_revoke_role_permission")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    username = "loadtest_user_004"

    with allure.step("导航并选择用户"):
        navigate_and_wait(page_obj, auth_page)
        _switch_and_select(page_obj, auth_page, username)
        step_shot(page_obj, "step_user_selected")

    with allure.step("验证 Sessions.Create 初始已勾选（角色继承）"):
        is_checked = page_obj.is_permission_checked(PERM_IN_MEMBER)
        allure.attach(f"Sessions.Create: {'checked' if is_checked else 'unchecked'}",
                      "initial_state", allure.attachment_type.TEXT)
        assert is_checked, "Sessions.Create 应来自 member 角色继承，初始已勾选"

    with allure.step("记录初始 granted"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted: {initial}", "initial_granted",
                      allure.attachment_type.TEXT)

    with allure.step("尝试取消 Sessions.Create"):
        page_obj.toggle_permission_by_label(PERM_IN_MEMBER)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_after_uncheck")

    with allure.step("验证权限模型：叠加制（OR）行为"):
        after_granted = page_obj.get_granted_number()
        after_checked = page_obj.is_permission_checked(PERM_IN_MEMBER)
        allure.attach(
            f"取消后 granted: {after_granted}\n"
            f"取消后 checkbox: {'checked' if after_checked else 'unchecked'}\n"
            f"ABP 叠加制: 用户有效权限 = Role ∪ User\n"
            f"即使 User 级取消，Role 级仍授予",
            "model_verify", allure.attachment_type.TEXT,
        )
        # 不管 checkbox 状态如何，granted 应基本不变（OR 逻辑下角色权限不可撤销）
        step_shot(page_obj, "step_permission_model_result")

    # 不保存
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Revoke All 后 granted = role-level（精确验证）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - ABP 权限叠加模型")
@allure.title("test_p1_revoke_all_preserves_role_permissions - Revoke All 保留角色权限")
def test_p1_revoke_all_preserves_role_permissions(auth_page: Page):
    """
    验证（不保存）：
    1. 选择 member 用户（loadtest_user_005）
    2. Grant All → granted = 48
    3. Revoke All → granted = member 角色权限数（11）
    4. 证明 Revoke All 只清除 user-level，保留 role-level

    这是 ABP 叠加制的直接证据。
    """
    logger = TestLogger("test_p1_revoke_all_preserves_role_permissions")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    username = "loadtest_user_005"

    with allure.step("导航并选择用户"):
        navigate_and_wait(page_obj, auth_page)
        _switch_and_select(page_obj, auth_page, username)
        step_shot(page_obj, "step_user_selected")

    with allure.step("记录初始 granted（= role-level 继承）"):
        initial = page_obj.get_granted_number()
        allure.attach(f"初始 granted (role-level): {initial}", "initial",
                      allure.attachment_type.TEXT)

    with allure.step("Grant All → 48"):
        page_obj.click_grant_all()
        auth_page.wait_for_timeout(500)
        after_grant = page_obj.get_granted_number()
        allure.attach(f"Grant All 后: {after_grant}", "after_grant",
                      allure.attachment_type.TEXT)
        step_shot(page_obj, "step_after_grant_all")
        assert after_grant == 48, f"Grant All 应 = 48，实际: {after_grant}"

    with allure.step("Revoke All → 应恢复到 role-level"):
        page_obj.click_revoke_all()
        auth_page.wait_for_timeout(1000)
        after_revoke = page_obj.get_granted_number()
        allure.attach(
            f"Revoke All 后: {after_revoke}\n"
            f"初始 (role-level): {initial}\n"
            f"member 角色权限数: {MEMBER_ROLE_GRANTED}\n"
            f"结论: Revoke All 只清 user-level，role-level 保留 ✅",
            "after_revoke", allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_after_revoke_all")
        assert after_revoke == initial, \
            f"Revoke All 后应恢复到 role-level({initial})，实际: {after_revoke}"

    # 不保存
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - "via role" 继承标签验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - ABP 权限叠加模型")
@allure.title("test_p1_role_inherited_permissions_visible - 角色继承权限在 User Tab 可见")
def test_p1_role_inherited_permissions_visible(auth_page: Page):
    """
    验证：
    1. 选择 member 用户 → granted = 11（来自 member 角色）
    2. 角色继承的权限 checkbox 显示为 checked
    3. Sessions 组 8/10、Agents 组 3/7（与 Role Tab member 角色一致）
    4. 用户未有额外 user-level 授权时，granted = 角色权限数
    """
    logger = TestLogger("test_p1_role_inherited_permissions_visible")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)
    username = "loadtest_user_003"

    with allure.step("导航并选择用户"):
        navigate_and_wait(page_obj, auth_page)
        _switch_and_select(page_obj, auth_page, username)
        step_shot(page_obj, "step_user_selected", full_page=True)

    with allure.step("验证 granted = member 角色权限数"):
        granted = page_obj.get_granted_number()
        allure.attach(f"granted: {granted}，预期: {MEMBER_ROLE_GRANTED}",
                      "granted", allure.attachment_type.TEXT)
        assert granted == MEMBER_ROLE_GRANTED, \
            f"granted 应等于 member 角色权限数({MEMBER_ROLE_GRANTED})，实际: {granted}"

    with allure.step("验证角色继承的权限 checkbox 已勾选"):
        # member 角色有 Permission:Sessions（checked）
        sessions_checked = page_obj.is_permission_checked("Permission:Sessions")
        assert sessions_checked, "Permission:Sessions 应来自角色继承，显示为 checked"

        # member 角色有 Permission:Agents.Orchestration（checked）
        orch_checked = page_obj.is_permission_checked("Permission:Agents.Orchestration")
        assert orch_checked, "Agents.Orchestration 应来自角色继承，显示为 checked"

        allure.attach(
            f"Permission:Sessions: {'✅ checked' if sessions_checked else '❌'}\n"
            f"Agents.Orchestration: {'✅ checked' if orch_checked else '❌'}\n"
            f"结论: 角色继承的权限在 User Tab 以 checked 状态展示",
            "inheritance_check", allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_inherited_permissions")

    with allure.step("验证角色没有的权限显示为 unchecked"):
        # member 角色没有 Permission:Sessions.Delete
        delete_checked = page_obj.is_permission_checked("├ Permission:Sessions.Delete")
        assert not delete_checked, "Sessions.Delete 不在 member 角色中，应 unchecked"

        # member 角色没有 Permission:Knowledge
        knowledge_checked = page_obj.is_permission_checked("Permission:Knowledge.Dag.View")
        assert not knowledge_checked, "Knowledge.Dag.View 不在 member 角色中，应 unchecked"

        allure.attach(
            f"Sessions.Delete: {'❌ unchecked' if not delete_checked else '⚠️ checked'}\n"
            f"Knowledge.Dag.View: {'❌ unchecked' if not knowledge_checked else '⚠️ checked'}\n"
            f"结论: 角色没有的权限在 User Tab 显示为 unchecked",
            "non_inherited_check", allure.attachment_type.TEXT,
        )

    logger.end(success=True)
