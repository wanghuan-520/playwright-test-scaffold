# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# Helpers
# Generated: 2025-12-22 13:06:47
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳。

from __future__ import annotations

from typing import Dict, Optional

from playwright.sync_api import Page, Response, expect


URL_PATH = '/admin/profile/change-password'

# 字段规则（由前后端代码推导；若来源缺失则会降级/skip）
FIELD_RULES = [{'field': 'confirmNewPassword',
  'selector': "[name='confirmNewPassword']",
  'required': None,
  'min_len': None,
  'max_len': None,
  'pattern': None,
  'html_type': 'password',
  'sources': [{'kind': 'dynamic', 'path': '(dom)', 'detail': 'PageAnalyzer element'}]},
 {'field': 'currentPassword',
  'selector': "[name='currentPassword']",
  'required': True,
  'min_len': None,
  'max_len': None,
  'pattern': None,
  'html_type': 'password',
  'sources': [{'kind': 'dynamic', 'path': '(dom)', 'detail': 'PageAnalyzer element'}]},
 {'field': 'newPassword',
  'selector': "[name='newPassword']",
  'required': None,
  'min_len': None,
  'max_len': None,
  'pattern': None,
  'html_type': 'password',
  'sources': [{'kind': 'dynamic', 'path': '(dom)', 'detail': 'PageAnalyzer element'}]}]

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
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {url}"


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
