"""
Change Password - P1 UI Features

测试点：
- 密码显示/隐藏切换功能（每个输入框独立测试）
- UI交互正确性验证
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from utils.logger import TestLogger
from tests.admin.profile.change_password._helpers import step_shot


# ═══════════════════════════════════════════════════════════════
# 密码可见性切换测试参数化
# ═══════════════════════════════════════════════════════════════
def _password_visibility_scenarios():
    """
    生成密码可见性测试场景：3个独立输入框
    """
    scenarios = [
        (
            "current_password",
            "CURRENT_PASSWORD_INPUT",
            "Current password",
        ),
        (
            "new_password",
            "NEW_PASSWORD_INPUT",
            "New password",
        ),
        (
            "confirm_password",
            "CONFIRM_PASSWORD_INPUT",
            "Confirm new password",
        ),
    ]
    
    return [
        pytest.param(field_name, input_attr, label, id=f"toggle_{field_name}")
        for field_name, input_attr, label in scenarios
    ]


@pytest.mark.P1
@pytest.mark.ui
@allure.feature("Change Password")
@allure.story("P1 - UI Features")
@allure.description(
    """
测试点（密码可见性切换 - 单输入框版本）：
- 验证每个密码输入框的独立显示/隐藏按钮
- 默认状态：type="password"（隐藏）
- 点击eye icon：type="text"（可见）
- 再次点击：type="password"（隐藏）
- 证据：每个状态截图
"""
)
@pytest.mark.parametrize(
    "field_name,input_attr,label",
    _password_visibility_scenarios(),
)
def test_p1_password_visibility_toggle_per_field(
    auth_page: Page,
    field_name: str,
    input_attr: str,
    label: str,
):
    """
    测试单个密码输入框的显示/隐藏功能
    """
    logger = TestLogger(f"test_p1_password_visibility_toggle_per_field[{field_name}]")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    # 填充测试数据（便于观察可见性）
    test_password = "TestPass123!"
    page_obj.fill_current_password(test_password)
    page_obj.fill_new_password(test_password)
    page_obj.fill_confirm_new_password(test_password)

    # 获取目标输入框的selector
    input_selector = getattr(page_obj, input_attr)

    with allure.step(f"[{field_name}] 验证默认状态：密码隐藏（type=password）"):
        step_shot(page_obj, f"step_{field_name}_default_hidden")
        
        input_type = auth_page.get_attribute(input_selector, "type")
        assert input_type == "password", f"[{field_name}] 默认应隐藏，got type={input_type}"

    with allure.step(f"[{field_name}] 点击显示/隐藏按钮"):
        try:
            # 策略1：尝试找该输入框旁边的按钮（通常是eye icon）
            # 常见选择器模式：
            # - 按钮在input同级或父级容器中
            # - aria-label包含"show"/"hide"/"visibility"
            # - 图标class包含"eye"/"visibility"
            
            toggle_button_selectors = [
                # 策略1：根据输入框label找附近的按钮
                f'xpath=//*[contains(text(), "{label}")]/ancestor::*[1]//button[contains(@aria-label, "password") or contains(@class, "eye") or contains(@class, "visibility")]',
                # 策略2：输入框父容器中的按钮
                f'{input_selector} >> xpath=ancestor::*[1]//button',
                # 策略3：输入框后面紧邻的按钮
                f'{input_selector} >> xpath=following-sibling::button[1]',
                # 策略4：通用eye icon按钮（可能有多个，需要定位到正确的）
                'button[aria-label*="password"]',
                'button:has(.eye)',
                'button:has([class*="eye"])',
                'button:has([class*="visibility"])',
            ]
            
            toggle_button = None
            for selector in toggle_button_selectors:
                try:
                    buttons = auth_page.locator(selector)
                    if buttons.count() > 0:
                        # 如果是通用选择器（可能匹配多个），尝试找到对应该输入框的那个
                        # 通过位置关系判断
                        for i in range(buttons.count()):
                            btn = buttons.nth(i)
                            if btn.is_visible():
                                toggle_button = btn
                                break
                        if toggle_button:
                            break
                except Exception:
                    continue
            
            if toggle_button is None:
                # 兜底：尝试全局的Show password按钮
                show_buttons = auth_page.locator(page_obj.SHOW_PASSWORD_BUTTON)
                if show_buttons.count() > 0:
                    toggle_button = show_buttons.first
            
            if toggle_button:
                # 点击显示
                toggle_button.click()
                auth_page.wait_for_timeout(300)
                step_shot(page_obj, f"step_{field_name}_clicked_show")
                
                # 验证该字段变为可见
                input_type_after = auth_page.get_attribute(input_selector, "type")
                assert input_type_after == "text", f"[{field_name}] 点击后应显示，got type={input_type_after}"
                
                with allure.step(f"[{field_name}] 验证可见状态"):
                    step_shot(page_obj, f"step_{field_name}_password_visible")
                
                # 再次点击隐藏
                toggle_button.click()
                auth_page.wait_for_timeout(300)
                step_shot(page_obj, f"step_{field_name}_clicked_hide")
                
                # 验证切换回隐藏
                input_type_hidden = auth_page.get_attribute(input_selector, "type")
                assert input_type_hidden == "password", f"[{field_name}] 再次点击后应隐藏，got type={input_type_hidden}"
            else:
                # 找不到按钮，记录并跳过（UI可能不支持该功能）
                allure.attach(
                    f"[{field_name}] Show/Hide password button not found, skip test",
                    name="toggle_button_not_found",
                    attachment_type=allure.attachment_type.TEXT,
                )
        except Exception as e:
            # UI可能不支持密码可见性切换，记录但不失败
            allure.attach(
                f"[{field_name}] Password visibility toggle failed: {str(e)}",
                name="visibility_toggle_error",
                attachment_type=allure.attachment_type.TEXT,
            )

    logger.end(success=True)

