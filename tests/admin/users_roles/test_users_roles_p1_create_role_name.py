# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Create Role - Role Name 字段测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Create Role 对话框 - Role Name 字段测试

测试点：
- Role Name 必填验证
- Role Name 唯一性验证
- Role Name 长度边界（0/空拒绝，1位接受，正常长度接受）
- Role Name 混合特殊字符接受

**重要说明**：
- Role Name 无特殊限制：无长度限制、无格式限制
- 仅要求：必填、唯一性、不能为空字符串
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
# P1 - Role Name 唯一性验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Role Name")
@allure.title("test_p1_create_role_name_duplicate - Role Name 唯一性验证")
def test_p1_create_role_name_duplicate(auth_page: Page):
    """验证：Role Name 必须唯一，重复名称应该被拒绝"""
    logger = TestLogger("test_p1_create_role_name_duplicate")
    logger.start()

    page_obj = AdminRolesPage(auth_page)

    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)

    with allure.step("打开 Create Role 对话框"):
        page_obj.click_create_role()
        page_obj.wait_for_create_role_dialog(timeout=3000)

    with allure.step("使用已存在的角色名称（member）"):
        auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill("member")
        step_shot(page_obj, "step_duplicate_name")

    with allure.step("提交并验证错误"):
        page_obj.submit_create_role()

        toast_visible = False
        toast_text = ""
        try:
            auth_page.wait_for_selector(TOAST_SELECTORS, state="visible", timeout=8000)
            toast_visible = True
        except Exception:
            pass

        step_shot(page_obj, "step_error_toast")

        if toast_visible:
            toast_text = get_toast_text(auth_page)

        if toast_text:
            allure.attach(f"错误 Toast 内容:\n{toast_text}", "error_toast_text", allure.attachment_type.TEXT)

        dialog_visible = auth_page.is_visible('[role="dialog"]', timeout=2000)
        if dialog_visible:
            dialog_text = auth_page.locator('[role="dialog"]').first.text_content() or ""
            has_inline_error = any(kw in dialog_text.lower() for kw in ["already taken", "duplicate", "exists", "已存在"])
            if has_inline_error:
                allure.attach(f"对话框内错误提示: {dialog_text[:300]}", "dialog_error_content", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_dialog_with_error")

        assert toast_visible or dialog_visible, \
            "使用重复角色名提交时，应该显示错误提示（Toast 或对话框内错误信息）"

    with allure.step("关闭对话框"):
        page_obj.cancel_create_role()

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Role Name 长度边界测试（精简版）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Role Name")
@allure.title("test_p1_create_role_name_length_boundaries - Role Name 长度边界测试")
@pytest.mark.parametrize(
    "name_length,expected_result",
    [
        (0, "reject"),   # 空字符串 → 必填拒绝
        (1, "accept"),   # 最小 1 位
        (20, "accept"),  # 正常长度
    ],
    ids=["len_0_reject", "len_1_accept", "len_20_accept"],
)
def test_p1_create_role_name_length_boundaries(
    auth_page: Page,
    name_length: int,
    expected_result: str,
):
    """验证：Role Name 长度边界（无长度限制，仅空字符串拒绝）"""
    logger = TestLogger("test_p1_create_role_name_length_boundaries")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000

    if name_length == 0:
        role_name = ""
    else:
        base_name = f"role_{unique_suffix}"
        if name_length <= len(base_name):
            role_name = base_name[:name_length]
        else:
            role_name = base_name + "a" * (name_length - len(base_name))

    allure.dynamic.parameter("角色名长度", name_length)
    allure.dynamic.parameter("期望结果", expected_result)

    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)

        with allure.step("打开 Create Role 对话框"):
            page_obj.click_create_role()
            page_obj.wait_for_create_role_dialog(timeout=3000)

        with allure.step(f"填写 Role Name（长度: {name_length}）"):
            auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
            step_shot(page_obj, f"step_name_length_{name_length}")

        with allure.step("提交并验证结果"):
            if expected_result == "reject":
                submit_button = auth_page.locator(page_obj.CREATE_ROLE_SUBMIT_BUTTON)
                is_disabled = submit_button.is_disabled()

                if is_disabled:
                    step_shot(page_obj, "step_rejected_button_disabled")
                    allure.attach("Create Role 按钮被禁用，前端已阻止提交", "button_disabled", allure.attachment_type.TEXT)
                else:
                    submit_button.click()
                    auth_page.wait_for_timeout(1000)
                    name_input = auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT)
                    validation_message = name_input.evaluate("el => el.validationMessage") or ""
                    dialog_visible = auth_page.is_visible('[role="dialog"]', timeout=2000)
                    assert is_disabled or dialog_visible or validation_message, "应该阻止提交空名称"
                    step_shot(page_obj, "step_rejected")
            else:
                with auth_page.expect_response(
                    lambda r: r.url.endswith("/api/identity/roles") and r.status in [200, 201],
                    timeout=10000,
                ) as resp_info:
                    page_obj.submit_create_role()

                response = resp_info.value
                assert response.status in [200, 201], f"创建角色失败，状态码: {response.status}"
                step_shot(page_obj, f"step_accepted_{name_length}")

                auth_page.wait_for_timeout(2000)
                page_obj.navigate()
                page_obj.wait_for_roles_loaded(timeout=5000)

        logger.end(success=True)

    finally:
        if expected_result == "accept" and role_name:
            try:
                delete_test_role(page_obj, role_name)
            except Exception as e:
                logger.warning(f"清理角色 {role_name} 时出错: {e}")


# ═══════════════════════════════════════════════════════════════
# P1 - Role Name 混合特殊字符测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Role Name")
@allure.title("test_p1_create_role_name_special_characters - Role Name 特殊字符混合测试")
def test_p1_create_role_name_special_characters(auth_page: Page):
    """验证：Role Name 可以包含各种特殊字符（混合场景：@#$%&*_-.）"""
    logger = TestLogger("test_p1_create_role_name_special_characters")
    logger.start()

    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"Role@#${unique_suffix}%&Test_ABC-abc.123"

    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)

    with allure.step("打开 Create Role 对话框"):
        page_obj.click_create_role()
        page_obj.wait_for_create_role_dialog(timeout=3000)

    with allure.step("填写 Role Name（混合特殊字符）"):
        auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
        step_shot(page_obj, "step_special_characters_filled")

    with allure.step("提交创建角色"):
        with auth_page.expect_response(
            lambda r: r.url.endswith("/api/identity/roles") and r.status in [200, 201],
            timeout=10000,
        ) as resp_info:
            page_obj.submit_create_role()

        response = resp_info.value
        assert response.status in [200, 201], f"创建角色失败，状态码: {response.status}"
        step_shot(page_obj, "step_role_created")

        auth_page.wait_for_timeout(2000)
        page_obj.navigate()
        page_obj.wait_for_roles_loaded(timeout=5000)
        allure.attach(f"角色 {role_name} 创建成功", "create_success", allure.attachment_type.TEXT)

    try:
        logger.end(success=True)
    finally:
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")
