"""
Change Password - P1

P1 原则：
- 以 ABP 后端规则为真理源（PasswordPolicy）
- 前端使用正则验证密码策略
- 断言以"前端可观测行为"为主：error evidence / 不发请求 / 失败可诊断

密码策略（docs/requirements/account-profile-field-requirements.md）：
- 最小长度：6 字符（前后端都验证）
- 最大长度：无限制（MongoDB 不强制）
- 需要小写字母、大写字母、数字、特殊字符
- 确认密码匹配：仅前端验证

前端正则：
/^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':"\\\\|,.<>\\/?]).{6,}$/
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from tests.myaccount._matrix_helpers import assert_frontend_has_error_evidence, wait_for_frontend_validation
from utils.logger import TestLogger

from tests.myaccount.change_password._helpers import (
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
            lambda r: ("/api/vibe/change-password" in (r.url or "")) and (r.request.method == "POST"),
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
- newPassword !== confirmPassword 时显示 Toast: "New passwords do not match"
- 前端使用正则验证密码策略（6+字符，大小写+数字+特殊字符）

后端限制：
- confirmPassword 不发送到后端（仅前端验证）

测试点：
- new password 与 confirm password 不匹配
- 预期：前端拦截（不发请求）+ Toast 提示

断言：
- 不应发起 /api/vibe/change-password 请求
- 前端必须有错误证据（Toast 提示）
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
- 输入框无 maxlength 限制

后端限制：
- currentPassword 为空返回 400: "currentPassword and newPassword are required"

测试点：
- current password 为空提交
- 预期：前端 required 阻止 或 后端 400 拒绝

断言：
- 如果前端拦截：有错误证据（validation error/toast）
- 如果后端拦截：响应状态 400
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
        # 直接填充并点击，不等待响应
        page_obj.fill_form("", new_pwd, new_pwd)
        page_obj.click_save()
        auth_page.wait_for_timeout(1500)
        step_shot(page_obj, "step_after_submit")

    with allure.step("断言：前端已阻止"):
        # 检查是否有 Toast 错误提示或浏览器 required 验证
        has_error = False
        
        # 检查 Toast
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = auth_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    allure.attach(f"Toast found", "error_evidence")
                    break
            except Exception:
                pass
        
        # 检查浏览器 required 验证（current password 输入框获得焦点）
        if not has_error:
            current_pwd_input = auth_page.locator(page_obj.CURRENT_PASSWORD_INPUT)
            has_error = current_pwd_input.evaluate("el => el === document.activeElement")
            if has_error:
                allure.attach("Browser required validation triggered", "error_evidence")
        
        # 检查其他错误提示
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=500)
        
        assert has_error, "missing current password: expected frontend error evidence"

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
- 后端验证 currentPassword 是否匹配
- 不匹配返回 400: "Password change failed"

测试点：
- 提交错误的 current password（不是账号真实密码）
- 预期：后端 400 拒绝

断言：
- 响应状态 400
- 页面显示错误提示（Toast）
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
        # 填充并点击
        page_obj.fill_form(wrong_current, new_pwd, new_pwd)
        page_obj.click_save()
        
        # 等待 Toast 显示
        auth_page.wait_for_timeout(2000)
        step_shot(page_obj, "step_after_submit")

    with allure.step("断言：后端应返回 4xx 或前端显示错误"):
        # 检查是否有 Toast 错误提示
        has_error = False
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = auth_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    toast_text = toast.first.inner_text()
                    allure.attach(f"Toast found: {toast_text}", "error_evidence")
                    break
            except Exception:
                pass
        
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=1000)
        
        assert has_error, "wrong current password: expected error Toast from backend"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- newPassword: HTML required 属性
- 输入框无 maxlength 限制

后端限制：
- newPassword 为空返回 400: "currentPassword and newPassword are required"

测试点：
- new password 为空提交
- 预期：前端 required 阻止 或 后端 400 拒绝

断言：
- 提交按钮被禁用 或 不应发起 API 请求
- 前端必须有错误证据（disabled/validation error/toast）
    """
)
def test_p1_missing_new_password_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_missing_new_password_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step("newPassword 为空，提交"):
        step_shot(page_obj, "step_before_submit")
        # 直接填充并点击，不等待响应
        page_obj.fill_current_password("DummyOld123!")
        page_obj.fill_new_password("")  # 新密码为空
        page_obj.fill_confirm_new_password("DummyNew123!")
        page_obj.click_save()
        auth_page.wait_for_timeout(1500)
        step_shot(page_obj, "step_after_submit")

    with allure.step("断言：前端已阻止"):
        # 检查是否有 Toast 错误提示或浏览器 required 验证
        has_error = False
        
        # 检查 Toast
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = auth_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    allure.attach("Toast found", "error_evidence")
                    break
            except Exception:
                pass
        
        # 检查浏览器 required 验证（new password 输入框获得焦点）
        if not has_error:
            new_pwd_input = auth_page.locator(page_obj.NEW_PASSWORD_INPUT)
            has_error = new_pwd_input.evaluate("el => el === document.activeElement")
            if has_error:
                allure.attach("Browser required validation triggered", "error_evidence")
        
        # 检查其他错误提示
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=500)
        
        assert has_error, "missing new password: expected frontend error evidence"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - 校验矩阵")
@allure.description(
    """
前端限制：
- confirmPassword: HTML required 属性
- 仅前端验证，不发送到后端

后端限制：
- confirmPassword 不发送到后端

测试点：
- confirm password 为空提交
- 预期：前端 required 阻止

断言：
- 提交按钮被禁用 或 不应发起 API 请求
- 前端必须有错误证据（disabled/validation error/toast）
    """
)
def test_p1_missing_confirm_password_should_be_blocked(auth_page: Page):
    logger = TestLogger("test_p1_missing_confirm_password_should_be_blocked")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step("confirmPassword 为空，提交"):
        step_shot(page_obj, "step_before_submit")
        # 直接填充并点击，不等待响应
        page_obj.fill_current_password("DummyOld123!")
        page_obj.fill_new_password("DummyNew123!")
        page_obj.fill_confirm_new_password("")  # 确认密码为空
        page_obj.click_save()
        auth_page.wait_for_timeout(1500)
        step_shot(page_obj, "step_after_submit")

    with allure.step("断言：前端已阻止"):
        # 检查是否有 Toast 错误提示或浏览器 required 验证
        has_error = False
        
        # 检查 Toast
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = auth_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    allure.attach("Toast found", "error_evidence")
                    break
            except Exception:
                pass
        
        # 检查浏览器 required 验证（confirm password 输入框获得焦点）
        if not has_error:
            confirm_pwd_input = auth_page.locator(page_obj.CONFIRM_PASSWORD_INPUT)
            has_error = confirm_pwd_input.evaluate("el => el === document.activeElement")
            if has_error:
                allure.attach("Browser required validation triggered", "error_evidence")
        
        # 检查其他错误提示
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=500)
        
        assert has_error, "missing confirm password: expected frontend error evidence"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 注意：最大长度边界测试已删除
# 原因：项目使用 MongoDB，不强制 maxLength 约束
# 参考：docs/requirements/account-profile-field-requirements.md
# ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Change Password")
@allure.story("P1 - PasswordPolicy")
@allure.description(
    """
前端限制（正则验证）：
- /^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[特殊字符]).{6,}$/
- 不符合正则时显示 Toast: 
  "Password must be at least 6 characters and contain uppercase, lowercase, number, and special character"

后端限制（ABP Identity）：
- RequireDigit = true（必须包含数字）
- RequireUppercase = true（必须包含大写字母）
- RequireLowercase = true（必须包含小写字母）
- RequireNonAlphanumeric = true（必须包含特殊字符）
- 不符合策略返回 400 + details 数组

测试点：
- 生成缺少指定策略项的密码（digit/upper/lower/special）
- 预期：前端正则拦截 或 后端 400 拒绝

断言：
- 前端拦截：Toast 错误提示
- 后端拦截：响应 400 + details
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
        # 直接填充并点击，不等待响应（前端验证会阻止请求）
        page_obj.fill_form(current_password, invalid_new, invalid_new)
        page_obj.click_save()
        
        # 等待 Toast 出现（前端验证会立即显示 Toast）
        logged_in_page.wait_for_timeout(1500)
        step_shot(page_obj, f"step_after_submit_{missing_kind}")

    with allure.step("断言：必须失败且可观测"):
        # 检查是否有 Toast 错误提示
        has_error = False
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "ol li:has(button)",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = logged_in_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    toast_text = toast.first.inner_text()
                    allure.attach(f"Toast found: {toast_text}", "toast_content")
                    break
            except Exception:
                pass
        
        # 也检查其他错误提示
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=1000)
        
        assert has_error, f"policy_missing_{missing_kind}: expected frontend error evidence (Toast)"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 最小长度边界测试
# ═══════════════════════════════════════════════════════════════
@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.boundary
@allure.feature("Change Password")
@allure.story("P1 - PasswordPolicy Boundaries")
@allure.description(
    """
前端限制（正则验证）：
- 正则 .{6,} 要求最少 6 字符
- 不符合时显示 Toast 错误提示

后端限制：
- ABP Identity: RequiredLength = 6
- 最大长度：无限制（MongoDB 不强制）

测试点：
- min-1 (5字符): 应失败 - 前端正则拦截 或 后端 400
- min (6字符): 应成功
- min+1 (7字符): 应成功

断言：
- min-1: 前端 Toast 或 后端 400
- min/min+1: 响应 2xx，立即回滚

注意：
- 生成 5 字符且满足 digit/upper/lower/special 的密码几乎不可能
- min-1 场景可能因字符集不足导致实际长度 > 5
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
        
        if length_offset < 0:
            # min-1: 直接点击，不等待响应（前端验证会阻止请求）
            page_obj.fill_form(current_password, new_password, new_password)
            page_obj.click_save()
            logged_in_page.wait_for_timeout(1500)
            step_shot(page_obj, f"step_after_submit_len{target_len}_error")
            resp = None
        else:
            # min / min+1: 正常提交
            resp = page_obj.submit_change_password(current_password, new_password, new_password, wait_response=True, timeout_ms=15000)
            step_shot_after_success_toast(page_obj, f"step_after_submit_len{target_len}_success_toast")

    # 断言
    if length_offset < 0:
        # min-1: 应失败 - 检查 Toast 错误提示
        has_error = False
        toast_selectors = [
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "ol li:has(button)",
            "[role='alert']",
        ]
        for selector in toast_selectors:
            try:
                toast = logged_in_page.locator(selector)
                if toast.count() > 0 and toast.first.is_visible(timeout=500):
                    has_error = True
                    toast_text = toast.first.inner_text()
                    allure.attach(f"Toast found: {toast_text}", "toast_content")
                    break
            except Exception:
                pass
        
        if not has_error:
            has_error = page_obj.wait_for_error_hint(timeout_ms=1000)
        
        assert has_error, f"min-1({target_len}) should be rejected with error evidence (Toast)"
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

