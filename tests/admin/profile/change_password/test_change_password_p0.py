"""
Change Password - P0

P0 原则：
- 主链路必须可回滚（两次改密：old -> new -> old）
- 不写入任何真实密码/凭证到仓库文件
"""

from __future__ import annotations

import os

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from utils.logger import TestLogger
from tests.admin.profile.change_password._helpers import (
    attach_backend_text,
    fetch_abp_password_policy,
    generate_password,
    step_shot,
    step_shot_after_success_toast,
)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P0 - 主流程")
@allure.description(
    """
测试点：
- 页面可打开（/admin/profile/change-password）且核心控件可见
- 改密成功并立即回滚，避免污染账号池

账号来源：
- 本文件不写死账号/密码；运行期由账号池 fixture 提供
"""
)
def test_p0_change_password_page_load(auth_page: Page):
    logger = TestLogger("test_p0_change_password_page_load")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    with allure.step("导航到 Change Password 页面"):
        page_obj.navigate()
        step_shot(page_obj, "step_navigate")

    assert not page_obj.is_login_page(), f"疑似未登录，current_url={auth_page.url}"
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
@allure.description(
    """
测试点：
- 改密成功（old -> new）
- 立即回滚（new -> old），保证可重复执行

实现说明：
- 为了获取 current password，本用例使用“UI 登录链路”fixture：logged_in_page + test_account
- 仅在本用例中使用该链路，避免大范围增加 lockout 风险
"""
)
def test_p0_change_password_success_and_rollback(logged_in_page: Page, test_account: dict):
    logger = TestLogger("test_p0_change_password_success_and_rollback")
    logger.start()

    old_password = (test_account.get("password") or "").strip()
    assert old_password, "missing current password from account pool (test_account.password is empty)"

    page_obj = AdminProfileChangePasswordPage(logged_in_page)
    page_obj.navigate()
    step_shot(page_obj, "step_navigate")

    with allure.step("读取 ABP PasswordPolicy（真理源）"):
        policy = fetch_abp_password_policy(logged_in_page)

    # 生成新密码：满足策略 + 不是旧密码 + 正常长度（避免边界值污染 P0）
    target_len = max(int(getattr(policy, "required_length", 6) or 6), 8)
    new_password = generate_password(policy, length=target_len)
    if new_password == old_password:
        new_password = generate_password(policy, length=target_len + 1)

    with allure.step("第一次改密：old -> new（期望成功）"):
        step_shot(page_obj, "step_before_change_1")
        resp1 = page_obj.submit_change_password(old_password, new_password, new_password, wait_response=True, timeout_ms=20000)
        # 等待success toast并截图（全屏，确保toast可见）
        step_shot_after_success_toast(page_obj, "step_after_submit_1_with_toast")
        assert resp1 is not None and resp1.ok, f"change-password failed (1st) status={getattr(resp1,'status',None)}"

    with allure.step("第二次改密（回滚）：new -> old（期望成功）"):
        step_shot(page_obj, "step_before_change_2")
        resp2 = page_obj.submit_change_password(new_password, old_password, old_password, wait_response=True, timeout_ms=20000)
        # 等待success toast并截图（全屏）
        step_shot_after_success_toast(page_obj, "step_after_submit_2_with_toast")
        assert resp2 is not None and resp2.ok, f"change-password rollback failed status={getattr(resp2,'status',None)}"

    # 仅在需要审计时展示后端 body（默认关闭，避免噪音）
    try:
        attach_backend_text("change_password_statuses", f"{resp1.status},{resp2.status}")
    except Exception:
        pass

    logger.end(success=True)


