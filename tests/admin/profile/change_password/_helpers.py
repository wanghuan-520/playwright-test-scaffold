# ═══════════════════════════════════════════════════════════════
# Change Password - Test Helpers
# ═══════════════════════════════════════════════════════════════
"""
仅服务于 Profile -> Change Password 的测试 helper。

原则：
- 关键步骤截图（默认开启；FAST=1 可跳过）
- Allure 降噪：默认仅展示前端证据；后端诊断按开关显示
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Dict, Any

import allure


# FAST=1：跳过高开销动作（截图/等 toast）
FAST_MODE: bool = os.getenv("FAST", "0") == "1"
FULL_PAGE_SHOT: bool = os.getenv("FULL_PAGE_SHOT", "0") == "1"
ALLURE_SHOW_BACKEND: bool = os.getenv("ALLURE_SHOW_BACKEND", "0") == "1"
ALLURE_SHOW_META: bool = os.getenv("ALLURE_SHOW_META", "0") == "1"
ALLURE_SHOW_DEBUG: bool = os.getenv("ALLURE_SHOW_DEBUG", "0") == "1"


def now_suffix() -> str:
    return datetime.now().strftime("%H%M%S")


def step_shot(page_obj, name: str) -> None:
    if FAST_MODE:
        return
    page_obj.take_screenshot(name, full_page=FULL_PAGE_SHOT)


def debug_shot(page_obj, name: str) -> None:
    if FAST_MODE:
        return
    if not ALLURE_SHOW_DEBUG:
        return
    page_obj.take_screenshot(name, full_page=FULL_PAGE_SHOT)


def settle_toasts(page_obj, timeout_ms: int = 8000) -> None:
    if FAST_MODE:
        return
    try:
        page_obj.wait_for_toasts_to_disappear(timeout_ms=timeout_ms)
    except Exception:
        return


def attach_backend_text(name: str, text: str) -> None:
    if not ALLURE_SHOW_BACKEND:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_backend_json(name: str, obj: Any) -> None:
    if not ALLURE_SHOW_BACKEND:
        return
    try:
        import json

        allure.attach(json.dumps(obj, ensure_ascii=False, indent=2), name=name, attachment_type=allure.attachment_type.JSON)
    except Exception:
        allure.attach(str(obj), name=name, attachment_type=allure.attachment_type.TEXT)


def attach_meta_text(name: str, text: str) -> None:
    if not ALLURE_SHOW_META:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_rule_source_note() -> None:
    attach_meta_text(
        name="rule_source",
        text=(
            "规则来源："
            "frontend src/components/profile/ChangePassword.tsx（shouldDisabled/toast + required） + "
            "backend swagger /api/account/my-profile/change-password（ChangePasswordInput maxLength=128）。"
        ),
    )


def capture_dialogs(page) -> Dict[str, Optional[str]]:
    """
    安全用例：捕获任何 dialog（alert/confirm/prompt），不允许弹窗执行。
    """
    seen: Dict[str, Optional[str]] = {"type": None, "message": None}

    def _on_dialog(d):
        try:
            seen["type"] = getattr(d, "type", None)
            seen["message"] = getattr(d, "message", None)
        except Exception:
            pass
        try:
            d.dismiss()
        except Exception:
            pass

    try:
        page.on("dialog", _on_dialog)
    except Exception:
        pass
    return seen


