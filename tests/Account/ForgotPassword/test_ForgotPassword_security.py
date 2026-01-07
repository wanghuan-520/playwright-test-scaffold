# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountForgotpassword - Security
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from utils.config import ConfigManager
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.ForgotPassword._helpers import (
    URL_PATH,
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('ForgotPassword' + "_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature('AccountForgotpassword')
@allure.story("Security")
@allure.description(
    """
测试点：
- ForgotPassword 属于匿名页：未登录访问不应跳转登录
- 证据：全页截图
"""
)
def test_security_unauth_redirects_to_login(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/ForgotPassword is anonymous (no redirect)")

    cfg = ConfigManager()
    # ForgotPassword 属于后端匿名页（/Account/*），用 backend base
    base = (cfg.get_service_url("backend") or "").rstrip("/")
    url = f"{base}{URL_PATH}"

    page = unauth_page
    po = AccountForgotpasswordPage(page)
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
    except PlaywrightTimeoutError:
        # 共享环境偶发卡顿：重试一次
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
    
    assert_not_redirected_to_login(page)
    current = page.url or ""
    assert "/Account/ForgotPassword" in current, f"expected stay on forgotpassword page, got: {current}"
    
    # 使用 step_shot 确保截图
    from tests.admin.profile._helpers import step_shot
    step_shot(po, "step_unauth_should_stay_on_forgotpassword", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature('AccountForgotpassword')
@allure.story("Security")
@allure.description(
    """
测试点：
- 精简版：5个代表性 XSS/SQLi/HTML 注入 payload
- 不触发浏览器 dialog（payload 不执行）
- payload 非法 email：应被前端拦截，不应发出写请求（避免真实发码/发邮件副作用）
证据：每个 payload 截图
"""
)
@pytest.mark.parametrize(
    "case_name,payload",
    [
        # ═══════════════════════════════════════════════════════════════
        # 精简版 payload（5个代表性攻击向量）
        # ═══════════════════════════════════════════════════════════════
        ("xss_script", "<script>alert('XSS')</script>"),  # XSS: 经典 script 注入
        ("xss_img", "<img src=x onerror=alert('XSS')>"),  # XSS: 事件触发型
        ("sqli_quote", "' OR '1'='1"),                    # SQLi: 逻辑绕过
        ("sqli_comment", "admin'--"),                     # SQLi: 注释截断
        ("html_bold", "<b>bold</b>"),                     # HTML注入: 标签过滤
    ],
    ids=["xss_script", "xss_img", "sqli_quote", "sqli_comment", "html_bold"],
)
def test_security_xss_payload_no_dialog(unauth_page: Page, case_name: str, payload: str):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/ForgotPassword injection safety (no dialog, no request)")

    page = unauth_page
    po = AccountForgotpasswordPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(_):
        dialog_triggered["value"] = True

    page.on("dialog", on_dialog)

    cfg = ConfigManager()
    base = (cfg.get_service_url("backend") or "").rstrip("/")
    try:
        page.goto(f"{base}{URL_PATH}", wait_until="domcontentloaded", timeout=120000)
    except PlaywrightTimeoutError:
        page.goto(f"{base}{URL_PATH}", wait_until="domcontentloaded", timeout=120000)
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip("Email 输入框不可见（selector 失效或页面结构变化）")

    with allure.step(f"[{case_name}] 填写 payload + 提交（不应弹窗/不应发请求）"):
        allure.attach(payload, name=f"{case_name}_payload", attachment_type=allure.attachment_type.TEXT)
        snap = snapshot_inputs(page, [selector])
        try:
            page.fill(selector, payload)
            page.wait_for_timeout(150)
            step_shot(po, f"step_{case_name}_filled", full_page=True)

            # payload 非法 email：应被前端 validity 拦截，避免触发真实"发码/发邮件"副作用
            click_save(page)
            resp = wait_mutation_response(page, timeout_ms=1500)
            page.wait_for_timeout(200)
            step_shot(po, f"step_{case_name}_after_submit", full_page=True)

            fatal = detect_fatal_error_page(page)
            assert not fatal, f"fatal error page detected: {fatal}"
            assert resp is None, f"{case_name}: expected no mutation request"
            assert dialog_triggered["value"] is False, f"{case_name}: payload triggered a dialog"
        finally:
            try:
                restore_inputs(page, snap)
            except Exception:
                pass

    logger.end(success=True)
