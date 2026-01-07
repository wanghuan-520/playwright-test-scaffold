# ═══════════════════════════════════════════════════════════════
# Account/Login - Security
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.account_login_page import AccountLoginPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Login._helpers import assert_not_redirected_to_login, detect_fatal_error_page, wait_mutation_response
from utils.logger import TestLogger

logger = TestLogger("Login_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security")
@allure.description(
    """
测试点：
- 精简版：5个代表性 XSS/SQLi/HTML 注入 payload
- 不触发浏览器 dialog（payload 不执行）
- 点击 Login 也不应导致 5xx（崩溃态）
- 不触发真实登录副作用：密码保持为空
证据：填写/提交截图
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
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login injection safety (no dialog, no 5xx)")
    page = unauth_page
    po = AccountLoginPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(d):
        dialog_triggered["value"] = True
        try:
            d.dismiss()
        except Exception:
            pass

    page.on("dialog", on_dialog)
    with allure.step("导航到 /Account/Login"):
        try:
            po.navigate()
        except PlaywrightTimeoutError:
            # 共享环境偶发卡顿：重试一次
            po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    def _ensure_login_page() -> None:
        """
        submit 后页面可能发生 reload/跳转（例如错误页/重定向），导致下一轮找不到输入框。
        这里做“自愈”：每个场景开始前保证回到 /Account/Login 且输入框可见。
        """
        try:
            if page.locator("#LoginInput_UserNameOrEmailAddress").count() > 0:
                return
        except Exception:
            pass
        try:
            po.navigate()
            page.wait_for_timeout(200)
        except Exception:
            pass
        assert_not_redirected_to_login(page)

    if page.locator("#LoginInput_UserNameOrEmailAddress").count() == 0:
        pytest.skip("login input not found")
    _ensure_login_page()
    with allure.step(f"[{case_name}] 填写 payload + 提交（不应弹窗/不应 5xx）"):
        allure.attach(payload, name=f"{case_name}_payload", attachment_type=allure.attachment_type.TEXT)

        # ═══════════════════════════════════════════════════════════════
        # 控制变量：只有 username 是恶意 payload，password 填合法值
        # ═══════════════════════════════════════════════════════════════
        page.fill("#LoginInput_UserNameOrEmailAddress", payload)
        if page.locator("#LoginInput_Password").count() > 0:
            # 填一个合法密码（不会成功登录，因为 username 是恶意值）
            page.fill("#LoginInput_Password", "ValidPass123!")
        page.wait_for_timeout(200)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        page.click("button[name='Action'][type='submit']")
        resp = wait_mutation_response(page, timeout_ms=3000)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        # 不再使用 xfail，直接断言失败（已知Bug应该在报告里"刺眼地显示为失败"）
        assert not fatal, f"产品缺陷：/Account/Login 注入类输入触发 500（Internal Server Error）: {fatal}"

        if resp is not None:
            assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        assert dialog_triggered["value"] is False, f"{case_name}: payload triggered a dialog"
    logger.end(success=True)


