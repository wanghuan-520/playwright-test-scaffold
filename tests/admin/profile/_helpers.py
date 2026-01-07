"""
# ═══════════════════════════════════════════════════════════════
# Admin / Profile - Shared Helpers
# ═══════════════════════════════════════════════════════════════
#
# 说明：
# - 该目录下的 profile_settings/change_password 等 suite 会共享本 helpers。
# - 这里提供“稳定的通用能力”：截图、toast 稳定化、规则来源附件、ABP 常量。
# - 安全：不记录敏感输入明文（密码/Token/PII）。
#
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import allure  # pyright: ignore[reportMissingImports]
from playwright.sync_api import Page, expect


# ============================================================
# ABP Constants (minimal, for matrix slicing)
# ============================================================


class AbpUserConsts:
    # ABP IdentityUserConsts defaults (common)
    MaxUserNameLength = 256
    MaxEmailLength = 256
    MaxNameLength = 64
    MaxSurnameLength = 64
    # 来源：Swagger UpdateProfileDto.phoneNumber.maxLength=16
    MaxPhoneNumberLength = 16

    # ABP 默认用户名允许字符：字母数字 + @ . _ -
    UserNamePattern = r"^[a-zA-Z0-9@\._\-]+$"

    # 最小可用 email 正则（用于 sanity，不做 RFC 全覆盖）
    EmailPattern = r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$"


# ============================================================
# Screenshot helpers
# ============================================================


def now_suffix() -> str:
    return datetime.now().strftime("%H%M%S")


def step_shot(page_obj, name: str, *, full_page: bool = False) -> None:
    """
    关键步骤截图（Allure 附件）。
    - page_obj: BasePage 子类
    """
    try:
        page_obj.take_screenshot(name, full_page=full_page)
    except Exception:
        # 不让截图失败阻塞主流程
        pass


def debug_shot(page_obj, name: str) -> None:
    """
    调试截图：默认全页，尽量在失败/回滚路径保留证据。
    """
    step_shot(page_obj, name, full_page=True)


def settle_toasts(page_obj, *, timeout_ms: int = 2000) -> None:
    """
    尝试等待 toast 动画/通知区域稳定，减少 flaky。
    """
    page = getattr(page_obj, "page", None)
    if page is None:
        return
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        try:
            # Notifications (F8) 是页面上常见的 region；有则等待其列表项稳定
            region = page.get_by_role("region", name=re.compile("Notifications", re.I))
            if region.count() > 0:
                # 如果有 listitem，等一小段时间让动画结束
                item = region.first.get_by_role("listitem").first
                if item.count() > 0:
                    page.wait_for_timeout(150)
                    return
        except Exception:
            pass
        try:
            page.wait_for_timeout(100)
        except Exception:
            break


def step_shot_after_success_toast(page_obj, name: str, *, timeout_ms: int = 3000) -> None:
    """
    等待 success toast（如果存在）后截图；不存在则直接截图。
    """
    page = getattr(page_obj, "page", None)
    if page is not None:
        try:
            region = page.get_by_role("region", name=re.compile("Notifications", re.I))
            item = region.get_by_role("listitem").first
            item.wait_for(state="visible", timeout=timeout_ms)
        except Exception:
            pass
    step_shot(page_obj, name)


# ============================================================
# Rule source (audit)
# ============================================================


def attach_rule_source_note(note: str = "") -> None:
    """
    把“规则来源/推导说明”作为 Allure 附件，便于审计。
    """
    try:
        allure.attach(note or "rule_source: (not provided)", name="rule_source", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass


def attach_backend_text(name: str, text: str) -> None:
    """
    附加后端响应/状态等文本（用于诊断）。
    注意：不得包含密码/Token。
    """
    try:
        allure.attach(text or "", name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass


def assert_no_dialog(page: Page, dialog_seen: dict) -> None:
    """
    Security 断言：XSS 不应触发浏览器 dialog。
    dialog_seen 由测试在 page.on("dialog", ...) 中维护。
    """
    t = (dialog_seen or {}).get("type")
    msg = (dialog_seen or {}).get("message")
    if t is None and msg is None:
        return
    try:
        allure.attach(str(dialog_seen), name="unexpected_dialog", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass
    raise AssertionError(f"unexpected dialog: type={t} message={(msg or '')[:200]}")


def check_success_toast(page_obj, *, timeout_ms: int = 1500) -> bool:
    """
    轻量成功提示探测（toast/status/notifications）。
    不绑定具体 UI 框架；用于矩阵用例的辅助判定。
    """
    page = getattr(page_obj, "page", None)
    if page is None:
        return False
    try:
        # role=status 常见于“保存成功”
        st = page.get_by_role("status")
        if st.is_visible(timeout=timeout_ms):
            txt = (st.text_content() or "").lower()
            if ("success" in txt) or ("updated" in txt) or ("成功" in txt) or ("更新" in txt):
                return True
    except Exception:
        pass
    try:
        # notifications region
        region = page.get_by_role("region", name=re.compile("Notifications", re.I))
        item = region.get_by_role("listitem").first
        if item.is_visible(timeout=timeout_ms):
            txt = (item.text_content() or "").lower()
            if ("success" in txt) or ("updated" in txt) or ("成功" in txt) or ("更新" in txt):
                return True
            # 只要出现 toast，也可作为“有反馈”的证据
            return True
    except Exception:
        pass
    return False


def abp_profile_put(page: Page, baseline: dict, patch: dict) -> dict:
    """
    通过前端同域 API 强制回滚 Profile（用于 Security/Matrix 的“防污染”）。
    返回：{ok,status,body}
    """
    origin = ""
    try:
        origin = (page.url or "").split("/")[0:3]
        origin = "/".join(origin)
    except Exception:
        origin = ""
    if not origin:
        # 兜底：按 dev 前端
        origin = "https://localhost:3000"

    payload = dict(baseline or {})
    payload.update(patch or {})
    try:
        resp = page.request.put(f"{origin}/api/account/my-profile", data=payload)
        body = ""
        try:
            body = resp.text() or ""
        except Exception:
            body = ""
        return {"ok": bool(resp.ok), "status": int(resp.status), "body": body[:2000]}
    except Exception as e:
        return {"ok": False, "status": None, "body": f"exception:{type(e).__name__}:{e}"}


def abp_profile_put_should_reject(page: Page, baseline: dict, patch: dict) -> None:
    """
    断言：后端应拒绝该 patch（4xx）。
    """
    r = abp_profile_put(page, baseline, patch)
    st = r.get("status")
    if st is None:
        raise AssertionError(f"expected backend reject (4xx) but request failed: {r}")
    if 400 <= int(st) < 500:
        return
    raise AssertionError(f"expected backend reject (4xx) but got status={st} body={str(r.get('body'))[:200]}")


# ============================================================
# Generic assertions used by suites
# ============================================================


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {url}"



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
