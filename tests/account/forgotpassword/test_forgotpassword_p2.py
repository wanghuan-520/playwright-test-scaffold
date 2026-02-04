# ═══════════════════════════════════════════════════════════════
# ForgotPassword - P2 UI 可见性测试
# URL: http://localhost:5173/forgot-password
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.account.forgotpassword._helpers import assert_not_redirected_to_login
from tests.admin.settings.profile._helpers import step_shot
from utils.logger import TestLogger

logger = TestLogger("forgotpassword_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountForgotPassword")
@allure.story("P2 - Fields Visible")
@allure.description(
    """
测试点：
- 验证页面核心控件可见
- Email 输入框、提交按钮、返回登录链接
"""
)
def test_p2_fields_visible(unauth_page: Page):
    """测试页面字段可见性"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证 Email 输入框可见"):
        expect(page.locator(po.EMAIL_INPUT)).to_be_visible()
    
    with allure.step("验证提交按钮可见"):
        expect(page.locator(po.SUBMIT_BUTTON)).to_be_visible()
    
    with allure.step("验证返回登录链接可见"):
        expect(page.locator(po.BACK_TO_LOGIN_LINK)).to_be_visible()

    step_shot(po, "forgotpassword_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountForgotPassword")
@allure.story("P2 - Keyboard Tab Navigation")
@allure.description(
    """
测试点：
- 键盘 Tab 导航测试
- 验证焦点切换顺序
"""
)
def test_p2_keyboard_tab_navigation(unauth_page: Page):
    """测试键盘 Tab 导航"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("点击 Email 输入框开始 Tab 导航"):
        page.click(po.EMAIL_INPUT)
        step_shot(po, "step_focus_email", full_page=True)
    
    with allure.step("Tab 切换到提交按钮"):
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)
        
        # 添加红色边框高亮
        page.evaluate("""() => {
            const focused = document.activeElement;
            if (focused) {
                focused.style.outline = '3px solid red';
                focused.style.outlineOffset = '2px';
            }
        }""")
        step_shot(po, "step_tab_to_submit", full_page=True)
    
    with allure.step("Tab 切换到返回登录链接"):
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)
        
        page.evaluate("""() => {
            const focused = document.activeElement;
            if (focused) {
                focused.style.outline = '3px solid red';
                focused.style.outlineOffset = '2px';
            }
        }""")
        step_shot(po, "step_tab_to_back_link", full_page=True)

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountForgotPassword")
@allure.story("P2 - Page Title")
@allure.description(
    """
测试点：
- 验证页面标题正确
"""
)
def test_p2_page_title(unauth_page: Page):
    """测试页面标题"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证页面标题"):
        # 检查页面包含 "Forgot Password" 标题
        heading = page.locator("h2:has-text('Forgot Password')")
        expect(heading).to_be_visible()
        
        allure.attach(
            f"页面标题元素可见",
            name="title_check",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(po, "step_page_title", full_page=True)

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountForgotPassword")
@allure.story("P2 - Placeholder Text")
@allure.description(
    """
测试点：
- 验证输入框 placeholder 文本
"""
)
def test_p2_placeholder_text(unauth_page: Page):
    """测试输入框 placeholder"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证 Email 输入框 placeholder"):
        placeholder = page.get_attribute(po.EMAIL_INPUT, "placeholder") or ""
        allure.attach(
            f"placeholder: '{placeholder}'",
            name="email_placeholder",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        assert "email" in placeholder.lower(), f"unexpected placeholder: {placeholder}"
        step_shot(po, "step_placeholder", full_page=True)

    logger.end(success=True)

