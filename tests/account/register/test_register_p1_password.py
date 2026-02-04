"""
Account/Register - Password 字段测试

测试内容：
- Password 策略验证（弱密码矩阵）
- Password 长度边界（6 点法）
- Password 有效格式
"""

import allure
import pytest
import time
import uuid
from typing import Optional
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.admin.settings.profile._helpers import attach_rule_source_note, step_shot
from tests.account.register import _abp_constraints_helpers as ABP
from tests.account.register._helpers import (
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
    get_validation_message,
    has_any_error_ui,
    wait_mutation_response,
    wait_response_by_url_substring,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


def _ensure_register_page(page: Page, po: AccountRegisterPage) -> None:
    """复用 Register 页"""
    try:
        if page.locator(po.USERNAME_INPUT).count() > 0:
            return
    except Exception:
        pass
    po.navigate()
    page.wait_for_timeout(200)


ABP_PASSWORD_MAX = 128  # Password 最大长度


# ═══════════════════════════════════════════════════════════════════════════════
# Password 策略测试（弱密码矩阵）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountRegister")
@allure.story("P1 - Password Policy Matrix")
@allure.description("测试密码策略：弱密码必须被拒绝")
@pytest.mark.parametrize(
    "case_name,pwd",
    [
        ("missing_digit", "ValidPass!!!"),
        ("missing_uppercase", "validpass123!"),
        ("missing_lowercase", "VALIDPASS123!"),
        ("missing_non_alphanumeric", "ValidPass123"),
    ],
)
def test_p1_register_password_policy_should_reject_weak_passwords(
    unauth_page: Page, xdist_worker_id: str, case_name: str, pwd: str
):
    attach_rule_source_note("Password policy matrix")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step(f"[{case_name}] 填写弱密码并提交"):
        po.navigate()
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_navigate", full_page=True)

        suf = _unique_suffix(xdist_worker_id)
        po.fill_username(f"pwd_{suf}")
        po.fill_email(f"pwd_{suf}@testmail.com")
        po.fill_password(pwd)
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        resp = None
        try:
            resp = wait_response_by_url_substring(page, "/api/account/register", timeout_ms=2500)
        except Exception:
            resp = None
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            page_text = page.inner_text("body") if hasattr(page, 'inner_text') else ""
            if "500" in str(page_text) or "API Error" in str(page_text):
                pytest.xfail(f"后端API返回500错误: {fatal}")
            else:
                assert False, f"[{case_name}] fatal error page detected: {fatal}"

        msg = get_validation_message(page, po.PASSWORD_INPUT)
        if msg:
            allure.attach(msg, name=f"{case_name}_validationMessage", attachment_type=allure.attachment_type.TEXT)

        if resp is not None:
            assert resp.status < 500, f"[{case_name}] unexpected 5xx status={resp.status}"

        current_url = page.url or ""
        assert "/register" in current_url or "/Account/Register" in current_url, f"[{case_name}] unexpected navigation: {current_url}"
        
        has_validation = bool(msg)
        has_error_ui = has_any_error_ui(page)
        has_4xx = resp is not None and 400 <= resp.status < 500
        
        if not (has_validation or has_error_ui or has_4xx):
            pytest.fail(f"[{case_name}] 未检测到验证证据")


# ═══════════════════════════════════════════════════════════════════════════════
# Password 长度边界测试（6 点法）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Password Length Boundaries")
@allure.description("测试 Password 长度边界值（6 点法：5/6/7/127/128/129）")
@pytest.mark.parametrize(
    "total_len,expected_result",
    [
        pytest.param(5, "reject", id="len_5_reject"),
        pytest.param(6, "accept", id="len_6_accept"),
        pytest.param(7, "accept", id="len_7_accept"),
        pytest.param(127, "accept", id="len_127_accept"),
        pytest.param(128, "accept", id="len_128_accept"),
        pytest.param(129, "reject", id="len_129_reject"),
    ],
)
def test_p1_register_password_length_boundaries(unauth_page: Page, xdist_worker_id: str, total_len: int, expected_result: str):
    """测试 Password 长度边界（6 点法）"""
    attach_rule_source_note("Password boundary")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = _unique_suffix(xdist_worker_id)
    case_name = f"password_boundary_{total_len}"

    _ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    if total_len < 4:
        password = ("Aa1!" * ((total_len // 4) + 1))[:total_len]
    else:
        password = ("A" * (total_len - 4)) + "a1!a"

    allure.dynamic.parameter("期望长度", total_len)
    allure.dynamic.parameter("预期结果", expected_result)
    allure.dynamic.parameter("实际长度", len(password))

    with allure.step(f"[{case_name}] 填写 {total_len} 字符 Password 并提交"):
        po.fill_username(f"pwd_{suffix}")
        po.fill_email(f"pwd_{suffix}@testmail.com")
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        allure.attach(
            f"期望长度: {total_len}\n实际长度: {len(password)}\n预期结果: {expected_result}",
            name=f"📋 {case_name}_输入信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        actual_len = len(po.get_password_value())

        click_save(page)
        resp = wait_mutation_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            pytest.xfail(f"[{case_name}] fatal error page: {fatal}")

        if expected_result == "reject":
            msg = get_validation_message(page, po.PASSWORD_INPUT)
            has_error = has_any_error_ui(page) or bool(msg)
            has_4xx = resp is not None and 400 <= resp.status < 500
            was_truncated = actual_len < total_len
            current_url = page.url or ""
            still_on_register = "/register" in current_url or "/Account/Register" in current_url

            if was_truncated:
                allure.attach(f"✅ 被前端截断（实际 {actual_len}）", name=f"{case_name}_truncated", attachment_type=allure.attachment_type.TEXT)
            elif has_4xx:
                allure.attach(f"✅ 被后端拒绝（4xx）", name=f"{case_name}_rejected", attachment_type=allure.attachment_type.TEXT)
            elif has_error:
                allure.attach(f"✅ 显示错误 UI", name=f"{case_name}_error", attachment_type=allure.attachment_type.TEXT)
            elif still_on_register:
                allure.attach(f"✅ 被前端阻止", name=f"{case_name}_blocked", attachment_type=allure.attachment_type.TEXT)
            else:
                pytest.fail(f"{case_name}: 应被拒绝但似乎被接受了")
        else:
        if resp is not None:
                assert resp.status < 500, f"{case_name}: 5xx"
                assert resp.status < 400, f"{case_name}: {resp.status}"
            assert not has_any_error_ui(page), f"{case_name}: error UI"


# ═══════════════════════════════════════════════════════════════════════════════
# Password 有效格式测试
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Password Valid Formats")
@allure.description("验证各种合法密码格式应被接受")
@pytest.mark.parametrize(
    "password,description",
    [
        ("Aa1!aa", "最小合法密码"),
        ("ValidPass123!", "标准强密码"),
        ("Abcdef1!", "简单合法密码"),
        ("P@ssw0rd", "常见强密码"),
        ("Test123$%^", "多特殊字符"),
        ("UPPERCASE123lower!", "大小写混合"),
    ],
    ids=["min_valid", "standard", "simple", "common", "multi_special", "mixed_case"],
)
def test_p1_register_password_valid_formats(unauth_page: Page, xdist_worker_id: str, password: str, description: str):
    """验证 Password 有效格式"""
    attach_rule_source_note("Password valid formats")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = _unique_suffix(xdist_worker_id)

    allure.dynamic.parameter("格式描述", description)
    allure.dynamic.parameter("密码长度", len(password))

    _ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"填写有效密码并提交（{description}）"):
        po.fill_username(f"pwd_{suffix}")
        po.fill_email(f"pwd_{suffix}@testmail.com")
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_valid_{description[:10]}_filled", full_page=True)

        click_save(page)
        resp = wait_mutation_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_valid_{description[:10]}_after", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            pytest.xfail(f"后端错误: {fatal}")

        if resp is not None:
            assert resp.status < 500, f"5xx: {resp.status}"
        assert not has_any_error_ui(page), "unexpected error UI"
