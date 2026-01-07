# ═══════════════════════════════════════════════════════════════
# Account/Login - P2
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.account_login_page import AccountLoginPage
from tests.Account.Login._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger("Login_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2")
def test_p2_fields_visible(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    # 以更稳的 id 作为主断言（ABP 登录表单相对稳定）
    expect(page.locator("#LoginInput_UserNameOrEmailAddress")).to_be_visible()
    expect(page.locator("#LoginInput_Password")).to_be_visible()
    po.take_screenshot("Login_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2")
@allure.description(
    """
测试点：
- 键盘 Tab 导航可用性
- 每按一次 Tab 截图一次，验证焦点移动
证据：每次 Tab 后的截图
"""
)
def test_p2_keyboard_tab_navigation(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("Tab 导航测试：每按一次 Tab 截图一次，并记录焦点状态"):
        # 初始状态
        po.take_screenshot("Login_p2_tab_0_initial", full_page=False)
        
        # 点击第一个输入框
        page.click("#LoginInput_UserNameOrEmailAddress")
        page.wait_for_timeout(300)  # 等待焦点样式渲染
        active_element_1 = page.evaluate("document.activeElement?.id || document.activeElement?.tagName")
        allure.attach(f"焦点元素: {active_element_1}", name="tab_1_focus_state", attachment_type=allure.attachment_type.TEXT)
        po.take_screenshot("Login_p2_tab_1_username_focused", full_page=False)
        
        # 按 Tab 到密码框
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        active_element_2 = page.evaluate("document.activeElement?.id || document.activeElement?.tagName")
        allure.attach(f"焦点元素: {active_element_2}", name="tab_2_focus_state", attachment_type=allure.attachment_type.TEXT)
        po.take_screenshot("Login_p2_tab_2_password_focused", full_page=False)
        
        # 再按 Tab 到登录按钮
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        active_element_3 = page.evaluate("document.activeElement?.id || document.activeElement?.tagName")
        allure.attach(f"焦点元素: {active_element_3}", name="tab_3_focus_state", attachment_type=allure.attachment_type.TEXT)
        po.take_screenshot("Login_p2_tab_3_button_focused", full_page=False)

    logger.end(success=True)


