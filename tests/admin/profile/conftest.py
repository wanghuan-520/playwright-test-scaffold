# ═══════════════════════════════════════════════════════════════
# Profile Settings - Local Fixtures (tests/admin/profile)
# ═══════════════════════════════════════════════════════════════
"""
本目录专用 fixture：
- 解决“跨用例状态泄漏”：即使某条用例失败，也必须把 Profile 恢复到可提交的合法状态。
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

import pytest
from playwright.sync_api import Page

from pages.personal_settings_page import PersonalSettingsPage
from ._helpers import now_suffix, step_shot, debug_shot, settle_toasts, attach_backend_text


def _sanitize_local_part(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _is_valid_email_basic(email: str) -> bool:
    email = (email or "").strip()
    if len(email) > 256:
        return False
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    if not local or "." not in domain:
        return False
    return True


def _is_reasonably_short(value: str, max_len: int) -> bool:
    value = (value or "").strip()
    return (len(value) > 0) and (len(value) <= max_len)


def _ensure_baseline(page_obj: PersonalSettingsPage) -> Dict[str, str]:
    """
    把页面资料修正到“可提交”的 baseline。

    说明：
    - userName/email 是必填；如果当前值明显非法（空/超长/邮箱无 @），先修正再保存一次
    - baseline 值将用于 teardown 回滚（即使测试失败也执行）
    """
    current = page_obj.read_form_values()
    patch: Dict[str, str] = {}

    # baseline 设计原则：
    # - P0 用例不应该默认把输入框填成“接近 maxLength 的超长字符串”
    # - baseline 应“正常且稳定”，边界值只在 @pytest.mark.boundary 的用例中显式构造
    NORMAL_USERNAME_MAX = 32
    NORMAL_NAME_MAX = 32
    NORMAL_SURNAME_MAX = 32
    NORMAL_EMAIL_MAX = 64

    # userName
    user = (current.get("userName") or "").strip()
    if (not user) or (len(user) > 256) or (not _is_reasonably_short(user, NORMAL_USERNAME_MAX)):
        suf = now_suffix()
        safe = _sanitize_local_part(user)[:16]
        patch["userName"] = f"{safe}_{suf}"

    # name / surname（非必填，但 baseline 也保持“正常长度”，避免 P0 截图/回滚出现超长噪音）
    name = (current.get("name") or "").strip()
    if name and (len(name) > 64 or not _is_reasonably_short(name, NORMAL_NAME_MAX)):
        suf = now_suffix()
        patch["name"] = f"Auto_{suf}"

    surname = (current.get("surname") or "").strip()
    if surname and (len(surname) > 64 or not _is_reasonably_short(surname, NORMAL_SURNAME_MAX)):
        suf = now_suffix()
        patch["surname"] = f"Run_{suf}"

    # email
    email = (current.get("email") or "").strip()
    if (not _is_valid_email_basic(email)) or (not _is_reasonably_short(email, NORMAL_EMAIL_MAX)):
        suf = now_suffix()
        # 尽量与 username 关联，降低“唯一性”冲突风险
        base = _sanitize_local_part(patch.get("userName") or user)[:16]
        patch["email"] = f"{base}_{suf}@t.com"

    if patch:
        # 不在 Allure 展示“回到 baseline/修正”过程，只保留关键截图与必要诊断
        page_obj.fill_form(patch)
        debug_shot(page_obj, "baseline_fix_fill")
        resp = page_obj.save_and_wait_profile_update(timeout_ms=20000)
        attach_backend_text("baseline_fix_profile_update_status", str(resp.status))
        debug_shot(page_obj, "baseline_fix_saved")

        # 重新读取，作为 baseline
        return page_obj.read_form_values()

    # 无需修正，当前即 baseline
    return current


@pytest.fixture(scope="function")
def profile_settings(auth_page: Page) -> Tuple[Page, PersonalSettingsPage, Dict[str, str]]:
    """
    返回：
    - page（已登录）
    - page_obj（PersonalSettingsPage）
    - baseline_values（保证可提交的 baseline）
    """
    page_obj = PersonalSettingsPage(auth_page)
    page_obj.navigate()
    baseline = _ensure_baseline(page_obj)
    # baseline 建立完成后，重置“本用例是否真正写成功过”的标记（避免 baseline_fix 的保存污染判断）
    try:
        setattr(page_obj, "_profile_update_ok_in_test", False)
    except Exception:
        pass

    yield auth_page, page_obj, baseline

    # teardown：无论测试是否失败，都尽量恢复 baseline（不让后续用例继承脏状态）
    try:
        # 不在 Allure 展示“回到 baseline/teardown 回滚”过程，只保留关键截图与必要诊断
        wrote_ok = bool(getattr(page_obj, "_profile_update_ok_in_test", False))
        attach_backend_text("teardown_wrote_ok_in_test", str(wrote_ok))

        # 没有“成功写入”过：无需回滚保存（新 page/context 会被销毁，不会污染下一条；服务端也不应被改动）
        if not wrote_ok:
            debug_shot(page_obj, "teardown_skip_no_persisted_change")
            return

        # 有成功写入：以“服务端当前值”为准判断是否需要回滚，避免无意义的二次保存
        keys = ["userName", "name", "surname", "email", "phoneNumber"]
        server_profile = None
        try:
            frontend = (page_obj.config.get_service_url("frontend") or "").rstrip("/")
            if frontend:
                r = auth_page.context.request.get(f"{frontend}/api/account/my-profile")
                if r.ok:
                    server_profile = r.json()
        except Exception:
            server_profile = None

        if isinstance(server_profile, dict):
            current_server = {k: (server_profile.get(k) or "") for k in keys}
            diff_server = {k: (current_server.get(k), baseline.get(k)) for k in keys if (current_server.get(k) or "") != (baseline.get(k) or "")}
            attach_backend_text("teardown_server_diff", str(diff_server))
            if not diff_server:
                debug_shot(page_obj, "teardown_noop_server_already_baseline")
                return

        # 需要回滚（或无法读取服务端，保守回滚一次）
        settle_toasts(page_obj)
        page_obj.fill_form(baseline)
        debug_shot(page_obj, "teardown_restore_fill")
        resp = page_obj.click_save_and_capture_profile_update(timeout_ms=12000)
        if resp is not None:
            attach_backend_text("teardown_profile_update_status", str(resp.status))
            assert resp.ok, f"teardown profileUpdate failed status={resp.status}"
        debug_shot(page_obj, "teardown_restore_done")
    except Exception:
        # 不让 teardown 把失败“扩大化”，证据由 artifacts_on_failure 负责采集
        pass

