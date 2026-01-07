# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminSettingsFeatureManagement - P2
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.admin_settings_feature_management_page import AdminSettingsFeatureManagementPage
from tests.admin.settings_feature_management._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger('settings_feature_management_settings' + "_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AdminSettingsFeatureManagement')
@allure.story("P2")
@allure.title("UI：字段可见性 + 全页截图")
def test_p2_fields_visible(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminSettingsFeatureManagementPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = []
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    po.take_screenshot('settings_feature_management_settings' + "_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AdminSettingsFeatureManagement')
@allure.story("P2")
@allure.title("UI：键盘 Tab 可用性")
def test_p2_keyboard_tab_navigation(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminSettingsFeatureManagementPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = []
    if not selectors:
        pytest.skip("未推导出字段 selector（Tab 用例跳过）")

    page.click(selectors[0])
    for _ in range(min(5, len(selectors))):
        page.keyboard.press("Tab")

    po.take_screenshot('settings_feature_management_settings' + "_p2_keyboard_tab")
    logger.end(success=True)
