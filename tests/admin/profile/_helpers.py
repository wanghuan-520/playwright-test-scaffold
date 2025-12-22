# ═══════════════════════════════════════════════════════════════
# Profile / Personal Settings - Test Helpers
# ═══════════════════════════════════════════════════════════════
"""
仅服务于 Profile -> Personal Settings 的测试 helper。

原则：
- 关键步骤必须截图（Allure 规范）
- 用例必须可重复执行：任何写操作都要回滚
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
import os

import allure
from playwright.sync_api import Page

from pages.personal_settings_page import PersonalSettingsPage
from utils.config import ConfigManager


# ABP / OpenAPI 规则缓存（避免每条用例都打 swagger）
_ABP_RULES_CACHE: Optional[Dict] = None

# FAST=1：极限提速开关（用于本地/CI 快速回归）
# - 跳过“每步截图/等 toast 消失/等成功 toast”这类高开销动作
# - 让“1 分钟级别跑完”在工程上变得可能（配合并发）
FAST_MODE: bool = os.getenv("FAST", "0") == "1"

# 截图策略（加速开关）
# - FULL_PAGE_SHOT=1：整页截图（最可检证，但慢）
# - 默认：视口截图（更快，通常足够覆盖输入区 + toast 区）
FULL_PAGE_SHOT: bool = os.getenv("FULL_PAGE_SHOT", "0") == "1"

# Allure 展示“降噪”开关：
# - 默认只展示前端证据（截图/输入框 validationMessage 等）
# - 后端接口响应/状态码/回滚诊断等仅在失败时才需要；若想强制展示，用 ALLURE_SHOW_BACKEND=1
ALLURE_SHOW_BACKEND: bool = os.getenv("ALLURE_SHOW_BACKEND", "0") == "1"
# 元信息（规则来源/ABP openapi 规则等）默认不展示；需要审计时再打开
ALLURE_SHOW_META: bool = os.getenv("ALLURE_SHOW_META", "0") == "1"
# debug 噪音（例如 toast missing 说明）默认不展示
ALLURE_SHOW_DEBUG: bool = os.getenv("ALLURE_SHOW_DEBUG", "0") == "1"


def attach_backend_text(name: str, text: str) -> None:
    """后端/诊断类附件：默认不展示，避免 Allure 过度噪音。"""
    if not ALLURE_SHOW_BACKEND:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_backend_json(name: str, text: str) -> None:
    """后端/诊断类附件（JSON 文本）：默认不展示。"""
    if not ALLURE_SHOW_BACKEND:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.JSON)


def attach_meta_text(name: str, text: str) -> None:
    """元信息附件：默认不展示。"""
    if not ALLURE_SHOW_META:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


@dataclass(frozen=True)
class ProfileFieldRules:
    # 来自前端源码：src/components/profile/ProfileSettings.tsx
    USERNAME_MAX: int = 256
    NAME_MAX: int = 64
    SURNAME_MAX: int = 64
    EMAIL_MAX: int = 256
    PHONE_MAX: int = 16


class AbpUserConsts:
    """
    ABP Identity 默认约束（对齐 aevatar_station 的用例写法）。

    说明：
    - 这里把“规则”显式写死，是为了让用例可读、可审计（不依赖 swagger 是否暴露全部规则）
    - 若项目自定义了 Identity 规则，应以真实后端行为为准（可用 ABP probe 用例验证）
    """

    # 长度
    MaxUserNameLength = 256
    MaxNameLength = 64
    MaxSurnameLength = 64
    MaxEmailLength = 256
    MaxPhoneNumberLength = 16

    MinUserNameLength = 1
    MinEmailLength = 3

    # 格式（ABP Identity 默认）
    UserNamePattern = r"^[a-zA-Z0-9_.@-]+$"
    EmailPattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def now_suffix() -> str:
    return datetime.now().strftime("%H%M%S")


def make_string(n: int, ch: str = "A") -> str:
    return (ch * max(n, 0))[: max(n, 0)]


def make_email_with_length(total_len: int, suffix: str = "") -> str:
    """
    生成一个尽量满足 HTML5 email 的长邮箱字符串。
    total_len: 目标总长度（可能略有偏差，但会 >= 目标值的主要边界）
    """
    # 基础结构：<local>@<domain>.com
    # 其中 domain 固定，local 填充以达到长度
    domain = "example.com"
    fixed = f"@{domain}"
    local_len = max(1, total_len - len(fixed))
    # 需要唯一性（避免 email unique 约束）：把 suffix 塞进 local，并用 a 补齐长度
    suf = (suffix or "").strip()
    if suf:
        # 只允许安全字符，避免破坏 email 格式
        suf = "".join([c for c in suf if c.isalnum()])[: max(1, min(12, local_len))]
    base = suf if suf else ""
    pad_len = max(0, local_len - len(base))
    local = (base + ("a" * pad_len))[:local_len]
    return f"{local}{fixed}"


def get_page(auth_page: Page) -> PersonalSettingsPage:
    return PersonalSettingsPage(auth_page)


def check_success_toast(page_obj: PersonalSettingsPage) -> bool:
    """多选择器兜底检测 success toast（用于截图命名/诊断，不作为唯一断言）。"""
    selectors = [
        f"text={page_obj.SUCCESS_TOAST_TEXT}",
        "text=successfully",
        "text=Success",
        "text=success",
        ".text-success",
        ".alert-success",
        ".toast-success",
        ".Toastify__toast--success",
        "[class*='toast'][class*='success']",
        "[class*='Toast'][class*='success']",
    ]
    for sel in selectors:
        try:
            if page_obj.is_visible(sel, timeout=1500):
                return True
        except Exception:
            continue
    return False


def step_shot(page_obj: PersonalSettingsPage, name: str) -> None:
    """强制：关键步骤内截图（full_page=True）"""
    if FAST_MODE:
        return
    page_obj.take_screenshot(name, full_page=FULL_PAGE_SHOT)


def debug_shot(page_obj: PersonalSettingsPage, name: str) -> None:
    """
    Debug 截图：默认不展示（避免 Allure 报告出现 baseline/teardown 过程噪音）。
    - 只在 ALLURE_SHOW_DEBUG=1 时启用
    """
    if FAST_MODE:
        return
    if not ALLURE_SHOW_DEBUG:
        return
    page_obj.take_screenshot(name, full_page=FULL_PAGE_SHOT)


def step_shot_after_success_toast(page_obj: PersonalSettingsPage, name: str, timeout_ms: int = 8000) -> None:
    """
    用于“保存成功”的截图：先等成功提示出现，再截图。

    解决的问题：
    - 网络已返回 OK，但 toast 动画尚未渲染 -> 截图看不到 Success
    """
    if FAST_MODE:
        return
    timeout_ms = int(os.getenv("SUCCESS_TOAST_WAIT_MS", str(timeout_ms)) or timeout_ms)
    # toast 属于 UI 侧证据：尽力等，但不能把“截图证据点”变成炸点
    try:
        page_obj.wait_for_save_success(timeout_ms=timeout_ms)
    except Exception as e:
        # 默认不在 Allure 上刷“debug 噪音”；需要时用 ALLURE_SHOW_DEBUG=1 打开
        if ALLURE_SHOW_DEBUG:
            allure.attach(
                f"success toast not visible within {timeout_ms}ms: {type(e).__name__}: {e}",
                name=f"{name}_toast_missing",
                attachment_type=allure.attachment_type.TEXT,
            )
    page_obj.take_screenshot(name, full_page=FULL_PAGE_SHOT)


def settle_toasts(page_obj: PersonalSettingsPage, timeout_ms: int = 8000) -> None:
    """
    等待上一条 toast 消失，避免“错误 toast + 成功 toast 同框”的截图污染。
    """
    if FAST_MODE:
        return
    timeout_ms = int(os.getenv("TOAST_SETTLE_MS", str(timeout_ms)) or timeout_ms)
    page_obj.wait_for_toasts_to_disappear(timeout_ms=timeout_ms)


def assert_no_dialog(page: Page, dialog_seen: Dict[str, Optional[str]]) -> None:
    assert dialog_seen.get("type") is None, f"不应弹出 dialog，但捕获到: {dialog_seen}"


def attach_rule_source_note() -> None:
    attach_meta_text(
        name="rule_source",
        text="规则来源：前端 src/components/profile/ProfileSettings.tsx (react-hook-form required/maxLength/pattern)。",
    )


def _extract_openapi_profile_rules(swagger: Dict) -> Dict[str, Dict]:
    """
    从 OpenAPI/Swagger JSON 中抽取 profileUpdate DTO 的字段约束（required/maxLength/minLength/pattern）。
    尽量兼容 OpenAPI3 / Swagger2。
    """
    # OpenAPI3: paths -> requestBody -> content -> schema -> $ref
    paths = swagger.get("paths") or {}
    path_item = paths.get("/api/account/my-profile") or {}
    put = path_item.get("put") or {}

    ref = None
    try:
        rb = put.get("requestBody") or {}
        content = rb.get("content") or {}
        app_json = content.get("application/json") or next(iter(content.values()), {})
        schema = (app_json or {}).get("schema") or {}
        ref = schema.get("$ref")
    except Exception:
        ref = None

    # Swagger2: parameters -> in: body -> schema -> $ref
    if not ref:
        try:
            for p in (put.get("parameters") or []):
                if (p or {}).get("in") == "body":
                    schema = (p or {}).get("schema") or {}
                    ref = schema.get("$ref")
                    break
        except Exception:
            ref = None

    def _resolve_ref(r: str) -> Dict:
        if not r or not isinstance(r, str):
            return {}
        name = r.split("/")[-1]
        comp = (swagger.get("components") or {}).get("schemas") or {}
        defs = swagger.get("definitions") or {}
        return comp.get(name) or defs.get(name) or {}

    schema = _resolve_ref(ref) if ref else {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])

    rules: Dict[str, Dict] = {}
    for k, v in props.items():
        if not isinstance(v, dict):
            continue
        rules[k] = {
            "required": k in required,
            "maxLength": v.get("maxLength"),
            "minLength": v.get("minLength"),
            "pattern": v.get("pattern"),
            "type": v.get("type"),
        }
    return rules


def fetch_abp_profile_rules(auth_page: Page) -> Dict[str, Dict]:
    """
    通过 ABP 后端提供的 OpenAPI/Swagger 拉取 profileUpdate DTO 规则。
    如果 swagger 不可用，返回空 dict（但不会阻塞测试）。
    """
    global _ABP_RULES_CACHE
    if _ABP_RULES_CACHE is not None:
        return _ABP_RULES_CACHE

    cfg = ConfigManager()
    backend = (cfg.get_service_url("backend") or "").rstrip("/")
    frontend = (cfg.get_service_url("frontend") or "").rstrip("/")

    candidates = [
        f"{backend}/swagger/v1/swagger.json",
        f"{backend}/swagger/v1/swagger.json?format=json",
        f"{frontend}/swagger/v1/swagger.json",
        f"{frontend}/swagger/v1/swagger.json?format=json",
    ]

    api = auth_page.context.request
    for url in candidates:
        try:
            resp = api.get(url)
            if not resp.ok:
                continue
            data = resp.json()
            rules = _extract_openapi_profile_rules(data or {})
            _ABP_RULES_CACHE = rules
            return rules
        except Exception:
            continue

    _ABP_RULES_CACHE = {}
    return _ABP_RULES_CACHE


def attach_abp_profile_rules(auth_page: Page) -> None:
    """把 ABP(OpenAPI) 规则作为附件挂到 Allure，便于审计测试依据。"""
    if not ALLURE_SHOW_META:
        return
    rules = fetch_abp_profile_rules(auth_page)
    allure.attach(
        str(rules),
        name="abp_profile_rules(openapi)",
        attachment_type=allure.attachment_type.TEXT,
    )


def abp_profile_put_should_reject(auth_page: Page, baseline: Dict[str, str], patch: Dict[str, str]) -> None:
    """
    直连 /api/account/my-profile，断言 ABP 后端拒绝该 patch（4xx）。
    用于“前后端一致性”验证：前端拦截只是第一道门，后端必须同样拒绝。
    """
    import json as _json

    cfg = ConfigManager()
    backend = (cfg.get_service_url("backend") or "").rstrip("/")
    frontend = (cfg.get_service_url("frontend") or "").rstrip("/")
    bases = [b for b in [backend, frontend] if b]

    def _xsrf_headers() -> Dict[str, str]:
        token = ""
        try:
            for c in (auth_page.context.cookies() or []):
                if (c or {}).get("name") == "XSRF-TOKEN":
                    token = (c or {}).get("value") or ""
                    break
        except Exception:
            token = ""
        if not token:
            return {}
        return {
            "X-XSRF-TOKEN": token,
            "x-xsrf-token": token,
            "X-Requested-With": "XMLHttpRequest",
        }

    payload = dict(baseline)
    payload.update(patch)

    api = auth_page.context.request
    resp = None
    body_text = ""
    last_exc: Optional[Exception] = None
    for base in bases:
        url = f"{base}/api/account/my-profile"
        headers = {"content-type": "application/json", "accept": "application/json"}
        if base == backend:
            headers.update(_xsrf_headers())
        try:
            resp = api.put(url, data=_json.dumps(payload), headers=headers)
            try:
                body_text = resp.text() or ""
            except Exception:
                body_text = ""
            # backend 没带对 token 常见 400；兜底走 frontend 再试
            if base == backend and resp.status == 400:
                continue
            break
        except Exception as e:
            last_exc = e
            continue

    if resp is None:
        allure.attach(str(last_exc), name="abp_put_exception", attachment_type=allure.attachment_type.TEXT)
        raise last_exc or RuntimeError("abp_profile_put_should_reject failed without response")

    # 仅在失败/审计需要时再展示后端响应（默认不刷到报告里）
    if not (400 <= resp.status < 500):
        # 失败必须可诊断：强制挂出必要信息
        allure.attach(str(resp.status), name="abp_put_status", attachment_type=allure.attachment_type.TEXT)
        if body_text:
            allure.attach(body_text, name="abp_put_body", attachment_type=allure.attachment_type.JSON)
        assert 400 <= resp.status < 500, f"expected ABP to reject invalid input (4xx), got {resp.status}"

    # 尽量结构化解析；失败则退回到 body 文本兜底
    ves = PersonalSettingsPage(auth_page).get_abp_validation_errors(resp)
    if ves:
        attach_backend_text("abp_validationErrors", str(ves))
        return

    # fallback：至少确保 body 有内容（否则报告不可诊断）
    if not body_text.strip():
        allure.attach(str(resp.status), name="abp_put_status", attachment_type=allure.attachment_type.TEXT)
        assert body_text.strip(), "ABP rejected request but response body is empty (cannot diagnose validation reason)"


def abp_profile_put(auth_page: Page, baseline: Dict[str, str], patch: Dict[str, str]) -> Dict:
    """
    直连 /api/account/my-profile，返回 ABP 响应信息（不做断言）。

    用途：
    - 规则探测（discover）：后端到底拒绝哪些输入
    - 一致性用例：如果后端拒绝，则前端必须拦截（不能放行到后端才报错）
    """
    import json as _json

    cfg = ConfigManager()
    backend = (cfg.get_service_url("backend") or "").rstrip("/")
    frontend = (cfg.get_service_url("frontend") or "").rstrip("/")
    bases = [b for b in [backend, frontend] if b]

    def _xsrf_headers() -> Dict[str, str]:
        token = ""
        try:
            for c in (auth_page.context.cookies() or []):
                if (c or {}).get("name") == "XSRF-TOKEN":
                    token = (c or {}).get("value") or ""
                    break
        except Exception:
            token = ""
        if not token:
            return {}
        return {
            "X-XSRF-TOKEN": token,
            "x-xsrf-token": token,
            "X-Requested-With": "XMLHttpRequest",
        }

    payload = dict(baseline)
    payload.update(patch)

    api = auth_page.context.request
    resp = None
    body_text = ""
    last_exc: Optional[Exception] = None
    for base in bases:
        url = f"{base}/api/account/my-profile"
        headers = {"content-type": "application/json", "accept": "application/json"}
        if base == backend:
            headers.update(_xsrf_headers())
        try:
            resp = api.put(url, data=_json.dumps(payload), headers=headers)
            try:
                body_text = resp.text() or ""
            except Exception:
                body_text = ""
            if base == backend and resp.status == 400:
                continue
            break
        except Exception as e:
            last_exc = e
            continue

    if resp is None:
        return {
            "status": None,
            "ok": False,
            "validationErrors": [],
            "body": str(last_exc or "no response"),
            "patch": patch,
        }

    ves = PersonalSettingsPage(auth_page).get_abp_validation_errors(resp)

    return {
        "status": resp.status,
        "ok": bool(resp.ok),
        "validationErrors": ves,
        "body": body_text,
        "patch": patch,
    }

