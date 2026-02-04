# ═══════════════════════════════════════════════════════════════
# Account/Login - Helpers
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳。

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Dict, Optional

from playwright.sync_api import Page, Response, expect


# ═══════════════════════════════════════════════════════════════
# ABP 常量（与后端保持一致）
# ═══════════════════════════════════════════════════════════════
ABP_MAX_USERNAME_LENGTH = 256
ABP_MAX_EMAIL_LENGTH = 256
ABP_MIN_PASSWORD_LENGTH = 6
ABP_MAX_PASSWORD_LENGTH = 128
ABP_LOCKOUT_MAX_ATTEMPTS = 5
ABP_LOCKOUT_DURATION_MINUTES = 5


URL_PATH = '/Account/Login'
CHANGE_PASSWORD_API_PATH = ''

FATAL_ERROR_URL_KEYWORDS = [
    "/Error",
    "/error",
    "/StatusCode",
    "/statuscode",
    "/500",
    "/400",
    "/404",
]

FATAL_ERROR_TEXT_SNIPPETS = [
    "An unhandled exception occurred",
    "Internal Server Error",
    "Request ID",
    "Stack trace",
    "Exception",
]


# 字段规则（由前后端代码推导；若来源缺失则会降级/skip）
# 更新为实际页面的selector
FIELD_RULES = [{'field': 'email',
  'selector': '#email',
  'required': None,
  'min_len': None,
  'max_len': None,
  'pattern': None,
  'html_type': 'text',
  'sources': [{'kind': 'dynamic', 'path': '(dom)', 'detail': 'Playwright MCP analysis'}]},
 {'field': 'password',
  'selector': '#password',
  'required': None,
  'min_len': None,
  'max_len': None,
  'pattern': None,
  'html_type': 'password',
  'sources': [{'kind': 'dynamic', 'path': '(dom)', 'detail': 'Playwright MCP analysis'}]}]

ERROR_SELECTORS = [
    ".invalid-feedback",
    ".text-danger",
    # ASP.NET / ABP (Razor pages) 常见校验结构
    ".validation-summary-errors",
    "div.validation-summary-errors",
    "span.field-validation-error",
    "[data-valmsg-summary='true']",
    "[data-valmsg-for]",
    ".input-validation-error",
    ".alert.alert-danger",
    ".error-message",
    ".field-error",
    ".toast-error",
    ".Toastify__toast--error",
    "p.text-red-500",
]


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    # Account/Login 本身就是后端登录页（/Account/Login），因此不能把它当作“被重定向”


def click_save(page: Page) -> None:
    # Account/Login 的主按钮是 Login（不是 Save）
    # 使用ABP标准selector
    btn = page.locator("button[name='Action'][type='submit']").first
    from playwright.sync_api import expect
    expect(btn).to_be_visible()
    expect(btn).to_be_enabled()
    btn.click()
    btn = page.locator('role=button[name="Login"]').first
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
    """读取浏览器原生表单校验文案（required/pattern 等）。"""
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage")
        return (msg or "").strip()
    except Exception:
        return ""


def assert_any_validation_evidence(page: Page, selector: str) -> None:
    """
    必填/格式校验的“证据合取”：只要命中任意一种即可。
    - 原生 validationMessage（最稳定）
    - 页面错误 UI（toast/field error）
    - 后端 4xx（实现把 required 放到后端也算通过）
    """
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
    raise AssertionError("no validation evidence observed (validationMessage/error UI/4xx)")


def wait_for_toast(page: Page, timeout_ms: int = 3000) -> None:
    """等待通知区域出现至少一条 toast。"""
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
    assert any((n or "") in text for n in (needles or [])), f"toast text not matched. want any={needles} got={text!r}"


def has_any_error_ui(page: Page) -> bool:
    for sel in ERROR_SELECTORS:
        try:
            if page.is_visible(sel, timeout=500):
                return True
        except Exception:
            continue
    return False


def detect_fatal_error_page(page: Page) -> str:
    """
    检测“致命错误页/异常页”：
    - 这类情况不应被当作“校验证据”，必须直接 fail（否则会掩盖产品崩溃）。
    返回空字符串表示未命中。
    """
    url = (page.url or "").strip()
    for kw in FATAL_ERROR_URL_KEYWORDS:
        if kw and kw in url:
            return f"fatal_error_url_keyword={kw} url={url}"

    # 标题命中（宽松）：只要含 Error 且不在正常 /Account/Login
    try:
        title = (page.title() or "").strip()
    except Exception:
        title = ""
    if title and ("error" in title.lower()) and ("/Account/Login" not in url):
        return f"fatal_error_title={title!r} url={url}"

    # 文本关键字（尽量轻量，不读取整页 HTML）
    for t in FATAL_ERROR_TEXT_SNIPPETS:
        try:
            if page.locator(f"text={t}").first.is_visible(timeout=300):
                return f"fatal_error_text={t!r} url={url} title={title!r}"
        except Exception:
            continue

    return ""


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


# ═══════════════════════════════════════════════════════════════
# 唯一标识符生成
# ═══════════════════════════════════════════════════════════════

def unique_suffix(xdist_worker_id: str = "") -> str:
    """
    生成唯一后缀，用于测试数据隔离。
    格式: {worker}_{timestamp}_{uuid6}
    """
    worker = xdist_worker_id or "master"
    ts = int(time.time() * 1000) % 100000
    uid = uuid.uuid4().hex[:6]
    return f"{worker}_{ts}_{uid}"


def get_first_available_account() -> Optional[dict]:
    """
    获取账号池中第一个可用账号
    
    Returns:
        账号字典 或 None（无可用账号）
    """
    pool_path = os.path.join(
        os.path.dirname(__file__),
        "../../../test-data/test_account_pool.json"
    )
    try:
        with open(pool_path, "r") as f:
            data = json.load(f)
        pool = data.get("test_account_pool", [])
        for acc in pool:
            if not acc.get("is_locked", False):
                return acc
    except Exception:
        pass
    return None


def get_boundary_account(account_type: str, boundary: str) -> Optional[dict]:
    """
    从 boundary_accounts.json 加载指定类型的边界账号
    
    Args:
        account_type: 账号类型 (username_boundary, password_boundary, email_boundary, special_account)
        boundary: 边界标识 (len_255, len_256, len_127, len_128, lockout_test)
        
    Returns:
        账号字典 或 None（未找到）
    """
    boundary_path = os.path.join(
        os.path.dirname(__file__),
        "../../../test-data/boundary_accounts.json"
    )
    try:
        with open(boundary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for acc in data.get("boundary_accounts", []):
            if acc.get("type") == account_type and acc.get("boundary") == boundary:
                return acc
    except Exception as e:
        print(f"⚠️ 加载边界账号失败: {e}")
    return None


def ensure_login_page(page: Page, po) -> None:
    """
    确保当前在登录页面
    
    如果不在登录页或输入框不可见，则重新导航
    """
    try:
        if page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT).count() > 0:
            return
    except Exception:
        pass
    try:
        po.navigate()
        page.wait_for_timeout(200)
    except Exception:
        pass
    assert_not_redirected_to_login(page)
