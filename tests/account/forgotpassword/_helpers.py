# ═══════════════════════════════════════════════════════════════
# ForgotPassword Helpers
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳

from __future__ import annotations

from typing import Dict, Optional

from playwright.sync_api import Page, Response


URL_PATH = '/forgot-password'

# ABP 约束常量
ABP_MAX_LEN_EMAIL = 256

FATAL_ERROR_URL_KEYWORDS = [
    "/error",
    "/500",
    "/400",
    "/404",
    "/exception",
]

FATAL_ERROR_TEXT_SNIPPETS = [
    "An unhandled exception occurred",
    "Internal Server Error",
    "Request ID",
    "Stack trace",
    "Exception",
]

ERROR_SELECTORS = [
    ".text-red-500",
    ".text-danger",
    ".invalid-feedback",
    ".error-message",
    ".field-error",
    "[role='alert']",
    ".toast-error",
    ".Toastify__toast--error",
]


def assert_not_redirected_to_login(page: Page) -> None:
    """验证未被重定向到登录页"""
    url = page.url or ""
    # ForgotPassword 是匿名页，不应被重定向
    assert "/login" not in url.lower() or "/forgot-password" in url.lower(), \
        f"redirected to login: {url}"


def click_submit(page: Page) -> None:
    """点击提交按钮"""
    btn = page.locator('button:has-text("Send Reset Link")').first
    btn.click()


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    """等待写操作响应（PUT/POST/PATCH）"""
    try:
        with page.expect_response(
            lambda r: r.request.method in ("PUT", "POST", "PATCH"),
            timeout=timeout_ms
        ) as resp_info:
            pass
        return resp_info.value
    except Exception:
        return None


def get_validation_message(page: Page, selector: str) -> str:
    """读取浏览器原生表单校验文案"""
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage")
        return (msg or "").strip()
    except Exception:
        return ""


def has_any_error_ui(page: Page) -> bool:
    """检查页面是否有错误 UI"""
    for sel in ERROR_SELECTORS:
        try:
            if page.is_visible(sel, timeout=500):
                return True
        except Exception:
            continue
    return False


def detect_fatal_error_page(page: Page) -> str:
    """检测致命错误页"""
    url = (page.url or "").strip().lower()
    for kw in FATAL_ERROR_URL_KEYWORDS:
        if kw and kw in url:
            return f"fatal_error_url_keyword={kw} url={url}"
    
    try:
        title = (page.title() or "").strip()
    except Exception:
        title = ""
    if title and "error" in title.lower():
        return f"fatal_error_title={title!r} url={url}"
    
    for t in FATAL_ERROR_TEXT_SNIPPETS:
        try:
            if page.locator(f"text={t}").first.is_visible(timeout=300):
                return f"fatal_error_text={t!r} url={url}"
        except Exception:
            continue
    
    return ""


def assert_any_validation_evidence(page: Page, selector: str) -> None:
    """验证存在任意校验证据"""
    fatal = detect_fatal_error_page(page)
    if fatal:
        raise AssertionError(f"fatal error page detected: {fatal}")
    
    msg = get_validation_message(page, selector)
    if msg:
        return
    
    if has_any_error_ui(page):
        return
    
    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None and (400 <= resp.status < 500):
        return
    
    raise AssertionError("no validation evidence observed")


def snapshot_inputs(page: Page, selectors: list) -> Dict[str, str]:
    """对输入框做 UI 快照"""
    snap: Dict[str, str] = {}
    for sel in selectors or []:
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
    """恢复输入框值"""
    for sel, val in snap.items():
        try:
            if page.locator(sel).count() == 0:
                continue
            page.fill(sel, val)
        except Exception:
            continue

