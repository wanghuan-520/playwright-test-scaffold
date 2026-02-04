# ═══════════════════════════════════════════════════════════════
# Account/Login - P0 关键路径测试
# ═══════════════════════════════════════════════════════════════
"""
P0 测试内容：
- 页面加载
- 登录成功（使用账号池）
"""

import allure
import pytest
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.settings.profile._helpers import attach_rule_source_note, step_shot
from tests.account.login._helpers import (
    assert_not_redirected_to_login,
    get_first_available_account,
    has_any_error_ui,
)
from utils.logger import TestLogger

logger = TestLogger("login_p0")


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P0")
@allure.description(
    """
测试点：
- /Account/Login 可正常打开（AuthServer 后端匿名页）
- 核心控件可见
证据：关键步骤截图
"""
)
def test_p0_page_load(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/account-login-field-requirements.md: Page load")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    step_shot(po, "step_loaded", full_page=True)
    
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P0")
@allure.description(
    """
测试点：
- 使用账号池的测试账号登录
- 验证登录成功（跳转到首页或无错误）
证据：登录前后截图
"""
)
def test_p0_login_success_with_account_pool(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/account-login-field-requirements.md: Login success")
    page = unauth_page
    po = AccountLoginPage(page)

    # 从 _helpers 获取账号
    test_account = get_first_available_account()
    if not test_account:
        pytest.skip("No available account in pool")

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写账号池账号并登录"):
        po.fill_username_or_email_address(test_account["username"])
        po.fill_password(test_account["password"])
        step_shot(po, "step_before_login", full_page=True)
        
        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录结果"):
    current_url = page.url or ""
        if "/login" in current_url.lower() or "/account/login" in current_url.lower():
        assert not has_any_error_ui(page), "登录失败：出现错误UI"
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)
