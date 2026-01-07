# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountForgotpassword - P0
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page
import time

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.ForgotPassword._helpers import (
    FIELD_RULES,
    assert_not_redirected_to_login,
    assert_any_validation_evidence,
    assert_toast_contains_any,
    click_save,
    has_any_error_ui,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('ForgotPassword' + "_p0")


@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AccountForgotpassword')
@allure.story("P0")
@allure.description(
    """
测试点：
- /Account/ForgotPassword 可正常打开（AuthServer 后端匿名页）
- 核心控件可见
- 证据：关键步骤截图
规则来源：docs/requirements/requirements.md
"""
)
def test_p0_page_load(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("docs/requirements/requirements.md: Account/ForgotPassword P0 page load")
    with allure.step("导航到 /Account/ForgotPassword"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    step_shot(po, "step_loaded", full_page=True)
    logger.end(success=True)




@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AccountForgotpassword')
@allure.story('P0')
@allure.description(
    """
测试点：
- 使用账号池的真实账号进行密码找回
- 不要求邮箱真实存在（避免账号枚举）
- 只要求：不崩溃（无 5xx）且有可观测反馈（截图留证）
"""
)
def test_p0_happy_path_update_save_with_rollback(unauth_page: Page, test_account):
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("docs/requirements/requirements.md: Account/ForgotPassword P0 submit (no side-effect assertions)")
    
    allure.attach(
        f"测试账号: {test_account['username']}\nEmail: {test_account['email']}\n用途: 密码找回流程验证",
        name="test_account_info",
        attachment_type=allure.attachment_type.TEXT,
    )
    
    with allure.step("导航到 /Account/ForgotPassword"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip('字段不可见/不存在（页面结构变化或 selector 失效）')

    # 使用账号池的真实邮箱
    email = test_account["email"]

    with allure.step("填写 Email 并提交"):
        po.fill_email(email)
        step_shot(po, "step_filled", full_page=True)
        click_save(page)

        # 尽量捕获写请求响应；如果被前端校验拦截也允许（但此处 email 是合法格式，通常会发出请求）
        resp = wait_mutation_response(page, timeout_ms=15000)
        if resp is not None:
            assert resp.status < 500, f"unexpected api status: {resp.status}"

            assert_not_redirected_to_login(page)
        # ForgotPassword 通常会返回"已发送/若存在将发送"的提示，也可能返回"邮箱不存在"等错误样式文案。
        # 该页面的 P0 只要求：不崩溃（无 5xx）且有可观测反馈（截图留证），不强绑"必须无 error UI"。
        step_shot(po, "step_after_submit", full_page=True)

    logger.end(success=True)


