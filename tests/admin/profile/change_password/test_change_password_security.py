# ═══════════════════════════════════════════════════════════════
# Change Password - Security
# ═══════════════════════════════════════════════════════════════
"""
安全最小集：
- 未登录访问应被拦截（重定向到登录/租户流程）
- XSS/SQLi 载荷不执行、不弹 dialog、不导致 5xx
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import allure

from utils.logger import TestLogger
from pages.change_password_page import ChangePasswordPage
from tests.admin.profile.change_password._helpers import (
    attach_rule_source_note,
    step_shot,
    settle_toasts,
    capture_dialogs,
)


DATA_PATH = Path("test-data/admin-profile-change-password_data.json")


def _load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Change Password")
@allure.story("Security - 未登录拦截")
def test_security_unauthenticated_should_redirect_to_login(unauth_page):
    attach_rule_source_note()
    logger = TestLogger("test_security_unauthenticated_should_redirect_to_login")
    logger.start()

    page_obj = ChangePasswordPage(unauth_page)
    with allure.step("未登录访问 /admin/profile/change-password"):
        page_obj.navigate()
        step_shot(page_obj, "step_navigate_unauth")
        # 允许登录/租户设置两类拦截入口
        assert page_obj.is_login_page(), f"expected redirect to login flow, got url={unauth_page.url}"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Change Password")
@allure.story("Security - XSS/SQLi 不执行")
@pytest.mark.parametrize("payload_key", ["xss_min", "sqli_min"])
def test_security_payloads_no_dialog_no_5xx(change_password, payload_key: str):
    """
    断言要点：
    - 不弹 dialog（alert/confirm/prompt）
    - 若触发提交请求：不应为 5xx
    - 不强绑 toast 文案（避免 i18n/样式漂移）
    """
    attach_rule_source_note()
    logger = TestLogger(f"test_security_payloads_no_dialog_no_5xx[{payload_key}]")
    logger.start()

    page, page_obj, ctx = change_password
    data = _load_data()
    payload = data["security_payloads"][payload_key]
    original_password = ctx["original_password"]

    dialog_seen = capture_dialogs(page)

    with allure.step(f"把 payload={payload_key} 填入 new/confirm 并提交"):
        settle_toasts(page_obj)
        step_shot(page_obj, "step_before_fill")
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(payload)
        page_obj.fill_confirm_password(payload)
        step_shot(page_obj, "step_after_fill")
        resp = page_obj.click_save_and_capture_change_password(timeout_ms=20000)

        # 不允许弹窗执行
        assert dialog_seen.get("type") is None, f"dialog should not appear, got={dialog_seen}"

        # 可能被前端拦截（比如某些环境下额外校验），也可能发请求被后端拒绝（4xx）
        if resp is not None:
            assert resp.status < 500, f"should not be 5xx, got {resp.status}"
        step_shot(page_obj, "step_after_submit")

    logger.end(success=True)


