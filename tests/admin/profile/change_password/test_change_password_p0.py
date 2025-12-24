# ═══════════════════════════════════════════════════════════════
# Change Password - P0
# ═══════════════════════════════════════════════════════════════
"""
P0：
- 页面可加载
- 主流程成功（改密成功，且必须可回滚）
- 必填校验（字段维度）：Current/New/Confirm
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import allure

from utils.logger import TestLogger
from tests.admin.profile.change_password._helpers import attach_rule_source_note, step_shot, settle_toasts


DATA_PATH = Path("test-data/admin-profile-change-password_data.json")


def _load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 页面加载")
def test_p0_change_password_page_load(change_password):
    attach_rule_source_note()
    logger = TestLogger("test_p0_change_password_page_load")
    logger.start()

    _page, page_obj, _ctx = change_password
    with allure.step("导航到 Change Password 并验证核心控件可见"):
        step_shot(page_obj, "step_navigate")
        assert page_obj.is_visible(page_obj.CURRENT_PASSWORD_INPUT, timeout=3000)
        assert page_obj.is_visible(page_obj.NEW_PASSWORD_INPUT, timeout=3000)
        assert page_obj.is_visible(page_obj.CONFIRM_PASSWORD_INPUT, timeout=3000)
        assert page_obj.is_visible(page_obj.SAVE_BUTTON, timeout=3000)
        step_shot(page_obj, "step_verify_controls")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 主流程")
def test_p0_change_password_success_and_revert(change_password):
    """
    P0：改密成功（happy path）。

    回滚策略：
    - 本用例只负责把“changed_to”写到 ctx，真正回滚在 fixture teardown 执行（避免重复保存耗时）。
    """
    attach_rule_source_note()
    logger = TestLogger("test_p0_change_password_success_and_revert")
    logger.start()

    _page, page_obj, ctx = change_password
    data = _load_data()
    new_password = data["valid"]["new_password_valid"]
    original_password = ctx["original_password"]

    assert new_password != original_password, "new_password_valid 必须与原密码不同（避免 no-op）"

    with allure.step("填写 current/new/confirm 并点击 Save（期望成功）"):
        settle_toasts(page_obj)
        step_shot(page_obj, "step_before_fill")
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(new_password)
        page_obj.fill_confirm_password(new_password)
        step_shot(page_obj, "step_after_fill")
        resp = page_obj.click_save_and_wait_change_password(timeout_ms=20000)
        assert resp.ok, f"change-password failed status={resp.status}"
        ctx["changed_to"] = new_password
        step_shot(page_obj, "step_after_save")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 必填校验")
def test_p0_current_password_required(change_password):
    attach_rule_source_note()
    logger = TestLogger("test_p0_current_password_required")
    logger.start()

    _page, page_obj, _ctx = change_password
    data = _load_data()
    new_password = data["valid"]["new_password_valid"]

    with allure.step("Current password 为空，点击 Save（期望被浏览器 required 拦截，不发请求）"):
        settle_toasts(page_obj)
        page_obj.fill_new_password(new_password)
        page_obj.fill_confirm_password(new_password)
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_capture_change_password(timeout_ms=1500)
        assert resp is None, "前端/浏览器应拦截（不应发出 change-password 请求）"

        # 尽力触发 HTML5 validity，并采集证据（不绑定具体文案）
        page_obj.report_validity(page_obj.CURRENT_PASSWORD_INPUT)
        msg = page_obj.get_html5_validation_message(page_obj.CURRENT_PASSWORD_INPUT)
        assert msg.strip() != "", "expected html5 validationMessage for required field"
        step_shot(page_obj, "step_after_validity")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 必填校验")
def test_p0_new_password_required(change_password):
    """
    前端逻辑证据：
    - src/components/profile/ChangePassword.tsx: shouldDisabled() 对 new/confirm 为空直接 toast + return
    """
    attach_rule_source_note()
    logger = TestLogger("test_p0_new_password_required")
    logger.start()

    _page, page_obj, ctx = change_password
    original_password = ctx["original_password"]

    with allure.step("New password 为空，点击 Save（期望 toast 且不发请求）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_confirm_password(" ")
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_capture_change_password(timeout_ms=1500)
        assert resp is None, "shouldDisabled 应拦截（不应发出请求）"
        page_obj.wait_for_any_toast(timeout_ms=3000)
        step_shot(page_obj, "step_toast_visible")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 必填校验")
def test_p0_confirm_password_required(change_password):
    attach_rule_source_note()
    logger = TestLogger("test_p0_confirm_password_required")
    logger.start()

    _page, page_obj, ctx = change_password
    original_password = ctx["original_password"]

    with allure.step("Confirm new password 为空，点击 Save（期望 toast 且不发请求）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password("Aa1!aa")
        page_obj.fill_confirm_password(" ")
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_capture_change_password(timeout_ms=1500)
        assert resp is None, "shouldDisabled 应拦截（不应发出请求）"
        page_obj.wait_for_any_toast(timeout_ms=3000)
        step_shot(page_obj, "step_toast_visible")

    logger.end(success=True)


