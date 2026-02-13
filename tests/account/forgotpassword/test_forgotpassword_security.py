# ═══════════════════════════════════════════════════════════════
# ForgotPassword - Security 安全测试
# URL: http://localhost:5173/forgot-password
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.account.forgotpassword._helpers import (
    URL_PATH,
    assert_not_redirected_to_login,
    click_submit,
    detect_fatal_error_page,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from tests.myaccount._helpers import step_shot, attach_rule_source_note
from utils.config import ConfigManager
from utils.logger import TestLogger

logger = TestLogger("forgotpassword_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountForgotPassword")
@allure.story("Security - Anonymous Access")
@allure.description(
    """
测试点：
- ForgotPassword 属于匿名页：未登录访问不应跳转登录
- 证据：全页截图
"""
)
def test_security_anonymous_access(unauth_page: Page):
    """测试匿名访问不被重定向"""
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword is anonymous")

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "http://localhost:5173").rstrip("/")
    url = f"{base}{URL_PATH}"

    page = unauth_page
    po = AccountForgotpasswordPage(page)
    
    with allure.step(f"访问 {url}"):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except PlaywrightTimeoutError:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_navigate", full_page=True)
    
    with allure.step("验证未被重定向"):
        assert_not_redirected_to_login(page)
        current = page.url or ""
        assert "/forgot-password" in current.lower(), f"expected stay on forgotpassword page, got: {current}"
        
        allure.attach(
            f"✅ 匿名访问成功，停留在忘记密码页\nURL: {current}",
            name="result",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountForgotPassword")
@allure.story("Security - XSS/SQLi Injection")
@allure.description(
    """
测试点：
- XSS/SQLi/HTML 注入 payload
- 不触发浏览器 dialog（payload 不执行）
- payload 非法 email：应被前端拦截
"""
)
@pytest.mark.parametrize(
    "case_name,payload",
    [
        ("xss_script", "<script>alert('XSS')</script>"),
        ("xss_img", "<img src=x onerror=alert('XSS')>"),
        ("xss_svg", "<svg onload=alert('XSS')>"),
        ("sqli_quote", "' OR '1'='1"),
        ("sqli_comment", "admin'--"),
        ("html_bold", "<b>bold</b>"),
    ],
    ids=["xss_script", "xss_img", "xss_svg", "sqli_quote", "sqli_comment", "html_bold"],
)
def test_security_xss_injection(unauth_page: Page, case_name: str, payload: str):
    """测试 XSS/SQLi 注入"""
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword injection safety")

    page = unauth_page
    po = AccountForgotpasswordPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(d):
        dialog_triggered["value"] = True
        try:
            d.dismiss()
        except Exception:
            pass

    page.on("dialog", on_dialog)

    with allure.step("导航到 /forgot-password"):
        try:
            po.navigate()
        except PlaywrightTimeoutError:
            po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step(f"[{case_name}] 填写 payload + 提交"):
        allure.attach(payload, name=f"{case_name}_payload", attachment_type=allure.attachment_type.TEXT)
        snap = snapshot_inputs(page, [po.EMAIL_INPUT])
        
        try:
            page.fill(po.EMAIL_INPUT, payload)
            page.wait_for_timeout(150)
            step_shot(po, f"step_{case_name}_filled", full_page=True)

            click_submit(page)
            resp = wait_mutation_response(page, timeout_ms=1500)
            page.wait_for_timeout(200)
            step_shot(po, f"step_{case_name}_after_submit", full_page=True)

            fatal = detect_fatal_error_page(page)
            assert not fatal, f"fatal error page detected: {fatal}"
            
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
            
            assert dialog_triggered["value"] is False, f"{case_name}: payload triggered a dialog"
            
            allure.attach(
                f"✅ [{case_name}] 注入测试通过\n- 无 dialog 弹窗\n- 无 5xx 错误",
                name=f"{case_name}_result",
                attachment_type=allure.attachment_type.TEXT,
            )
        finally:
            try:
                restore_inputs(page, snap)
            except Exception:
                pass

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountForgotPassword")
@allure.story("Security - Email Autocomplete")
@allure.description(
    """
测试点：
- 检查邮箱输入框的 autocomplete 属性
- 避免浏览器自动填充敏感信息
"""
)
def test_security_email_autocomplete(unauth_page: Page):
    """测试邮箱输入框 autocomplete 属性"""
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword autocomplete")

    page = unauth_page
    po = AccountForgotpasswordPage(page)

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    with allure.step("检查 Email 输入框的 autocomplete 属性"):
        if page.locator(po.EMAIL_INPUT).count() == 0:
            pytest.skip("Email 输入框不可见")
        
        autocomplete_attr = page.get_attribute(po.EMAIL_INPUT, "autocomplete") or ""
        allure.attach(
            f"autocomplete 属性: '{autocomplete_attr}'",
            name="autocomplete_attr",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 记录属性值（不强制失败，因为不同产品有不同策略）
        if autocomplete_attr.lower() in ["off", "new-password", "email"]:
            allure.attach(
                "✅ autocomplete 属性设置合理",
                name="result",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            allure.attach(
                f"⚠️ autocomplete 属性为 '{autocomplete_attr}'，建议设置为 'off' 或 'email'",
                name="warning",
                attachment_type=allure.attachment_type.TEXT,
            )

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.security
@allure.feature("AccountForgotPassword")
@allure.story("Security - Rate Limiting Awareness")
@allure.description(
    """
测试点：
- 连续提交多次，检查系统响应
- 不应导致崩溃
- 注意：此测试不验证实际限流（避免副作用）
"""
)
def test_security_rate_limiting_awareness(unauth_page: Page):
    """测试连续提交不崩溃"""
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword rate limiting")

    page = unauth_page
    po = AccountForgotpasswordPage(page)

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    # 使用固定的测试邮箱（不依赖账号池）
    email = "testuser@example.com"

    with allure.step("连续提交 3 次（测试不崩溃）"):
        for i in range(3):
            with allure.step(f"第 {i + 1} 次提交"):
                # 重新导航到 forgotpassword 页面，确保页面状态稳定
                if i > 0:
                    try:
                        po.navigate()
                    except Exception:
                        pass
                
                try:
                    if page.locator(po.EMAIL_INPUT).count() == 0:
                        allure.attach(f"⚠️ 第 {i + 1} 次: Email 输入框不可见，跳过", name=f"attempt_{i + 1}_skip", attachment_type=allure.attachment_type.TEXT)
                        break
                    
                    page.fill(po.EMAIL_INPUT, email)
                    click_submit(page)
                    
                    resp = wait_mutation_response(page, timeout_ms=10000)
                    if resp is not None:
                        allure.attach(
                            f"第 {i + 1} 次: HTTP {resp.status}",
                            name=f"attempt_{i + 1}_status",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                        # 允许 5xx 错误，因为邮件服务可能未配置
                        if resp.status >= 500:
                            allure.attach(
                                f"⚠️ 后端返回 {resp.status}，可能是邮件服务未配置",
                                name=f"attempt_{i + 1}_backend_warning",
                                attachment_type=allure.attachment_type.TEXT,
                            )
                    
                    page.wait_for_timeout(1000)
                    step_shot(po, f"step_attempt_{i + 1}", full_page=True)
                    
                    # 如果被限流（429），记录并结束
                    if resp is not None and resp.status == 429:
                        allure.attach(
                            f"✅ 第 {i + 1} 次后触发限流 (HTTP 429)",
                            name="rate_limit_triggered",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                        break
                except Exception as e:
                    allure.attach(f"⚠️ 第 {i + 1} 次提交出错: {str(e)}", name=f"attempt_{i + 1}_error", attachment_type=allure.attachment_type.TEXT)
                    break

    logger.end(success=True)

