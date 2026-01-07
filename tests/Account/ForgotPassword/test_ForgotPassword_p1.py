# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountForgotpassword - P1
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.ForgotPassword._helpers import (
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

logger = TestLogger('ForgotPassword' + "_p1")




# Source: dynamic (dom) PageAnalyzer element
@pytest.mark.P1
@pytest.mark.validation
@allure.feature('AccountForgotpassword')
@allure.story('P1')
@allure.description(
    """
测试点：
- 输入非法 email（not-an-email）应被 HTML5 validity 拦截
- 不应发送写请求（避免副作用）
- 证据：提交前后截图
规则来源：docs/requirements/requirements.md（email format 是 ABP 真理源）
"""
)
def test_p1_email_invalid_format_should_fail(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/ForgotPassword invalid email should be blocked (no request)")
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    with allure.step("导航到 /Account/ForgotPassword"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip('Email 字段不可见/不存在（页面结构变化或 selector 失效）')

    original = page.input_value(selector)
    with allure.step("填写非法 email 并提交"):
        page.fill(selector, 'not-an-email')
        step_shot(po, "step_filled_invalid", full_page=True)
        click_save(page)
        page.wait_for_timeout(200)
        step_shot(po, "step_after_submit", full_page=True)

    is_valid = page.eval_on_selector(selector, 'el => el.checkValidity()')
    assert is_valid is False, 'expected HTML5 email validity to reject invalid email'

    resp = wait_mutation_response(page, timeout_ms=1500)
    assert resp is None, 'expected no mutation request when email is invalid'

    page.fill(selector, original)
    click_save(page)
    _ = wait_mutation_response(page, timeout_ms=60000)

    logger.end(success=True)

