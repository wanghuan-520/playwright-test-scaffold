"""
TestCaseGenerator P2 and security template builders.
"""

from __future__ import annotations

from typing import Dict, List

from generators.page_types import PageInfo
from generators.utils import extract_url_path, get_file_name_from_url, get_page_name_from_url, to_class_name


class TestCaseGeneratorP2SecurityMixin:
    def _p2_py(self, page_info: PageInfo, module: str, page: str, page_key: str, rules: List[Dict]) -> str:
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        file_name = get_file_name_from_url(page_info.url)
        helper_mod = f"tests.{module}.{page}._helpers"

        selectors = [r.get("selector") for r in (rules or []) if r.get("selector")]
        selectors_literal = self._py_literal([s for s in selectors if isinstance(s, str)])

        body = f"""@pytest.mark.P2
@pytest.mark.ui
@allure.feature({class_name!r})
@allure.story("P2")
@allure.title("UI：字段可见性 + 全页截图")
def test_p2_fields_visible(auth_page: Page):
    logger.start()
    page = auth_page
    po = {class_name}Page(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    po.take_screenshot({page_key!r} + "_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature({class_name!r})
@allure.story("P2")
@allure.title("UI：键盘 Tab 可用性")
def test_p2_keyboard_tab_navigation(auth_page: Page):
    logger.start()
    page = auth_page
    po = {class_name}Page(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出字段 selector（Tab 用例跳过）")

    page.click(selectors[0])
    for _ in range(min(5, len(selectors))):
        page.keyboard.press("Tab")

    po.take_screenshot({page_key!r} + "_p2_keyboard_tab")
    logger.end(success=True)
"""
        return self._render_test_module(
            title=f"{class_name} - P2",
            playwright_import="from playwright.sync_api import Page, expect",
            file_name=file_name,
            class_name=class_name,
            helper_mod=helper_mod,
            helper_symbols=["assert_not_redirected_to_login"],
            page_key=page_key,
            logger_suffix="_p2",
            body=body,
        )

    def _security_py(self, page_info: PageInfo, module: str, page: str, page_key: str, rules: List[Dict]) -> str:
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        url_path = extract_url_path(page_info.url)
        helper_mod = f"tests.{module}.{page}._helpers"
        is_protected = "/admin/" in url_path

        selectors = [r.get("selector") for r in (rules or []) if r.get("selector")]
        selectors_literal = self._py_literal([s for s in selectors if isinstance(s, str)])

        body = f"""@pytest.mark.P1
@pytest.mark.security
@allure.feature({class_name!r})
@allure.story("Security")
@allure.title("未登录访问受保护页面应跳转登录")
def test_security_unauth_redirects_to_login(unauth_page: Page):
    logger.start()

    if {str(is_protected)} is False:
        pytest.skip("页面不在 /admin/ 路由下，默认不强制要求鉴权跳转")

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{{base}}{{URL_PATH}}"

    page = unauth_page
    page.goto(url, wait_until="commit", timeout=60000)
    page.wait_for_url(re.compile(r".*(/auth/login|/Account/Login).*"), timeout=60000)

    current = page.url or ""
    assert "/auth/login" in current or "/Account/Login" in current, f"expected redirect to login, got: {{current}}"
    page.screenshot(path=f"screenshots/{page_key}_security_unauth_redirect.png", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature({class_name!r})
@allure.story("Security")
@allure.title("XSS/SQLi payload 不得触发 dialog")
def test_security_xss_payload_no_dialog(auth_page: Page):
    logger.start()

    page = auth_page
    dialog_triggered = {{"value": False}}

    def on_dialog(_):
        dialog_triggered["value"] = True

    page.on("dialog", on_dialog)
    page.goto("https://localhost:3000" + URL_PATH, wait_until="domcontentloaded", timeout=60000)
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出可注入的输入框 selector（拒绝凭猜）")

    snap = snapshot_inputs(page, [{{"selector": s}} for s in selectors])
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
                    assert resp.status < 500, f"unexpected status after payload save: {{resp.status}}"
                assert_not_redirected_to_login(page)
                page.wait_for_timeout(200)
    finally:
        restore_inputs(page, snap)
        try:
            page.reload()
        except Exception:
            pass
        page.wait_for_timeout(300)

    assert dialog_triggered["value"] is False, "XSS payload triggered a dialog"
    page.screenshot(path=f"screenshots/{page_key}_security_xss_no_dialog.png", full_page=True)
    logger.end(success=True)
"""
        return self._render_test_module(
            title=f"{class_name} - Security",
            playwright_import="from playwright.sync_api import Page",
            file_name=file_name,
            class_name=class_name,
            helper_mod=helper_mod,
            helper_symbols=[
                "URL_PATH",
                "assert_not_redirected_to_login",
                "click_save",
                "snapshot_inputs",
                "restore_inputs",
                "wait_mutation_response",
            ],
            page_key=page_key,
            logger_suffix="_security",
            body=body,
            extra_imports=["import re", "from utils.config import ConfigManager"],
        )
