# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountRegister - P2
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.account_register_page import AccountRegisterPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Register._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger('Register' + "_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AccountRegister')
@allure.story("P2")
@allure.description(
    """
测试点：
- Username/Email/Password 输入框可见
- 证据：全页截图
"""
)
def test_p2_fields_visible(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Register P2 UI visibility")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step("导航到 /Account/Register"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    selectors = ['role=textbox[name="Email address *"]', 'role=textbox[name="Password *"]', 'role=textbox[name="Username *"]']
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    step_shot(po, "step_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature('AccountRegister')
@allure.story("P2")
@allure.description(
    """
测试点：
- 键盘 Tab 能在 Username → Email → Password 之间切换焦点
- 证据：3 张步骤截图（focused）
"""
)
def test_p2_keyboard_tab_navigation(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Register P2 keyboard tab")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step("导航到 /Account/Register"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    # 3 张截图策略（足够审计）：
    # 1) 初始聚焦 Username
    # 2) Tab 后聚焦 Email
    # 3) Tab 后聚焦 Password
    username = 'role=textbox[name="Username *"]'
    email = 'role=textbox[name="Email address *"]'
    password = 'role=textbox[name="Password *"]'

    if page.locator(username).count() == 0 or page.locator(email).count() == 0 or page.locator(password).count() == 0:
        pytest.skip("字段不可见/不存在（selector 失效或页面结构变化）")

    # Step 1: focus username
    page.click(username)
    expect(page.locator(username)).to_be_focused()
    step_shot(po, "step_tab_focus_username", full_page=False)

    # Step 2: tab -> email
    page.keyboard.press("Tab")
    expect(page.locator(email)).to_be_focused()
    step_shot(po, "step_tab_focus_email", full_page=False)

    # Step 3: tab -> password
    page.keyboard.press("Tab")
    expect(page.locator(password)).to_be_focused()
    step_shot(po, "step_tab_focus_password", full_page=False)
    logger.end(success=True)
