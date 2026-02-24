"""
TestCaseGenerator shared helper templates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List
import pprint

from generators.page_types import PageInfo
from generators.utils import extract_url_path


class TestCaseGeneratorHelpersMixin:
    def _helpers_py(self, page_info: PageInfo, rules: List[Dict], *, is_change_password: bool) -> str:
        url_path = extract_url_path(page_info.url)
        rules_literal = self._py_literal(rules)
        change_password_api = "/api/account/my-profile/change-password"
        change_password_api_line = (
            f"CHANGE_PASSWORD_API_PATH = {change_password_api!r}\n" if is_change_password else "CHANGE_PASSWORD_API_PATH = ''\n"
        )
        return f"""# ═══════════════════════════════════════════════════════════════
# Helpers
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳。

from __future__ import annotations

from typing import Dict, Optional

from playwright.sync_api import Page, Response, expect


URL_PATH = {url_path!r}
{change_password_api_line}

# 字段规则（由前后端代码推导；若来源缺失则会降级/skip）
FIELD_RULES = {rules_literal}

ERROR_SELECTORS = [
    ".invalid-feedback",
    ".text-danger",
    ".error-message",
    ".field-error",
    ".toast-error",
    ".Toastify__toast--error",
    "p.text-red-500",
]


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {{url}}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {{url}}"


def click_save(page: Page) -> None:
    # 尽量用文案锁定，避免命中同 class 的非目标按钮
    btn = page.locator("button:has-text('Save')").first
    expect(btn).to_be_visible()
    expect(btn).to_be_enabled()
    btn.click()


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    # 等待任意写操作响应（PUT/POST/PATCH）。存在则返回，否则返回 None。
    try:
        with page.expect_response(lambda r: (r.request.method in ("PUT", "POST", "PATCH")), timeout=timeout_ms) as resp_info:
            pass
        return resp_info.value
    except Exception:
        return None


def wait_response_by_url_substring(page: Page, url_substring: str, *, method: str = "POST", timeout_ms: int = 60000) -> Response:
    with page.expect_response(
        lambda r: (r.request.method == method) and (url_substring in (r.url or "")),
        timeout=timeout_ms,
    ) as resp_info:
        pass
    return resp_info.value


def get_validation_message(page: Page, selector: str) -> str:
    \"\"\"读取浏览器原生表单校验文案（required/pattern 等）。\"\"\"
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage")
        return (msg or "").strip()
    except Exception:
        return ""


def assert_any_validation_evidence(page: Page, selector: str) -> None:
    \"\"\"
    必填/格式校验的“证据合取”：只要命中任意一种即可。
    - 原生 validationMessage（最稳定）
    - 页面错误 UI（toast/field error）
    - 后端 4xx（实现把 required 放到后端也算通过）
    \"\"\"
    msg = get_validation_message(page, selector)
    if msg:
        return
    if has_any_error_ui(page):
        return
    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None and (400 <= resp.status < 500):
        return
    raise AssertionError("no validation evidence observed (validationMessage/error UI/4xx)")


def wait_for_toast(page: Page, timeout_ms: int = 3000) -> None:
    \"\"\"等待通知区域出现至少一条 toast。\"\"\"
    regions = page.get_by_role("region", name="Notifications (F8)")
    picked = None
    try:
        n = regions.count()
    except Exception:
        n = 0
    for i in range(max(n, 1)):
        r = regions.nth(i) if n > 0 else regions
        try:
            if r.is_visible(timeout=200):
                picked = r
                break
        except Exception:
            continue
    region = picked or regions.first
    item = region.get_by_role("listitem").first
    expect(item).to_be_visible(timeout=timeout_ms)


def get_toast_text(page: Page) -> str:
    regions = page.get_by_role("region", name="Notifications (F8)")
    try:
        n = regions.count()
    except Exception:
        n = 0
    if n == 0:
        return ""
    for i in range(n):
        r = regions.nth(i)
        try:
            if not r.is_visible(timeout=200):
                continue
            return (r.inner_text(timeout=1000) or "").strip()
        except Exception:
            continue
    try:
        return (regions.first.inner_text(timeout=1000) or "").strip()
    except Exception:
        return ""


def assert_toast_contains_any(page: Page, needles: list[str]) -> None:
    wait_for_toast(page, timeout_ms=3000)
    text = get_toast_text(page)
    assert any((n or "") in text for n in (needles or [])), f"toast text not matched. want any={{needles}} got={{text!r}}"


def has_any_error_ui(page: Page) -> bool:
    for sel in ERROR_SELECTORS:
        try:
            if page.is_visible(sel, timeout=500):
                return True
        except Exception:
            continue
    return False


def snapshot_inputs(page: Page, rules: list[dict]) -> Dict[str, str]:
    # 按规则列表对输入框做 UI 快照（selector -> value）。
    snap: Dict[str, str] = dict()
    for r in rules:
        sel = r.get("selector") or ""
        if not sel:
            continue
        if page.locator(sel).count() == 0:
            continue
        try:
            snap[sel] = page.input_value(sel)
        except Exception:
            continue
    return snap


def restore_inputs(page: Page, snap: Dict[str, str]) -> None:
    # UI 级恢复（不依赖后端特定 API）。
    for sel, val in snap.items():
        try:
            if page.locator(sel).count() == 0:
                continue
            page.fill(sel, val)
        except Exception:
            continue
"""

    def _render_sources_comment(self, r: Dict) -> str:
        srcs = r.get("sources") or []
        if not srcs:
            return "# Source: (missing)"
        lines = []
        for s in srcs:
            kind = s.get("kind")
            path = s.get("path")
            detail = s.get("detail") or ""
            lines.append(f"# Source: {kind} {path} {detail}".rstrip())
        return "\n".join(lines)

    def _py_literal(self, obj) -> str:
        return pprint.pformat(obj, width=120, sort_dicts=False)

    def _render_banner(self, title: str) -> str:
        return "\n".join(
            [
                "# ═══════════════════════════════════════════════════════════════",
                f"# {title}",
                f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "# ═══════════════════════════════════════════════════════════════",
            ]
        )

    def _render_test_module(
        self,
        *,
        title: str,
        playwright_import: str,
        file_name: str,
        class_name: str,
        helper_mod: str,
        helper_symbols: List[str],
        page_key: str,
        logger_suffix: str,
        body: str,
        extra_imports: List[str] | None = None,
    ) -> str:
        helper_import_block = ",\n    ".join(helper_symbols)
        imports = [
            "import allure",
            "import pytest",
            playwright_import,
            *(extra_imports or []),
            "",
            f"from pages.{file_name}_page import {class_name}Page",
            f"from {helper_mod} import (",
            f"    {helper_import_block}",
            ")",
            "from utils.logger import TestLogger",
            "",
            f"logger = TestLogger({page_key!r} + {logger_suffix!r})",
            "",
        ]
        return f"""{self._render_banner(title)}

{chr(10).join(imports)}
{body.rstrip()}
"""
