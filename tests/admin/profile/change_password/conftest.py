# ═══════════════════════════════════════════════════════════════
# Change Password - Local Fixtures
# ═══════════════════════════════════════════════════════════════
"""
本目录专用 fixture：
- 进入 Change Password 页面
- 写操作必须可回滚：若成功改密，teardown 会把密码改回原值（避免污染账号池/后续登录）

注意：
- 账号来源遵循仓库规则：默认走账号池 fixture `test_account`。
- 密码字段为敏感信息：禁止写入日志/附件。
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, Optional

import pytest
from playwright.sync_api import Page

from pages.change_password_page import ChangePasswordPage
from utils.config import ConfigManager
from ._helpers import debug_shot, settle_toasts, attach_backend_text, attach_backend_json


def _xsrf_headers_from_cookies(page: Page) -> Dict[str, str]:
    """
    某些 ABP/后端直连场景需要 XSRF header。若拿不到 token，则返回空 dict。
    """
    token = ""
    try:
        for c in (page.context.cookies() or []):
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


def abp_change_password(page: Page, current_password: str, new_password: str) -> Dict[str, Any]:
    """
    直连后端/前端 API 修改密码（用于 teardown 回滚）。
    返回结构化结果，便于失败时诊断。
    """
    import json as _json

    cfg = ConfigManager()
    backend = (cfg.get_service_url("backend") or "").rstrip("/")
    frontend = (cfg.get_service_url("frontend") or "").rstrip("/")
    bases = [b for b in [backend, frontend] if b]

    api = page.context.request
    last_exc: Optional[Exception] = None
    for base in bases:
        url = f"{base}/api/account/my-profile/change-password"
        headers = {"content-type": "application/json", "accept": "application/json"}
        if base == backend:
            headers.update(_xsrf_headers_from_cookies(page))
        payload = {"currentPassword": current_password, "newPassword": new_password}
        try:
            resp = api.post(url, data=_json.dumps(payload), headers=headers)
            body = ""
            try:
                body = resp.text() or ""
            except Exception:
                body = ""
            ves = []
            try:
                ves = ChangePasswordPage(page).get_abp_validation_errors(resp)
            except Exception:
                ves = []
            return {"base": base, "url": url, "status": resp.status, "ok": bool(resp.ok), "body": body, "validationErrors": ves}
        except Exception as e:
            last_exc = e
            continue
    return {"base": None, "url": None, "status": None, "ok": False, "body": str(last_exc or "no response"), "validationErrors": []}


@pytest.fixture(scope="function")
def change_password(auth_page: Page, test_account: Dict[str, str]) -> Tuple[Page, ChangePasswordPage, Dict[str, str]]:
    """
    返回：
    - page（已登录）
    - page_obj（ChangePasswordPage）
    - ctx（包含原始密码，用于 teardown 回滚）
    """
    page_obj = ChangePasswordPage(auth_page)
    page_obj.navigate()
    assert not page_obj.is_login_page(), f"疑似未登录/被重定向，url={auth_page.url}"
    assert page_obj.is_loaded(), "Change Password 页面未加载完成"

    # teardown 上下文（不写入任何明文密码到日志/附件）
    ctx = {
        "username": test_account.get("username"),
        "email": test_account.get("email"),
        "original_password": (test_account.get("password") or ""),
        "changed_to": None,
    }
    # 用例开始前：清理上条 toast，避免截图污染
    settle_toasts(page_obj)

    # 标记：本用例是否真正改密成功过（用于 teardown 决策）
    try:
        setattr(page_obj, "_change_password_ok_in_test", False)
    except Exception:
        pass

    yield auth_page, page_obj, ctx

    # teardown：若本用例成功改密过，则把密码改回原值
    try:
        wrote_ok = bool(getattr(page_obj, "_change_password_ok_in_test", False))
        attach_backend_text("teardown_change_password_ok_in_test", str(wrote_ok))
        if not wrote_ok:
            debug_shot(page_obj, "teardown_skip_no_persisted_change")
            return

        original = ctx.get("original_password") or ""
        changed_to = ctx.get("changed_to") or ""
        if not original or not changed_to:
            attach_backend_text("teardown_missing_password_context", "missing original/changed_to")
            return

        settle_toasts(page_obj)
        res = abp_change_password(auth_page, current_password=changed_to, new_password=original)
        attach_backend_text("teardown_revert_status", str(res.get("status")))
        if not res.get("ok", False):
            attach_backend_json("teardown_revert_body", {"body": (res.get("body") or "")[:2000], "validationErrors": res.get("validationErrors")})
            assert res.get("ok", False), f"teardown revert failed status={res.get('status')}"
        debug_shot(page_obj, "teardown_revert_done")
    except Exception:
        # 不让 teardown 扩大化；失败诊断由 artifacts_on_failure 兜底
        pass


