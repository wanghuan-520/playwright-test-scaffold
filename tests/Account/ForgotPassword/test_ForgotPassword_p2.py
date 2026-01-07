# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountForgotpassword - P2
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.Account.ForgotPassword._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger('ForgotPassword' + "_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AccountForgotpassword')
@allure.story("P2")
def test_p2_fields_visible(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = ['role=textbox[name="Email *"]']
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    po.take_screenshot('ForgotPassword' + "_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AccountForgotpassword')
@allure.story("P2")
def test_p2_keyboard_tab_navigation(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = ['role=textbox[name="Email *"]']
    if not selectors:
        pytest.skip("未推导出字段 selector（Tab 用例跳过）")

    page.click(selectors[0])
    for _ in range(min(5, len(selectors))):
        page.keyboard.press("Tab")

    po.take_screenshot('ForgotPassword' + "_p2_keyboard_tab")
    logger.end(success=True)
