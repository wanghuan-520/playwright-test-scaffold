# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# Helpers
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳。

from __future__ import annotations

import re
import time
import uuid
from typing import Dict, Optional

import allure
from playwright.sync_api import Page, Response, expect


URL_PATH = '/Account/Register'
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
    "API Error",
    "API Error 500",
]


# 字段规则（根据 docs/requirements/account-register-field-requirements.md）
# 前端字段：UserName、Email、Password
FIELD_RULES = [
    {
        'field': 'userName',
        'selector': '#userName',
        'required': True,
        'min_len': 1,
        'max_len': 256,
        'pattern': r'^[a-zA-Z0-9._-]+$',  # 字母、数字、下划线、连字符、点号
        'html_type': 'text',
        'sources': [{'kind': 'requirements', 'path': 'docs/requirements/account-register-field-requirements.md'}]
    },
    {
        'field': 'email',
        'selector': '#email',
        'required': True,
        'min_len': 1,
        'max_len': 256,
        'pattern': None,  # 邮箱格式由 HTML5 type="email" 验证
        'html_type': 'email',
        'sources': [{'kind': 'requirements', 'path': 'docs/requirements/account-register-field-requirements.md'}]
    },
    {
        'field': 'password',
        'selector': '#password',
        'required': True,
        'min_len': 6,
        'max_len': None,  # 无最大长度限制（建议不超过128）
        'pattern': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{6,}$',
        'html_type': 'password',
        'sources': [{'kind': 'requirements', 'path': 'docs/requirements/account-register-field-requirements.md'}]
    }
]

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
    # React / Tailwind 风格的错误提示
    ".text-neon-red",
    ".bg-neon-red\\/10",
    "[class*='text-red']",
    "[class*='bg-red']",
]


def ensure_register_page(page: Page, po) -> None:
    """确保当前在注册页面，如果不在则导航过去"""
    try:
        selector = getattr(po, 'USERNAME_INPUT', None)
        if selector and page.locator(selector).count() > 0:
            return
    except Exception:
        pass
    po.navigate()
    page.wait_for_timeout(200)


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    # /register 是匿名页；允许停留在 /register 路由


def click_save(page: Page) -> None:
    # Register 的主按钮是 "Create Account"（不是 "Register"）
    # 优先使用Page Object的selector（button[type="submit"]），如果不存在则使用role selector
    # 注意：按钮在表单未完整时可能disabled，需要使用JavaScript强制点击
    
    # 方法1: 使用Page Object的selector（button[type="submit"]）
    submit_btn = page.locator('button[type="submit"]')
    if submit_btn.count() > 0:
        try:
            # 先尝试正常点击（如果按钮enabled）
            if submit_btn.is_visible():
                submit_btn.click(timeout=2000)
                return
        except Exception:
            # 如果正常点击失败（按钮disabled），使用JavaScript强制点击
            # 这对于测试场景是合理的：测试"即使字段为空，提交也不应该导致500错误"
            page.evaluate("""() => {
                const btn = document.querySelector('button[type="submit"]');
                if (btn) {
                    btn.click();
                }
            }""")
            return
    
    # 方法2: 尝试查找包含"Create Account"文本的按钮
    create_btn = page.get_by_role("button", name=re.compile(r"Create Account", re.IGNORECASE)).first
    if create_btn.count() > 0:
        try:
            expect(create_btn).to_be_visible()
            create_btn.click()
            return
        except Exception:
            # 如果点击失败，使用JavaScript强制点击
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.textContent && b.textContent.toLowerCase().includes('create account')
                );
                if (btn) {
                    btn.click();
                }
            }""")
            return
    
    # 方法3: 回退到查找包含"Register"文本的按钮（兼容旧代码）
    register_btn = page.get_by_role("button", name=re.compile(r"Register", re.IGNORECASE)).first
    if register_btn.count() > 0:
        try:
            expect(register_btn).to_be_visible()
            register_btn.click()
            return
        except Exception:
            # 如果点击失败，使用JavaScript强制点击
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.textContent && b.textContent.toLowerCase().includes('register')
                );
                if (btn) {
                    btn.click();
                }
            }""")
            return
    
    # 方法4: 最后尝试ABP标准selector
    abp_btn = page.locator("button[name='Action'][type='submit']")
    if abp_btn.count() > 0:
        try:
            abp_btn.click()
            return
        except Exception:
            # 如果点击失败，使用JavaScript强制点击
            page.evaluate("""() => {
                const btn = document.querySelector("button[name='Action'][type='submit']");
                if (btn) {
                    btn.click();
                }
            }""")
            return
    
    raise AssertionError("无法找到注册提交按钮（Create Account/Register）")


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


def get_error_text(page: Page) -> str:
    """获取页面上所有错误信息的文本"""
    texts = []
    for sel in ERROR_SELECTORS:
        try:
            elements = page.locator(sel).all()
            for el in elements:
                if el.is_visible():
                    text = el.text_content() or ""
                    if text.strip():
                        texts.append(text.strip())
        except Exception:
            continue
    return " ".join(texts)


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

    # 标题命中（宽松）：只要含 Error 且不在正常 /Account/Register
    try:
        title = (page.title() or "").strip()
    except Exception:
        title = ""
    if title and ("error" in title.lower()) and ("/Account/Register" not in url):
        return f"fatal_error_title={title!r} url={url}"

    # 文本关键字（尽量轻量，不读取整页 HTML）
    for t in FATAL_ERROR_TEXT_SNIPPETS:
        try:
            if page.locator(f"text={t}").first.is_visible(timeout=300):
                return f"fatal_error_text={t!r} url={url} title={title!r}"
        except Exception:
            continue
    
    # 额外检查：API Error 500（可能在页面文本中）
    try:
        page_text = page.evaluate("() => document.body.innerText") if hasattr(page, 'evaluate') else ""
        if "API Error" in str(page_text) and "500" in str(page_text):
            return f"fatal_error_api_500 url={url} title={title!r}"
    except Exception:
        pass

    return ""


def try_get_submit_response(page: Page, *, timeout_ms: int):
    """尝试获取提交响应"""
    try:
        return wait_response_by_url_substring(page, "/api/account/register", timeout_ms=timeout_ms)
    except Exception:
        return wait_mutation_response(page, timeout_ms=timeout_ms)


def assert_no_fatal_error(page: Page, *, case_name: str) -> None:
    """断言没有致命错误页"""
    fatal = detect_fatal_error_page(page)
    if fatal:
        allure.attach(fatal, name=f"{case_name}_fatal_error_page", attachment_type=allure.attachment_type.TEXT)
        raise AssertionError(f"[{case_name}] fatal error page detected: {fatal}")


def snapshot_inputs(page: Page, rules) -> Dict[str, str]:
    """
    按“输入规则列表”对输入框做 UI 快照（selector -> value）。

    兼容两种调用方式（历史/生成器混用时常见）：
    - rules: [{"selector": "<css/role selector>"}, ...]
    - rules: ["<css/role selector>", ...]
    """
    snap: Dict[str, str] = dict()
    for r in (rules or []):
        sel = ""
        if isinstance(r, dict):
            sel = str(r.get("selector") or "").strip()
        elif isinstance(r, str):
            sel = r.strip()
        else:
            continue

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
# ABP 约束常量（来自 ABP Identity 源码）
# ═══════════════════════════════════════════════════════════════
# IdentityUserConsts.MaxUserNameLength = 256
# IdentityUserConsts.MaxPasswordLength = 128
# IdentityUserConsts.MaxEmailLength = 256
ABP_MAX_LEN_COMMON = 256  # username/email 通用最大长度
ABP_PASSWORD_MAX = 128    # password 最大长度（ABP Identity 默认）


# ═══════════════════════════════════════════════════════════════
# 通用辅助函数（从各测试文件提取）
# ═══════════════════════════════════════════════════════════════

def unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    """生成唯一后缀，用于避免测试数据冲突"""
    import time
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


def ensure_register_page(page: Page, po) -> None:
    """
    复用 Register 页，降低每个参数化 case 都 Page.goto 的压力。
    - 若 submit 导致跳转/错误页，则重新导航
    """
    try:
        selector = getattr(po, 'USERNAME_INPUT', None)
        if selector and page.locator(selector).count() > 0:
            return
    except Exception:
        pass
    po.navigate()
    page.wait_for_timeout(200)
