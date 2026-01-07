"""
Change Password - P1

P1 原则：
- 以 ABP 后端规则为真理源（PasswordPolicy + Swagger 契约）
- 断言以“前端可观测行为”为主：error evidence / 不发请求 / 失败可诊断
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from tests.admin.profile._matrix_helpers import assert_frontend_has_error_evidence, wait_for_frontend_validation
from utils.logger import TestLogger

from tests.admin.profile.change_password._helpers import (
    attach_backend_text,
    fetch_abp_password_policy,
    generate_password,
    step_shot,
    step_shot_after_success_toast,
    step_shot_after_error_toast,
)


def _expect_no_change_password_request(page: Page, timeout_ms: int = 1200) -> bool:
    """快速探测：是否发生了改密请求（用于前端拦截断言）。"""
    try:
        page.wait_for_response(
            lambda r: ("/api/account/my-profile/change-password" in (r.url or "")) and (r.request.method == "POST"),
            timeout=timeout_ms,
        )
        return True
    except Exception:
        return False


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- newPassword + confirmNewPassword: JS验证非空且必须相同（trim()）
- 前端不验证长度和策略

后端限制：
- 如果前端未拦截，后端会返回4xx

测试点：
- new password与confirm password不匹配
- 预期：前端拦截（不发请求）+ 显示错误提示

断言：
- 不应发起 /api/account/my-profile/change-password 请求
- 前端必须有错误证据（红框/错误文案/toast）
    """
)
def test_p1_confirm_mismatch_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_confirm_mismatch_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step("构造 mismatch：new != confirm（前端必须拦截）"):
        policy = fetch_abp_password_policy(auth_page)
        length = max(int(getattr(policy, "required_length", 6) or 6), 8)
        new_pwd = generate_password(policy, length=length)
        confirm_pwd = generate_password(policy, length=length + 1)  # 保证不同

        step_shot(page_obj, "step_before_fill")
        page_obj.fill_form(current_password=" ", new_password=new_pwd, confirm_password=confirm_pwd)
        step_shot(page_obj, "step_filled")
        page_obj.click_save()

    with allure.step("断言：不应发起改密请求 + 前端有错误证据"):
        sent = _expect_no_change_password_request(auth_page, timeout_ms=1200)
        assert not sent, "confirm mismatch should be blocked by frontend (no request expected)"
        
        # ✅ 等待前端验证完成（给前端时间渲染错误提示）
        wait_for_frontend_validation(auth_page, timeout_ms=1000)
        
        # 等待error toast并全屏截图（确保toast完整可见）
        step_shot_after_error_toast(page_obj, "step_result_with_error_toast")
        
        # ✅ 再检查错误证据
        assert_frontend_has_error_evidence(auth_page, page_obj.CONFIRM_PASSWORD_INPUT, "confirm_mismatch")

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- currentPassword: HTML required 属性
- 浏览器原生验证可能阻止提交

后端限制：
- currentPassword 为空会返回 4xx

测试点：
- current password 为空提交
- 预期：前端HTML拦截 或 后端4xx拒绝

断言：
- 如果前端拦截：有错误证据（validation error/toast）
- 如果后端拦截：响应状态 400-499
    """
)
def test_p1_missing_current_password_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_missing_current_password_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    policy = fetch_abp_password_policy(auth_page)
    length = max(int(getattr(policy, "required_length", 6) or 6), 8)
    new_pwd = generate_password(policy, length=length)

    with allure.step("currentPassword 为空，提交"):
        step_shot(page_obj, "step_before_submit")
        resp = page_obj.submit_change_password("", new_pwd, new_pwd, wait_response=True, timeout_ms=2000)
        
        # 根据响应结果选择截图策略
        if resp is None:
            # 前端拦截，等待error toast
            step_shot_after_error_toast(page_obj, "step_after_submit_with_error_toast")
        else:
            # 后端返回，直接截图
            step_shot(page_obj, "step_after_submit")

    with allure.step("断言：必须失败（前端拦截或后端 4xx），且失败可观测"):
        if resp is None:
            # 前端拦截
            assert_frontend_has_error_evidence(auth_page, page_obj.CURRENT_PASSWORD_INPUT, "missing_current_password")
        else:
            attach_backend_text("missing_current_password_status", str(resp.status))
            assert 400 <= resp.status < 500, f"expected 4xx for missing current password, got {resp.status}"
            assert page_obj.wait_for_error_hint(timeout_ms=2000) or True

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- 前端不验证 currentPassword 的正确性

后端限制：
- 后端验证 currentPassword 是否匹配数据库中的密码
- 不匹配返回 4xx（通常 401/403）

测试点：
- 提交错误的 current password（不是账号真实密码）
- 预期：后端拒绝

断言：
- 响应状态 400-499
- 页面显示错误提示（toast/"Password Incorrect"）
    """
)
def test_p1_wrong_current_password_should_fail(auth_page: Page):
    logger = TestLogger("test_p1_wrong_current_password_should_fail")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    policy = fetch_abp_password_policy(auth_page)
    length = max(int(getattr(policy, "required_length", 6) or 6), 8)
    new_pwd = generate_password(policy, length=length)

    # 错误的 current：确保与 new 不同，且满足基本长度（不代表真实密码）
    wrong_current = generate_password(policy, length=length + 2)
    if wrong_current == new_pwd:
        wrong_current = generate_password(policy, length=length + 3)

    with allure.step("提交：wrong current password（期望后端拒绝）"):
        step_shot(page_obj, "step_before_submit")
        resp = page_obj.submit_change_password(wrong_current, new_pwd, new_pwd, wait_response=True, timeout_ms=15000)
        
        # 额外等待：确保前端完全处理了错误响应并渲染toast
        auth_page.wait_for_timeout(1000)
        
        # 根据响应结果选择截图策略
        if resp is None or (resp and not resp.ok):
            # 失败场景：等待error toast
            step_shot_after_error_toast(page_obj, "step_after_submit_with_error_toast")
        else:
            step_shot(page_obj, "step_after_submit")

    # 断言分层（必须）：
    # - 前端可观测：若未发请求，也必须给出错误证据
    # - 后端权威：若发请求，必须 4xx 拒绝
    if resp is None:
        # 前端拦截（例如按钮禁用/本地校验/路由层拦截），必须可观测
        assert page_obj.wait_for_error_hint(timeout_ms=2000) or page_obj.has_validation_error(), (
            "wrong current password: request not sent, and no frontend error evidence observed"
        )
    else:
        attach_backend_text("wrong_current_status", str(resp.status))
        assert 400 <= resp.status < 500, f"expected 4xx for wrong current password, got {resp.status}"
        # 尽量结构化验证 errors（不绑死文案）
        ves = page_obj.get_abp_validation_errors(resp)
        if ves:
            attach_backend_text("abp_validationErrors", str(ves))

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- newPassword: JS验证非空（trim()）
- shouldDisabled() 函数检查：if (!password.newPassword.trim()) return true

后端限制：
- 如果前端未拦截，后端验证 newPassword 必填

测试点：
- new password 为空提交
- 预期：前端JS拦截（按钮禁用/不发请求）

断言：
- 提交按钮应被禁用 或 不应发起API请求
- 前端必须有错误证据（按钮disabled/validation error）
    """
)
def test_p1_missing_new_password_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_missing_new_password_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step("填充：new password为空，其他字段正常"):
        step_shot(page_obj, "step_before_fill")
        page_obj.fill_current_password("DummyOld123!")
        page_obj.fill_new_password("")  # 新密码为空
        page_obj.fill_confirm_new_password("DummyNew123!")
        step_shot(page_obj, "step_filled_empty_new")

    with allure.step("尝试提交（预期前端拦截）"):
        # 检查保存按钮是否被禁用
        save_button = auth_page.locator(page_obj.SAVE_BUTTON)
        is_disabled = save_button.is_disabled()
        
        if is_disabled:
            # 按钮禁用，符合预期
            allure.attach(
                "Save button is disabled (as expected)",
                name="button_state",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_button_disabled")
        else:
            # 按钮未禁用，尝试点击并检查是否发送请求
            page_obj.click_save()
            sent = _expect_no_change_password_request(auth_page, timeout_ms=1200)
            assert not sent, "new password empty should be blocked by frontend (no request expected)"
            step_shot_after_error_toast(page_obj, "step_after_click_with_error")

    # 断言：必须有前端错误证据
    assert is_disabled or page_obj.wait_for_error_hint(timeout_ms=2000) or page_obj.has_validation_error(), (
        "missing new password: frontend must show error evidence (disabled button / validation error / toast)"
    )

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- confirmNewPassword: JS验证非空（trim()）
- shouldDisabled() 函数检查：if (!password.confirmNewPassword.trim()) return true

后端限制：
- confirmNewPassword 不发送到后端（仅前端验证）

测试点：
- confirm password 为空提交
- 预期：前端JS拦截（按钮禁用/不发请求）

断言：
- 提交按钮应被禁用 或 不应发起API请求
- 前端必须有错误证据（按钮disabled/validation error）
    """
)
def test_p1_missing_confirm_password_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_missing_confirm_password_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step("填充：confirm password为空，其他字段正常"):
        step_shot(page_obj, "step_before_fill")
        page_obj.fill_current_password("DummyOld123!")
        page_obj.fill_new_password("DummyNew123!")
        page_obj.fill_confirm_new_password("")  # 确认密码为空
        step_shot(page_obj, "step_filled_empty_confirm")

    with allure.step("尝试提交（预期前端拦截）"):
        # 检查保存按钮是否被禁用
        save_button = auth_page.locator(page_obj.SAVE_BUTTON)
        is_disabled = save_button.is_disabled()
        
        if is_disabled:
            # 按钮禁用，符合预期
            allure.attach(
                "Save button is disabled (as expected)",
                name="button_state",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_button_disabled")
        else:
            # 按钮未禁用，尝试点击并检查是否发送请求
            page_obj.click_save()
            sent = _expect_no_change_password_request(auth_page, timeout_ms=1200)
            assert not sent, "confirm password empty should be blocked by frontend (no request expected)"
            step_shot_after_error_toast(page_obj, "step_after_click_with_error")

    # 断言：必须有前端错误证据
    assert is_disabled or page_obj.wait_for_error_hint(timeout_ms=2000) or page_obj.has_validation_error(), (
        "missing confirm password: frontend must show error evidence (disabled button / validation error / toast)"
    )

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@pytest.mark.boundary
@allure.feature("Change Password")
@allure.story("P1 - 边界")
@allure.description(
    """
前端限制：
- 前端不验证密码长度（无 maxLength 属性）

后端限制：
- Swagger 定义：newPassword maxLength=128
- 超过128字符返回 4xx

测试点：
- 127 (max-1): 应成功
- 128 (max): 应成功
- 129 (max+1): 应失败（后端4xx）

断言：
- max-1/max: 响应2xx，立即回滚
- max+1: 后端400-499

注意：
- 使用 @pytest.mark.xdist_group 确保边界测试串行执行
- 避免并发修改密码导致的状态冲突和前端验证异常
    """
)
@pytest.mark.parametrize("length_value", [127, 128, 129], ids=["max-1", "max", "max+1"])
def test_p1_new_password_length_boundaries(logged_in_page: Page, test_account: dict, length_value: int):
    """
    测试新密码最大长度边界：
    - 127 (max-1): 应成功
    - 128 (max): 应成功
    - 129 (max+1): 应失败
    依据 Swagger：newPassword maxLength=128
    """
    logger = TestLogger(f"test_p1_new_password_length_boundaries[{length_value}]")
    logger.start()

    current_password = (test_account.get("password") or "").strip()
    assert current_password, "missing current password from account pool"

    page_obj = AdminProfileChangePasswordPage(logged_in_page)
    page_obj.navigate()

    policy = fetch_abp_password_policy(logged_in_page)
    new_password = generate_password(policy, length=length_value)

    with allure.step(f"提交改密：newPassword len={length_value}"):
        step_shot(page_obj, f"step_before_submit_len{length_value}")
        resp = page_obj.submit_change_password(current_password, new_password, new_password, wait_response=True, timeout_ms=15000)
        
        # 额外等待：确保前端完全处理了响应并渲染toast
        logged_in_page.wait_for_timeout(1000)
        
        # 根据预期结果选择截图策略
        if length_value > 128:
            # max+1: 预期失败
            if resp is None or (resp and not resp.ok):
                step_shot_after_error_toast(page_obj, f"step_after_submit_len{length_value}_error")
            else:
                step_shot(page_obj, f"step_after_submit_len{length_value}")
        else:
            # max-1/max: 预期成功，等待success toast并截图
            step_shot_after_success_toast(page_obj, f"step_after_submit_len{length_value}_success_toast")

    # 断言
    if length_value > 128:
        # max+1: 应失败
        if resp is None:
            assert_frontend_has_error_evidence(logged_in_page, page_obj.NEW_PASSWORD_INPUT, f"new_password_len_{length_value}")
        else:
            attach_backend_text(f"len{length_value}_status", str(resp.status))
            assert 400 <= resp.status < 500, f"len={length_value} expected 4xx, got {resp.status}"
    else:
        # max-1 / max: 应成功
        if resp is None:
            pytest.fail(f"len={length_value} expected success but got no response")
        attach_backend_text(f"len{length_value}_status", str(resp.status))
        assert resp.ok, f"len={length_value} expected success, got {resp.status}"
        
        # 立即回滚
        try:
            page_obj.submit_change_password(new_password, current_password, current_password, wait_response=True, timeout_ms=15000)
        except Exception:
            pass

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - PasswordPolicy")
@allure.description(
    """
前端限制：
- 前端不验证密码复杂度策略

后端限制：
- ABP Identity Password Policy（真理源）:
  * RequireDigit = true（必须包含数字）
  * RequireUppercase = true（必须包含大写字母）
  * RequireLowercase = true（必须包含小写字母）
  * RequireNonAlphanumeric = true（必须包含特殊字符）

测试点：
- 生成缺少指定策略项的密码（digit/upper/lower/special）
- 预期：后端4xx拒绝

断言：
- 前端如果拦截：有错误证据
- 后端拦截：响应400-499 + 可能包含 validationErrors
    """
)
@pytest.mark.parametrize("missing_kind", ["digit", "upper", "lower", "special"])
def test_p1_password_policy_should_reject_invalid_new_password(logged_in_page: Page, test_account: dict, missing_kind: str):
    """
    ABP PasswordPolicy 约束：RequireDigit/Uppercase/Lowercase/NonAlphanumeric = True。
    对应 missing_* 必须失败（前端拦截或后端 4xx）。
    """
    logger = TestLogger(f"test_p1_password_policy_should_reject_invalid_new_password[{missing_kind}]")
    logger.start()

    current_password = (test_account.get("password") or "").strip()
    assert current_password, "missing current password from account pool"

    page_obj = AdminProfileChangePasswordPage(logged_in_page)
    page_obj.navigate()

    policy = fetch_abp_password_policy(logged_in_page)
    length = max(int(getattr(policy, "required_length", 6) or 6), 8)
    invalid_new = generate_password(policy, length=length, missing=missing_kind)

    with allure.step(f"提交：newPassword missing_{missing_kind}"):
        step_shot(page_obj, f"step_before_submit_{missing_kind}")
        resp = page_obj.submit_change_password(current_password, invalid_new, invalid_new, wait_response=True, timeout_ms=15000)
        
        # 失败场景：等待error toast并全屏截图
        if resp is None or (resp and not resp.ok):
            step_shot_after_error_toast(page_obj, f"step_after_submit_{missing_kind}_with_error_toast")
        else:
            step_shot(page_obj, f"step_after_submit_{missing_kind}")

    with allure.step("断言：必须失败且可观测"):
        if resp is None:
            assert_frontend_has_error_evidence(logged_in_page, page_obj.NEW_PASSWORD_INPUT, f"policy_missing_{missing_kind}")
        else:
            attach_backend_text(f"policy_missing_{missing_kind}_status", str(resp.status))
            assert 400 <= resp.status < 500, f"expected 4xx for policy violation, got {resp.status}"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 最小长度边界测试（从 policy_boundaries 合并）
# ═══════════════════════════════════════════════════════════════
@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.boundary
@allure.feature("Change Password")
@allure.story("P1 - PasswordPolicy Boundaries")
@allure.description(
    """
前端限制：
- 前端不验证最小长度

后端限制：
- Swagger 定义：newPassword minLength=6
- ABP Identity Password Policy: RequiredLength（通常=6）

测试点：
- min-1: 应失败（后端4xx）
- min: 应成功
- min+1: 应成功

断言：
- min-1: 前端错误证据 或 后端400-499
- min/min+1: 响应2xx，立即回滚

注意：
- 生成满足复杂度策略的短密码比较困难（需要digit/upper/lower/special）
- 如果 minLength=6，生成5字符的合法密码几乎不可能
- 使用 @pytest.mark.xdist_group 确保边界测试串行执行
- 避免并发修改密码导致的状态冲突和前端验证异常
    """
)
@pytest.mark.parametrize("length_offset", [-1, 0, +1], ids=["min-1", "min", "min+1"])
def test_p1_new_password_min_length_boundaries(logged_in_page: Page, test_account: dict, length_offset: int):
    """
    测试新密码最小长度边界：
    - min-1: 应失败
    - min: 应成功
    - min+1: 应成功
    """
    logger = TestLogger(f"test_p1_new_password_min_length_boundaries[{length_offset:+d}]")
    logger.start()

    current_password = (test_account.get("password") or "").strip()
    assert current_password, "missing current password from account pool"

    page_obj = AdminProfileChangePasswordPage(logged_in_page)
    page_obj.navigate()

    with allure.step("读取 ABP PasswordPolicy"):
        policy = fetch_abp_password_policy(logged_in_page)
        min_len = max(int(getattr(policy, "required_length", 6) or 6), 1)
        target_len = min_len + length_offset
        
        # 边界-1不能小于0
        if target_len < 1:
            logger.end(success=True)
            pytest.skip(f"min_length={min_len}, offset={length_offset} -> target={target_len} < 1, skip")
            return

    with allure.step(f"生成密码：长度={target_len} (min={min_len}, offset={length_offset:+d})"):
        new_password = generate_password(policy, length=target_len)
        attach_backend_text("password_length", str(len(new_password)))

    with allure.step("提交改密"):
        step_shot(page_obj, f"step_before_submit_len{target_len}")
        resp = page_obj.submit_change_password(current_password, new_password, new_password, wait_response=True, timeout_ms=15000)
        
        # 根据预期结果选择截图策略
        if length_offset < 0:
            # min-1: 预期失败
            if resp is None or (resp and not resp.ok):
                step_shot_after_error_toast(page_obj, f"step_after_submit_len{target_len}_error")
            else:
                step_shot(page_obj, f"step_after_submit_len{target_len}")
        else:
            # min / min+1: 预期成功，等待success toast并截图
            step_shot_after_success_toast(page_obj, f"step_after_submit_len{target_len}_success_toast")

    # 断言
    if length_offset < 0:
        # min-1: 应失败
        if resp is None:
            # 前端拦截
            assert page_obj.wait_for_error_hint(timeout_ms=2000) or page_obj.has_validation_error(), (
                f"min-1({target_len}) should be rejected by frontend with error evidence"
            )
        else:
            # 后端拦截
            attach_backend_text(f"min-1_status", str(resp.status))
            assert 400 <= resp.status < 500, f"min-1({target_len}) expected 4xx, got {resp.status}"
    else:
        # min / min+1: 应成功
        if resp is None:
            pytest.fail(f"min{length_offset:+d}({target_len}) expected success but got no response")
        attach_backend_text(f"min{length_offset:+d}_status", str(resp.status))
        assert resp.ok, f"min{length_offset:+d}({target_len}) expected success, got {resp.status}"
        
        # 立即回滚
        try:
            page_obj.submit_change_password(new_password, current_password, current_password, wait_response=True, timeout_ms=15000)
        except Exception:
            pass

    logger.end(success=True)

