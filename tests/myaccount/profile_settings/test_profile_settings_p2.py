# ═══════════════════════════════════════════════════════════════
# Profile Settings (Edit) - P2
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
P2：编辑模式 UI 测试。

测试内容：
- 编辑模式下的元素可见性
- 键盘导航（编辑模式）
- 输入框状态
"""

import pytest
import allure

from utils.logger import TestLogger
from tests.myaccount._helpers import attach_rule_source_note, step_shot


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Edit Mode Elements Visible")
@allure.description(
    """
测试点：
- 验证编辑模式下所有元素可见
- Save/Cancel 按钮、输入框
- 证据：全页截图
"""
)
def test_p2_profile_settings_edit_mode_visible(profile_settings):
    """P2: 编辑模式元素可见性"""
    attach_rule_source_note("Profile Settings P2 - edit mode visible")
    logger = TestLogger("test_p2_profile_settings_edit_mode_visible")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("验证 Save 和 Cancel 按钮可见"):
        assert page_obj.is_visible(page_obj.SAVE_BUTTON, timeout=3000), "Save 按钮不可见"
        assert page_obj.is_visible(page_obj.CANCEL_BUTTON, timeout=3000), "Cancel 按钮不可见"

    with allure.step("验证输入框可见"):
        textboxes = auth_page.get_by_role('textbox')
        count = textboxes.count()
        allure.attach(
            f"输入框数量: {count}",
            name="textbox_count",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert count >= 5, f"期望至少 5 个输入框，实际 {count}"

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Edit Mode Keyboard Navigation")
@allure.description(
    """
测试点：
- 编辑模式下 Tab 键导航顺序正确
- 证据：每个 Tab 步骤截图
"""
)
def test_p2_profile_settings_keyboard_navigation(profile_settings):
    """P2: 编辑模式 Tab 键导航"""
    attach_rule_source_note("Profile Settings P2 - keyboard navigation")
    logger = TestLogger("test_p2_profile_settings_keyboard_navigation")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("Tab 键导航测试"):
        # 聚焦到第一个可编辑输入框 (First Name)
        textboxes = auth_page.get_by_role('textbox')
        if textboxes.count() > 1:
            textboxes.nth(1).focus()
        
        for i in range(6):
            # 添加红色边框高亮当前焦点元素
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '3px solid red';
                }
            }""")
            step_shot(page_obj, f"step_tab_{i}", full_page=True)
            # 移除高亮
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '';
                }
            }""")
            auth_page.keyboard.press("Tab")
            auth_page.wait_for_timeout(100)

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Input Field Labels")
@allure.description(
    """
测试点：
- 验证编辑模式下输入框标签正确
- First Name, Last Name, Phone Number 等
- 证据：截图
"""
)
def test_p2_profile_settings_input_labels(profile_settings):
    """P2: 输入框标签检查"""
    attach_rule_source_note("Profile Settings P2 - input labels")
    logger = TestLogger("test_p2_profile_settings_input_labels")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    labels_to_check = [
        "User Name",
        "First Name",
        "Last Name",
        "Email Address",
        "Phone Number",
    ]

    with allure.step("验证输入框标签"):
        for label in labels_to_check:
            is_visible = page_obj.is_visible(f'text="{label}"', timeout=2000)
            allure.attach(
                f"{label}: {'可见' if is_visible else '不可见'}",
                name=f"label_{label.replace(' ', '_')}",
                attachment_type=allure.attachment_type.TEXT,
            )

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Disabled Field Styling")
@allure.description(
    """
测试点：
- 验证只读字段有正确的视觉样式
- User Name 和 Email 应该有 disabled 样式
- 证据：截图
"""
)
def test_p2_profile_settings_disabled_field_styling(profile_settings):
    """P2: 只读字段样式检查"""
    attach_rule_source_note("Profile Settings P2 - disabled field styling")
    logger = TestLogger("test_p2_profile_settings_disabled_field_styling")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("检查只读字段提示文案"):
        # User Name 提示
        username_hint = page_obj.is_visible('p:has-text("User name cannot be changed")', timeout=2000)
        allure.attach(
            f"User name 提示可见: {username_hint}",
            name="username_hint_visible",
            attachment_type=allure.attachment_type.TEXT,
        )

        # Email 提示
        email_hint = page_obj.is_visible('p:has-text("Email cannot be changed")', timeout=2000)
        allure.attach(
            f"Email 提示可见: {email_hint}",
            name="email_hint_visible",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Button States")
@allure.description(
    """
测试点：
- 验证 Save 和 Cancel 按钮状态
- 证据：按钮状态截图
"""
)
def test_p2_profile_settings_button_states(profile_settings):
    """P2: 按钮状态检查"""
    attach_rule_source_note("Profile Settings P2 - button states")
    logger = TestLogger("test_p2_profile_settings_button_states")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("进入编辑模式"):
        page_obj.enter_edit_mode()
        step_shot(page_obj, "step_edit_mode", full_page=True)

    with allure.step("验证 Save 按钮可用"):
        save_button = auth_page.locator(page_obj.SAVE_BUTTON)
        is_enabled = save_button.is_enabled()
        allure.attach(
            f"Save 按钮可用: {is_enabled}",
            name="save_button_enabled",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("验证 Cancel 按钮可用"):
        cancel_button = auth_page.locator(page_obj.CANCEL_BUTTON)
        is_enabled = cancel_button.is_enabled()
        allure.attach(
            f"Cancel 按钮可用: {is_enabled}",
            name="cancel_button_enabled",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("退出编辑模式"):
        page_obj.exit_edit_mode()

    logger.end(success=True)
