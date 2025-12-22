# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword - P2
# Generated: 2025-12-22 13:06:47
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from tests.admin.profile_change_password._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger('profile_change_password_settings' + "_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AdminProfileChangePassword')
@allure.story("P2")
@allure.title("UI：字段可见性 + 全页截图")
def test_p2_fields_visible(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminProfileChangePasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = ["[name='confirmNewPassword']", "[name='currentPassword']", "[name='newPassword']"]
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    po.take_screenshot('profile_change_password_settings' + "_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AdminProfileChangePassword')
@allure.story("P2")
@allure.title("UI：键盘 Tab 可用性")
def test_p2_keyboard_tab_navigation(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminProfileChangePasswordPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = ["[name='confirmNewPassword']", "[name='currentPassword']", "[name='newPassword']"]
    if not selectors:
        pytest.skip("未推导出字段 selector（Tab 用例跳过）")

    page.click(selectors[0])
    for _ in range(min(5, len(selectors))):
        page.keyboard.press("Tab")

    po.take_screenshot('profile_change_password_settings' + "_p2_keyboard_tab")
    logger.end(success=True)
