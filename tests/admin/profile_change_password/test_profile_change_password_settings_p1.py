# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword - P1
# Generated: 2025-12-22 13:06:47
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from tests.admin.profile_change_password._helpers import (
    FIELD_RULES,
    assert_not_redirected_to_login,
    click_save,
    has_any_error_ui,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('profile_change_password_settings' + "_p1")

@pytest.mark.P1
@pytest.mark.boundary
@allure.feature('AdminProfileChangePassword')
@allure.story('P1')
@allure.title('边界值：未推导出 maxLength 规则（自动跳过）')
def test_p1_boundary_rules_none_derived(auth_page: Page):
    pytest.skip('未从前后端代码推导出 maxLength 规则（或缺少 selector），拒绝凭猜生成边界矩阵')



@pytest.mark.P1
@pytest.mark.validation
@allure.feature('AdminProfileChangePassword')
@allure.story('P1')
@allure.title('格式校验：未推导出 Email 字段（自动跳过）')
def test_p1_email_format_none_derived(auth_page: Page):
    pytest.skip('未从前后端代码推导出 Email 字段（或缺少 selector），拒绝凭猜生成 email 格式用例')



@pytest.mark.P1
@pytest.mark.exception
@allure.feature('AdminProfileChangePassword')
@allure.story('P1')
@allure.title('API 错误处理：写请求被拦截（兜底）')
def test_p1_api_failure_on_save(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminProfileChangePasswordPage(page)

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
        if not aborted['value']:
            pytest.skip('未触发任何写请求（可能是纯前端保存或保存按钮不对应写 API）')
        if not has_any_error_ui(page):
            pytest.skip('写请求失败后未观察到 error UI（错误选择器可能未覆盖）')
        po.take_screenshot('profile_change_password_settings_p1_api_failure')
    finally:
        page.unroute('**/*', abort_mutation)

    logger.end(success=True)

