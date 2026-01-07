# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountLogin - P0
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Login._helpers import (
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

logger = TestLogger('Login' + "_p0")


@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AccountLogin')
@allure.story("P0")
@allure.description(
    """
测试点：
- /Account/Login 可正常打开（AuthServer 后端匿名页）
- 核心控件可见
- 证据：关键步骤截图（navigate / loaded）
规则来源：docs/requirements/requirements.md（ABP 真理源 + 前端可观测）
"""
)
def test_p0_page_load(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login P0 page load")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到 /Account/Login"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    step_shot(po, "step_loaded", full_page=True)
    logger.end(success=True)




@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AccountLogin')
@allure.story('P0')
@allure.description(
    """
测试点：
- 使用账号池的测试账号登录
- 验证登录成功（跳转到首页或无错误）
- 无风险：账号池账号可重复登录
证据：登录前后截图
"""
)
def test_p0_login_success_with_account_pool(unauth_page: Page, test_account):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login P0 login success")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到 /Account/Login"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写账号池账号并登录"):
        page.fill("#LoginInput_UserNameOrEmailAddress", test_account["username"])
        page.fill("#LoginInput_Password", test_account["password"])
        step_shot(po, "step_before_login", full_page=True)
        
        page.click("button[name='Action'][type='submit']")
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    # 成功判据：不在登录页（跳转到首页）或没有错误UI
    current_url = page.url or ""
    if "/Account/Login" in current_url:
        # 仍在登录页，检查是否有错误（可能是账号问题）
        assert not has_any_error_ui(page), "登录失败：出现错误UI"
    # 否则已跳转，视为成功

    logger.end(success=True)


