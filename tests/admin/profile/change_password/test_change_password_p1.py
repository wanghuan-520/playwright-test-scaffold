# ═══════════════════════════════════════════════════════════════
# Change Password - P1 (Validation / Boundary / Backend Consistency)
# ═══════════════════════════════════════════════════════════════
"""
P1：
- confirm mismatch（前端 shouldDisabled 拦截）
- PasswordPolicy（ABP setting 真理源）与 maxLength（swagger 真理源）
- “前后端一致性”：应被拒绝的输入后端必须 4xx，不允许 5xx
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import allure

from utils.logger import TestLogger
from tests.admin.profile.change_password._helpers import attach_rule_source_note, step_shot, settle_toasts, attach_backend_text, attach_backend_json


DATA_PATH = Path("test-data/admin-profile-change-password_data.json")


def _load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - Confirm mismatch")
def test_p1_confirm_password_mismatch_should_be_blocked(change_password):
    attach_rule_source_note()
    logger = TestLogger("test_p1_confirm_password_mismatch_should_be_blocked")
    logger.start()

    _page, page_obj, ctx = change_password
    data = _load_data()
    original_password = ctx["original_password"]
    mismatch = data["invalid"]["confirm_mismatch"]

    with allure.step("New/Confirm 不一致，点击 Save（期望前端 toast + 不发请求）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(mismatch["new"])
        page_obj.fill_confirm_password(mismatch["confirm"])
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_capture_change_password(timeout_ms=1500)
        assert resp is None, "confirm mismatch 应被前端拦截（不应发请求）"
        page_obj.wait_for_any_toast(timeout_ms=3000)
        step_shot(page_obj, "step_toast_visible")

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - PasswordPolicy")
@pytest.mark.parametrize(
    "case_key",
    [
        "too_short_len_5",
        "missing_digit",
        "missing_lowercase",
        "missing_uppercase",
        "missing_special",
    ],
)
def test_p1_password_policy_rejected_by_backend(change_password, case_key: str):
    """
    前端未实现 PasswordPolicy 校验（仅校验 new/confirm 是否为空&一致），因此这些 case 应发请求并由后端拒绝。
    """
    attach_rule_source_note()
    logger = TestLogger(f"test_p1_password_policy_rejected_by_backend[{case_key}]")
    logger.start()

    _page, page_obj, ctx = change_password
    data = _load_data()
    original_password = ctx["original_password"]
    new_password = data["invalid"][case_key]

    with allure.step(f"填写 current + policy非法 new={case_key} 并点击 Save（期望后端 4xx）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(new_password)
        page_obj.fill_confirm_password(new_password)
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_wait_change_password(timeout_ms=20000)
        attach_backend_text("status", str(resp.status))
        if resp.status < 400 or resp.status >= 500:
            # 失败必须可诊断：尽量挂出 ABP validationErrors
            try:
                attach_backend_json("validationErrors", page_obj.get_abp_validation_errors(resp))
            except Exception:
                pass
        assert 400 <= resp.status < 500, f"expected backend reject (4xx), got {resp.status}"
        step_shot(page_obj, "step_after_reject")

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - Boundary")
@pytest.mark.parametrize(
    "case_key,should_ok",
    [
        ("min_minus_1_len_5", False),
        ("min_len_6", True),
        ("min_plus_1_len_7", True),
    ],
)
def test_p1_password_length_min_boundary(change_password, case_key: str, should_ok: bool):
    attach_rule_source_note()
    logger = TestLogger(f"test_p1_password_length_min_boundary[{case_key}]")
    logger.start()

    _page, page_obj, ctx = change_password
    data = _load_data()
    original_password = ctx["original_password"]
    candidate = data["boundary"][case_key]

    with allure.step(f"长度边界用例 {case_key}（should_ok={should_ok}）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(candidate)
        page_obj.fill_confirm_password(candidate)
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_wait_change_password(timeout_ms=20000)
        if should_ok:
            assert resp.ok, f"expected OK, got status={resp.status}"
            ctx["changed_to"] = candidate
        else:
            assert 400 <= resp.status < 500, f"expected reject (4xx), got {resp.status}"
        step_shot(page_obj, "step_after_submit")

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - Boundary")
def test_p1_password_max_length_129_rejected(change_password):
    """
    Swagger 真理源：ChangePasswordInput.newPassword maxLength=128。
    因此 len=129 应在模型绑定/校验阶段被拒绝（4xx）。
    """
    attach_rule_source_note()
    logger = TestLogger("test_p1_password_max_length_129_rejected")
    logger.start()

    _page, page_obj, ctx = change_password
    data = _load_data()
    original_password = ctx["original_password"]
    too_long = data["boundary"]["max_plus_1_len_129"]

    with allure.step("newPassword len=129（max+1），点击 Save（期望后端 4xx）"):
        settle_toasts(page_obj)
        page_obj.fill_current_password(original_password)
        page_obj.fill_new_password(too_long)
        page_obj.fill_confirm_password(too_long)
        step_shot(page_obj, "step_before_click")
        resp = page_obj.click_save_and_wait_change_password(timeout_ms=20000)
        attach_backend_text("status", str(resp.status))
        assert 400 <= resp.status < 500, f"expected reject (4xx), got {resp.status}"
        step_shot(page_obj, "step_after_reject")

    logger.end(success=True)


