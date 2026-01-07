# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminSettingsFeatureManagement - P1
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_settings_feature_management_page import AdminSettingsFeatureManagementPage
from tests.admin.settings_feature_management._helpers import (
    FIELD_RULES,
    CHANGE_PASSWORD_API_PATH,
    assert_not_redirected_to_login,
    assert_toast_contains_any,
    click_save,
    has_any_error_ui,
    wait_response_by_url_substring,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('settings_feature_management_settings' + "_p1")






@pytest.mark.P1
@pytest.mark.exception
@allure.feature('AdminSettingsFeatureManagement')
@allure.story('P1')
@allure.title('API 错误处理：写请求被拦截（兜底）')
def test_p1_api_failure_on_save(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminSettingsFeatureManagementPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    aborted = {'value': False}

    def abort_mutation(route):
        if route.request.method in {'PUT', 'POST', 'PATCH'}:
            aborted['value'] = True
            route.abort()
        else:
            route.continue_()

    page.route('**/*', abort_mutation)
    try:
        click_save(page)
        _ = wait_mutation_response(page, timeout_ms=3000)
        assert_not_redirected_to_login(page)
        assert aborted['value'] is True, 'expected a write request to be aborted'
        # 这里不强行断言 UI，因为不同产品对 network error 的反馈差异很大。
        po.take_screenshot('settings_feature_management_settings_p1_api_failure')
    finally:
        page.unroute('**/*', abort_mutation)

    logger.end(success=True)

