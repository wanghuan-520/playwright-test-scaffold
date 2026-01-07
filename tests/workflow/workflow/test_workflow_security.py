# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# Workflow - Security
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
import re
from playwright.sync_api import Page

from utils.config import ConfigManager
from tests.workflow.workflow._helpers import (
    URL_PATH,
    assert_not_redirected_to_login,
    click_save,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('workflow' + "_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature('Workflow')
@allure.story("Security")
@allure.title("未登录访问受保护页面应跳转登录")
def test_security_unauth_redirects_to_login(unauth_page: Page):
    logger.start()

    if False is False:
        pytest.skip("页面不在 /admin/ 路由下，默认不强制要求鉴权跳转")

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{base}{URL_PATH}"

    page = unauth_page
    # 只要“发生导航并提交”即可，login 页是否完成 domcontentloaded 不应影响鉴权跳转判断
    page.goto(url, wait_until="commit", timeout=60000)
    page.wait_for_url(re.compile(r".*(/auth/login|/Account/Login).*"), timeout=60000)

    current = page.url or ""
    assert "/auth/login" in current or "/Account/Login" in current, f"expected redirect to login, got: {current}"
    page.screenshot(path=f"screenshots/workflow_security_unauth_redirect.png", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature('Workflow')
@allure.story("Security")
@allure.title("XSS/SQLi payload 不得触发 dialog")
def test_security_xss_payload_no_dialog(auth_page: Page):
    logger.start()

    page = auth_page

    dialog_triggered = {"value": False}

    def on_dialog(_):
        dialog_triggered["value"] = True

    page.on("dialog", on_dialog)

    page.goto("https://localhost:3000" + URL_PATH, wait_until="domcontentloaded", timeout=60000)
    assert_not_redirected_to_login(page)

    selectors = []
    if not selectors:
        pytest.skip("未推导出可注入的输入框 selector（拒绝凭猜）")

    snap = snapshot_inputs(page, [{"selector": s} for s in selectors])
    try:
        payloads = [
            "<img src=x onerror=alert(1)>",
            "' OR 1=1 --",
            "<script>alert(1)</script>",
        ]

        for sel in selectors:
            if page.locator(sel).count() == 0:
                continue
            for payload in payloads:
                page.fill(sel, payload)
                click_save(page)
                resp = wait_mutation_response(page, timeout_ms=1500)
                if resp is not None:
                    assert resp.status < 500, f"unexpected status after payload save: {resp.status}"
                assert_not_redirected_to_login(page)
                page.wait_for_timeout(200)
    finally:
        # 安全用例只验证“不执行/不崩溃”，不做保存回滚（避免 required 阻塞导致长等待）。
        # 恢复输入后直接 reload，让页面回到干净状态即可。
        restore_inputs(page, snap)
        try:
            page.reload()
        except Exception:
            pass
        page.wait_for_timeout(300)

    assert dialog_triggered["value"] is False, "XSS payload triggered a dialog"
    page.screenshot(path=f"screenshots/workflow_security_xss_no_dialog.png", full_page=True)

    logger.end(success=True)
