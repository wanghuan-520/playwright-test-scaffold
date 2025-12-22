# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword - Security
# Generated: 2025-12-22 13:06:47
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Browser, Page

from utils.config import ConfigManager
from tests.admin.profile_change_password._helpers import (
    URL_PATH,
    assert_not_redirected_to_login,
    click_save,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('profile_change_password_settings' + "_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature('AdminProfileChangePassword')
@allure.story("Security")
@allure.title("未登录访问受保护页面应跳转登录")
def test_security_unauth_redirects_to_login(browser: Browser):
    logger.start()

    if True is False:
        pytest.skip("页面不在 /admin/ 路由下，默认不强制要求鉴权跳转")

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{base}{URL_PATH}"

    ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)

    current = page.url or ""
    assert "/auth/login" in current or "/Account/Login" in current, f"expected redirect to login, got: {current}"
    page.screenshot(path=f"screenshots/profile_change_password_settings_security_unauth_redirect.png", full_page=True)
    ctx.close()

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature('AdminProfileChangePassword')
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

    selectors = ["[name='confirmNewPassword']", "[name='currentPassword']", "[name='newPassword']"]
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
        restore_inputs(page, snap)
        click_save(page)
        _ = wait_mutation_response(page, timeout_ms=60000)

    assert dialog_triggered["value"] is False, "XSS payload triggered a dialog"
    page.screenshot(path=f"screenshots/profile_change_password_settings_security_xss_no_dialog.png", full_page=True)

    logger.end(success=True)
