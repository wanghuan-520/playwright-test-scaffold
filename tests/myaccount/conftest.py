# ═══════════════════════════════════════════════════════════════
# Profile Settings - Local Fixtures (tests/myaccount)
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
本目录专用 fixture：
- 解决"跨用例状态泄漏"：即使某条用例失败，也必须把 Profile 恢复到可提交的合法状态。
- 账号从账号池获取
"""

from __future__ import annotations

import re
import time
from typing import Dict, Tuple

import pytest
from playwright.sync_api import Page

from pages.personal_settings_page import PersonalSettingsPage
from tests.myaccount._helpers import now_suffix, step_shot, debug_shot, settle_toasts, attach_backend_text


def _sanitize_local_part(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "user"


def _is_reasonably_short(value: str, max_len: int) -> bool:
    value = (value or "").strip()
    return (len(value) > 0) and (len(value) <= max_len)


def _ensure_baseline(page_obj: PersonalSettingsPage) -> Dict[str, str]:
    """
    把页面资料修正到"可提交"的 baseline。

    说明：
    - 新页面中 userName/email 是只读的，无法修改
    - firstName/lastName/phoneNumber 是可编辑的
    - baseline 值将用于 teardown 回滚（即使测试失败也执行）
    """
    if page_obj.is_login_page():
        debug_shot(page_obj, "baseline_fail_redirected_to_login")
        pytest.fail(f"疑似未登录：访问 {page_obj.URL} 被重定向到登录页 url={page_obj.page.url}", pytrace=False)

    deadline = time.time() + 20.0
    while time.time() < deadline:
        if page_obj.is_loaded():
            break
        try:
            page_obj.page.wait_for_timeout(200)
        except Exception:
            break

    if not page_obj.is_loaded():
        debug_shot(page_obj, "baseline_fail_not_loaded")
        try:
            attach_backend_text("baseline_fail_current_url", str(page_obj.page.url))
        except Exception:
            pass
        pytest.fail(
            f"PersonalSettingsPage 未加载出表单，url={page_obj.page.url}",
            pytrace=False,
        )

    # 读取当前表单值（需要进入编辑模式）
    current = page_obj.read_form_values()
    
    # 新页面中 userName 和 email 是只读的，不需要修正
    # 只需要确保 firstName/lastName/phoneNumber 的值合理
    
    return current


@pytest.fixture(scope="function")
def profile_settings(auth_page: Page) -> Tuple[Page, PersonalSettingsPage, Dict[str, str]]:
    """
    返回：
    - page（已登录，账号从账号池获取）
    - page_obj（PersonalSettingsPage）
    - baseline_values（当前表单值作为 baseline）
    """
    page_obj = PersonalSettingsPage(auth_page)
    page_obj.navigate()
    baseline = _ensure_baseline(page_obj)
    
    # 退出编辑模式（如果进入了）
    try:
        page_obj.exit_edit_mode()
    except Exception:
        pass
    
    # 重置"本用例是否真正写成功过"的标记
    try:
        setattr(page_obj, "_profile_update_ok_in_test", False)
    except Exception:
        pass

    yield auth_page, page_obj, baseline

    # teardown：无论测试是否失败，都尽量恢复 baseline
    try:
        wrote_ok = bool(getattr(page_obj, "_profile_update_ok_in_test", False))
        attach_backend_text("teardown_wrote_ok_in_test", str(wrote_ok))

        if not wrote_ok:
            debug_shot(page_obj, "teardown_skip_no_persisted_change")
            return

        # 有成功写入：回滚到 baseline
        settle_toasts(page_obj)
        page_obj.fill_form(baseline)
        debug_shot(page_obj, "teardown_restore_fill")
        resp = page_obj.click_save_and_capture_profile_update(timeout_ms=12000)
        if resp is not None:
            attach_backend_text("teardown_profile_update_status", str(resp.status))
        debug_shot(page_obj, "teardown_restore_done")
    except Exception:
        pass
