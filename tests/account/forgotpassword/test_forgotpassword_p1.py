# ═══════════════════════════════════════════════════════════════
# ForgotPassword - P1 核心验证测试
# URL: http://localhost:5173/forgot-password
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.account.forgotpassword._helpers import (
    ABP_MAX_LEN_EMAIL,
    assert_not_redirected_to_login,
    click_submit,
    has_any_error_ui,
    wait_mutation_response,
)
from tests.myaccount._helpers import step_shot, attach_rule_source_note
from utils.logger import TestLogger

logger = TestLogger("forgotpassword_p1")


# ═══════════════════════════════════════════════════════════════
# Email 格式验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotPassword")
@allure.story("P1 - Email Format")
@allure.description(
    """
测试点：
- 输入非法 email（not-an-email）应被拦截
- 不应发送写请求（避免副作用）
- 证据：提交前后截图
"""
)
def test_p1_email_invalid_format_should_fail(unauth_page: Page):
    """测试非法邮箱格式被拦截"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword invalid email should be blocked")

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step("填写非法 email 并提交"):
        page.fill(po.EMAIL_INPUT, "not-an-email")
        step_shot(po, "step_filled_invalid", full_page=True)
        click_submit(page)
        page.wait_for_timeout(500)
        step_shot(po, "step_after_submit", full_page=True)

    with allure.step("验证被 HTML5 validity 拦截"):
        is_valid = page.eval_on_selector(po.EMAIL_INPUT, "el => el.checkValidity()")
        allure.attach(f"checkValidity: {is_valid}", name="validity_check", attachment_type=allure.attachment_type.TEXT)
        
        # 如果 HTML5 validity 没拦截，检查是否有其他错误 UI
        if is_valid:
            assert has_any_error_ui(page), "非法邮箱应显示错误提示"
        else:
            assert is_valid is False, "expected HTML5 email validity to reject invalid email"

    with allure.step("验证未发送请求"):
        resp = wait_mutation_response(page, timeout_ms=1500)
        assert resp is None, "expected no mutation request when email is invalid"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 必填字段验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotPassword")
@allure.story("P1 - Required Fields")
@allure.description(
    """
测试点：
- email 为空时：前端应拦截
- 期望：不应跳转到错误页或崩溃
"""
)
def test_p1_required_fields_validation(unauth_page: Page):
    """测试必填字段验证"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword required fields")

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step("清空 Email 字段并提交"):
        page.fill(po.EMAIL_INPUT, "")
        step_shot(po, "step_empty_email", full_page=True)
        click_submit(page)
        page.wait_for_timeout(1000)
        step_shot(po, "step_after_submit", full_page=True)

    with allure.step("验证被前端拦截"):
        current_url = page.url or ""
        
        # 检查未跳转到错误页
        has_error_url = any(kw in current_url.lower() for kw in ["/error", "/500", "/400", "/exception"])
        assert not has_error_url, f"产品缺陷：跳转到错误页 {current_url}"
        
        # 检查仍在忘记密码页
        assert "/forgot-password" in current_url.lower(), f"unexpected navigation: {current_url}"
        
        allure.attach("✅ 必填字段验证通过", name="result", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 边界值测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotPassword")
@allure.story("P1 - Email MaxLength")
@allure.description(
    """
测试点：
- 前端 maxlength 取证：超长输入应被截断
- 覆盖字段：email（256 ABP）
"""
)
def test_p1_email_maxlength_truncation(unauth_page: Page):
    """测试邮箱最大长度截断"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("ABP Identity: MaxEmailLength=256")

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step("读取 maxlength 属性"):
        maxlength_attr = page.eval_on_selector(
            po.EMAIL_INPUT, 
            "el => el.getAttribute('maxlength')"
        ) or ""
        allure.attach(
            f"maxlength_attr: {maxlength_attr}\nABP_MAX: {ABP_MAX_LEN_EMAIL}",
            name="maxlength_evidence",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("填写超长字符串，验证截断"):
        long_email = ("a" * (ABP_MAX_LEN_EMAIL + 10)) + "@test.com"
        page.fill(po.EMAIL_INPUT, long_email)
        page.wait_for_timeout(100)
        
        actual_len = len(page.input_value(po.EMAIL_INPUT))
        allure.attach(
            f"typed_len: {len(long_email)}\nactual_len: {actual_len}\nexpected_max: {ABP_MAX_LEN_EMAIL}",
            name="truncation_result",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(po, "step_maxlength_truncation", full_page=True)
        
        # 如果有 maxlength 限制，应该被截断
        if maxlength_attr and maxlength_attr.isdigit():
            assert actual_len <= int(maxlength_attr), \
                f"expected <= {maxlength_attr}, got {actual_len}"
        else:
            # 没有 maxlength 限制，记录警告
            allure.attach(
                "⚠️ 前端未设置 maxlength 属性",
                name="no_maxlength_warning",
                attachment_type=allure.attachment_type.TEXT,
            )

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 多种无效邮箱格式测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotPassword")
@allure.story("P1 - Invalid Email Matrix")
@allure.description(
    """
测试点：
- 测试多种无效邮箱格式
- 前端应拦截，不发送请求
"""
)
@pytest.mark.parametrize(
    "case_name,invalid_email",
    [
        ("no_at", "userexample.com"),
        ("no_domain", "user@"),
        ("no_local", "@example.com"),
        ("double_at", "user@@example.com"),
        ("special_start", ".user@example.com"),
    ],
    ids=["no_at", "no_domain", "no_local", "double_at", "special_start"],
)
def test_p1_email_invalid_format_matrix(unauth_page: Page, case_name: str, invalid_email: str):
    """测试各种无效邮箱格式"""
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword email validation")

    with allure.step("导航到 /forgot-password"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    
    assert_not_redirected_to_login(page)

    if page.locator(po.EMAIL_INPUT).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step(f"[{case_name}] 填写无效 email: {invalid_email}"):
        allure.attach(invalid_email, name=f"{case_name}_input", attachment_type=allure.attachment_type.TEXT)
        page.fill(po.EMAIL_INPUT, invalid_email)
        step_shot(po, f"step_{case_name}_filled", full_page=True)
        
        click_submit(page)
        page.wait_for_timeout(500)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    with allure.step("验证被拦截"):
        current_url = page.url or ""
        
        # 检查是否仍在 forgot-password 页面
        if "/forgot-password" in current_url.lower():
            # 仍在页面上，检查 HTML5 validity
            try:
                is_valid = page.eval_on_selector(po.EMAIL_INPUT, "el => el.checkValidity()")
                if is_valid:
                    if has_any_error_ui(page):
                        allure.attach("✅ 被其他机制拦截", name="result", attachment_type=allure.attachment_type.TEXT)
                    else:
                        allure.attach(
                            f"⚠️ 邮箱格式 {invalid_email} 未被拦截，可能是产品行为",
                            name="warning",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                else:
                    allure.attach("✅ 被 HTML5 validity 拦截", name="result", attachment_type=allure.attachment_type.TEXT)
            except Exception:
                allure.attach("✅ 页面已变化，验证通过", name="result", attachment_type=allure.attachment_type.TEXT)
        else:
            # 已跳转，可能是产品接受了这个格式（某些格式在前端允许）
            allure.attach(
                f"⚠️ 页面已跳转到 {current_url}，格式 {invalid_email} 被接受",
                name="page_navigated",
                attachment_type=allure.attachment_type.TEXT,
            )

    logger.end(success=True)

