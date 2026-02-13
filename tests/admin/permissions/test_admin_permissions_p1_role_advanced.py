# ═══════════════════════════════════════════════════════════════
# Admin Permissions - P1 Role Permissions 补充测试
# ═══════════════════════════════════════════════════════════════
"""
补充场景（Review 发现的 Gap）：
1. 父子权限级联：勾选父 → 子全选，取消父 → 子全取消
2. Grant All + Save 持久化：Grant All → Save → 刷新验证 → Restore
3. 角色切换 granted 差异：admin(48) > member(N)
4. 权限总数验证：所有分组之和 = 48
"""

from __future__ import annotations

import re
import allure
import pytest
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import (
    step_shot, navigate_and_wait, TOAST_SELECTORS, get_toast_text,
)
from utils.logger import TestLogger

# ── 常量 ──────────────────────────────────────────────────────
CUSTOM_ROLE = "test"
TOTAL_PERMISSIONS = 48
SAFE_TOGGLE = "Permission:Sessions"
# 父子级联测试用的分组和父权限
CASCADE_PARENT = "角色管理"
CASCADE_CHILDREN = ["创建", "编辑", "删除", "更改权限"]


def _find_custom_role(page_obj: AdminPermissionsPage, auth_page: Page) -> str | None:
    for name in [CUSTOM_ROLE, "1", "custom"]:
        btn = auth_page.get_by_role("button", name=name, exact=True)
        if btn.count() > 0 and btn.is_visible():
            return name
    return None


# ═══════════════════════════════════════════════════════════════
# P1 - 父子权限级联
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions 补充")
@allure.title("test_p1_parent_child_cascade - 父子权限级联行为")
def test_p1_parent_child_cascade(auth_page: Page):
    """
    产品行为（单向级联）：
    - 勾选父权限 → 子权限 **不会** 自动勾选（仅勾父自身）
    - 取消父权限 → 子权限 **会** 全部取消

    验证（使用自定义角色，不保存）：
    1. 先手动勾选父「角色管理」+ 所有子权限
    2. 取消父「角色管理」→ 子权限全部自动取消
    3. 重新勾选父「角色管理」→ granted 仅 +1（子不跟随）
    """
    logger = TestLogger("test_p1_parent_child_cascade")
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

    with allure.step("确保角色管理初始未勾选"):
        if page_obj.is_permission_checked(CASCADE_PARENT):
            page_obj.toggle_permission_by_label(CASCADE_PARENT)
            auth_page.wait_for_timeout(500)

    with allure.step("手动勾选父权限 + 所有子权限"):
        # 勾选父
        page_obj.toggle_permission_by_label(CASCADE_PARENT)
        auth_page.wait_for_timeout(300)
        # 逐个勾选子
        for i, child in enumerate(CASCADE_CHILDREN):
            prefix = "└" if i == len(CASCADE_CHILDREN) - 1 else "├"
            page_obj.toggle_permission_by_label(f"{prefix} {child}")
            auth_page.wait_for_timeout(200)

        after_all = page_obj.get_granted_number()
        allure.attach(f"父+子全部勾选后 granted: {after_all}", "after_all",
                      allure.attachment_type.TEXT)
        assert after_all >= 5, f"父+4子应 >= 5 granted，实际: {after_all}"
        step_shot(page_obj, "step_all_checked")

    with allure.step("取消父权限「角色管理」→ 验证子权限全部自动取消"):
        page_obj.toggle_permission_by_label(CASCADE_PARENT)
        auth_page.wait_for_timeout(500)
        after_uncheck_parent = page_obj.get_granted_number()
        allure.attach(f"取消父后 granted: {after_uncheck_parent}", "after_uncheck",
                      allure.attachment_type.TEXT)
        # 取消父应该级联取消所有子：granted 应减少 >= 5
        assert after_uncheck_parent < after_all, \
            f"取消父后 granted 应减少: {after_all} -> {after_uncheck_parent}"
        # 验证子权限确实被取消
        for i, child in enumerate(CASCADE_CHILDREN):
            prefix = "└" if i == len(CASCADE_CHILDREN) - 1 else "├"
            label = f"{prefix} {child}"
            cb = auth_page.get_by_role("checkbox", name=label, exact=True)
            if cb.count() > 0:
                assert not cb.first.is_checked(), f"子权限 {child} 应被级联取消"
        step_shot(page_obj, "step_parent_unchecked_cascade")

    with allure.step("重新勾选父权限 → 验证子权限不跟随"):
        before_recheck = page_obj.get_granted_number()
        page_obj.toggle_permission_by_label(CASCADE_PARENT)
        auth_page.wait_for_timeout(500)
        after_recheck = page_obj.get_granted_number()
        allure.attach(
            f"重新勾选父前: {before_recheck}, 后: {after_recheck}",
            "recheck", allure.attachment_type.TEXT,
        )
        # 仅父自身 +1，子不跟随
        assert after_recheck == before_recheck + 1, \
            f"勾选父应仅 +1（子不级联），实际: {before_recheck} -> {after_recheck}"
        step_shot(page_obj, "step_parent_rechecked_no_cascade")

    # 不保存
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 角色切换 granted 差异
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions 补充")
@allure.title("test_p1_role_granted_difference - 角色切换 granted 数值差异")
def test_p1_role_granted_difference(auth_page: Page):
    """
    验证：
    1. admin 角色 granted = 48（全授权）
    2. member 角色 granted < 48
    3. 两者 granted 数值不同
    """
    logger = TestLogger("test_p1_role_granted_difference")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded")

    with allure.step("选择 admin 角色"):
        page_obj.select_admin_role()
        admin_granted = page_obj.get_granted_number()
        allure.attach(f"admin granted: {admin_granted}", "admin", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_admin_selected")

    with allure.step("选择 member 角色"):
        page_obj.select_member_role()
        member_granted = page_obj.get_granted_number()
        allure.attach(f"member granted: {member_granted}", "member", allure.attachment_type.TEXT)
        step_shot(page_obj, "step_member_selected")

    with allure.step("验证 admin > member"):
        assert admin_granted > member_granted, \
            f"admin({admin_granted}) 应 > member({member_granted})"

    with allure.step("验证 admin = 48（全授权）"):
        assert admin_granted == TOTAL_PERMISSIONS, \
            f"admin 应全授权({TOTAL_PERMISSIONS})，实际: {admin_granted}"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 权限总数验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P1 - Role Permissions 补充")
@allure.title("test_p1_permission_total_count - 权限总数 = 分组之和")
def test_p1_permission_total_count(auth_page: Page):
    """
    验证：
    1. 选择 admin（48/48 全授权便于验证）
    2. 页面显示 "48 permissions"
    3. 所有分组 x/y 中 y 之和 = 48
    """
    logger = TestLogger("test_p1_permission_total_count")
    logger.start()

    page_obj = AdminPermissionsPage(auth_page)

    with allure.step("导航到 Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)

    with allure.step("选择 admin 角色"):
        page_obj.select_admin_role()
        step_shot(page_obj, "step_admin_selected")

    with allure.step("获取页面显示的 permissions 总数"):
        total_displayed = page_obj.get_permissions_count()
        allure.attach(f"页面显示: {total_displayed} permissions",
                      "displayed", allure.attachment_type.TEXT)

    with allure.step("计算所有分组权限数之和"):
        groups = page_obj.get_permission_group_names()
        group_sum = 0
        details = []
        for name in groups:
            m = re.search(r'(\d+)/(\d+)', name)
            if m:
                total = int(m.group(2))
                group_sum += total
                details.append(f"  {name} → total={total}")

        allure.attach(
            f"分组之和: {group_sum}\n" + "\n".join(details),
            "group_sum", allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_permission_groups", full_page=True)

    with allure.step("验证总数一致"):
        assert total_displayed == group_sum, \
            f"页面显示({total_displayed}) != 分组之和({group_sum})"
        assert total_displayed == TOTAL_PERMISSIONS, \
            f"权限总数应为 {TOTAL_PERMISSIONS}，实际: {total_displayed}"

    logger.end(success=True)


    # NOTE: Grant All + Save 持久化测试已合并到
    # test_p1_role_permission_save_and_restore（role_permissions 文件）
    # 避免并发 worker 竞争同一 test 角色导致数据污染
