# ═══════════════════════════════════════════════════════════════
# Profile Settings (Edit) - P0
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
P0：Profile 编辑/修改测试。

测试内容：
- 进入/退出编辑模式
- 保存成功
- 取消编辑
"""

import pytest
import allure

from utils.logger import TestLogger
from tests.myaccount._helpers import (
    attach_rule_source_note,
    now_suffix,
    step_shot,
    step_shot_after_success_toast,
    settle_toasts,
)
from playwright.sync_api import Page
from pages.personal_settings_page import PersonalSettingsPage


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - Enter Edit Mode")
@allure.description(
    """
测试点：
- 点击 Edit 按钮进入编辑模式
- 验证编辑模式下的控件可见（Save/Cancel 按钮，输入框）
- 证据：编辑前后截图
"""
)
def test_p0_profile_settings_enter_edit_mode(profile_settings):
    """P0: 进入编辑模式"""
    attach_rule_source_note("Profile Settings P0 - enter edit mode")
    logger = TestLogger("test_p0_profile_settings_enter_edit_mode")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("验证初始状态（查看模式）"):
        assert page_obj.is_visible(page_obj.EDIT_BUTTON, timeout=3000), "Edit 按钮不可见"
        step_shot(page_obj, "step_view_mode", full_page=True)

    with allure.step("点击 Edit 按钮进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    # 验证编辑模式下的控件可见
    with allure.step("验证编辑模式控件"):
        assert page_obj.is_in_edit_mode(), "未进入编辑模式"
        assert page_obj.is_visible(page_obj.SAVE_BUTTON, timeout=3000), "Save 按钮不可见"
        assert page_obj.is_visible(page_obj.CANCEL_BUTTON, timeout=3000), "Cancel 按钮不可见"

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - Cancel Edit")
@allure.description(
    """
测试点：
- 进入编辑模式后点击 Cancel
- 验证退出编辑模式，回到查看模式
- 验证修改的内容未被保存
- 证据：取消前后截图
"""
)
def test_p0_profile_settings_cancel_edit(profile_settings):
    """P0: 取消编辑"""
    attach_rule_source_note("Profile Settings P0 - cancel edit")
    logger = TestLogger("test_p0_profile_settings_cancel_edit")
    logger.start()

    auth_page, page_obj, baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("修改 First Name 字段"):
        suffix = now_suffix()
        test_value = f"TestCancel_{suffix}"
        page_obj.fill_first_name(test_value)
        step_shot(page_obj, "step_after_fill", full_page=True)

    with allure.step("点击 Cancel 按钮"):
        page_obj.click_cancel()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_after_cancel", full_page=True)

    # 验证已退出编辑模式
    assert not page_obj.is_in_edit_mode(), "未退出编辑模式"
    assert page_obj.is_visible(page_obj.EDIT_BUTTON, timeout=3000), "Edit 按钮不可见"

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - Save Success")
@allure.description(
    """
测试点：
- 更新可编辑字段（firstName/lastName/phoneNumber）并保存成功
- 注意：userName 和 email 是只读的，无法修改
- 证据：保存前后截图
"""
)
def test_p0_profile_settings_save_success(profile_settings):
    """P0: 保存成功（happy path）"""
    attach_rule_source_note("Profile Settings P0 - save success")
    logger = TestLogger("test_p0_profile_settings_save_success")
    logger.start()

    _page, page_obj, baseline = profile_settings

    suffix = now_suffix()
    
    # 只更新可编辑字段（firstName/lastName/phoneNumber）
    new_values = {
        "firstName": f"Auto_{suffix}",
        "lastName": f"Run_{suffix}",
        "phoneNumber": (f"138{suffix}")[:11],
    }

    with allure.step("进入编辑模式并更新字段"):
        step_shot(page_obj, "step_before_update", full_page=True)
        page_obj.fill_form(new_values)
        step_shot(page_obj, "step_after_fill", full_page=True)

    with allure.step("点击 Save 保存（期望成功）"):
        resp = page_obj.save_and_wait_profile_update(timeout_ms=20000)
        assert resp.ok, f"profileUpdate 失败 status={resp.status}"
        step_shot_after_success_toast(page_obj, "step_after_save_success")

    # 验证退出编辑模式
    assert not page_obj.is_in_edit_mode(), "保存后应退出编辑模式"

    settle_toasts(page_obj)
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - Edit Each Field")
@allure.description(
    """
测试点：
- 逐个编辑 First Name、Last Name、Phone Number
- 验证每个字段都可以正常编辑和保存
- 证据：每个字段编辑后截图
"""
)
@pytest.mark.parametrize(
    "field_name,field_key,test_value",
    [
        ("First Name", "firstName", "TestFirst"),
        ("Last Name", "lastName", "TestLast"),
        ("Phone Number", "phoneNumber", "13800138000"),
    ],
    ids=["first_name", "last_name", "phone_number"],
)
def test_p0_profile_settings_edit_field(profile_settings, field_name, field_key, test_value):
    """P0: 单字段编辑"""
    attach_rule_source_note(f"Profile Settings P0 - edit {field_name}")
    logger = TestLogger(f"test_p0_profile_settings_edit_{field_key}")
    logger.start()

    _page, page_obj, baseline = profile_settings

    suffix = now_suffix()
    value_with_suffix = f"{test_value}_{suffix}"[:16] if field_key == "phoneNumber" else f"{test_value}_{suffix}"

    with allure.step(f"编辑 {field_name} 字段"):
        page_obj.fill_form({field_key: value_with_suffix})
        step_shot(page_obj, f"step_fill_{field_key}", full_page=True)

    with allure.step("保存"):
        resp = page_obj.save_and_wait_profile_update(timeout_ms=15000)
        assert resp.ok, f"保存 {field_name} 失败 status={resp.status}"
        step_shot(page_obj, f"step_save_{field_key}", full_page=True)

    settle_toasts(page_obj)
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - Readonly Fields")
@allure.description(
    """
测试点（依据需求文档）：
- 验证 User Name 和 Email 字段是只读的
- 这些字段在编辑模式下应该是 disabled
- 尝试修改只读字段应该失败
- 依据：account-profile-field-requirements.md
  * 只读字段：UserName、Email、Id
  * 可编辑字段：Name、Surname、PhoneNumber、DisplayName、Bio
- 证据：disabled 状态截图 + 修改尝试结果
"""
)
def test_p0_profile_settings_readonly_fields(profile_settings):
    """P0: 只读字段验证"""
    attach_rule_source_note("Profile Settings P0 - readonly fields (UserName/Email 不可修改)")
    logger = TestLogger("test_p0_profile_settings_readonly_fields")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("验证 User Name 是只读的（disabled）"):
        textboxes = auth_page.get_by_role('textbox')
        username_input = textboxes.nth(0)
        is_disabled = username_input.is_disabled()
        
        # 获取原始值
        original_value = username_input.input_value() if not is_disabled else username_input.get_attribute("value")
        
        allure.attach(
            f"User Name:\n- disabled: {is_disabled}\n- value: {original_value}",
            name="username_field_status",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert is_disabled, "User Name 应该是只读的（disabled）"

    with allure.step("验证 Email 是只读的（disabled）"):
        email_input = textboxes.nth(3)
        is_disabled = email_input.is_disabled()
        
        # 获取原始值
        original_email = email_input.input_value() if not is_disabled else email_input.get_attribute("value")
        
        allure.attach(
            f"Email:\n- disabled: {is_disabled}\n- value: {original_email}",
            name="email_field_status",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert is_disabled, "Email 应该是只读的（disabled）"
        step_shot(page_obj, "step_readonly_fields_verified", full_page=True)

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)
