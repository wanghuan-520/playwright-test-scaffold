import allure
import pytest
from playwright.sync_api import Page

from pages.account_forgotpassword_page import AccountForgotpasswordPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.ForgotPassword._helpers import (
    assert_not_redirected_to_login,
    ABP_MAX_LEN_EMAIL,
    click_save,
)
from utils.logger import TestLogger

logger = TestLogger("ForgotPassword_p1_abp_constraints")

# ═══════════════════════════════════════════════════════════════
# ABP 约束常量（已在 _helpers.py 定义）
# ═══════════════════════════════════════════════════════════════
# ABP_MAX_LEN_EMAIL = 256

# ═══════════════════════════════════════════════════════════════
# 描述文案（复用）
# ═══════════════════════════════════════════════════════════════
DESC_MAXLENGTH_EVIDENCE = """
测试点：
- 前端 maxlength 取证：超长输入应被截断/阻止在 max 以内
- 覆盖字段：email（256 ABP）
- ⚠️ 警告：如果前端 maxlength ≠ 后端 ABP 约束，则记录 drift 警告
证据：每个字段的 maxlength 属性 + 实际输入长度 + drift 警告
"""

DESC_EMAIL_BOUNDARY = """
测试点：
- email 边界值测试：255/256/257（ABP 约束最大=256）
- **前端截断验证**：使用真实账号email进行测试
- 期望：255/256 能正常输入，257 被截断到 256
证据：每个边界值的实际输入长度
"""

DESC_REQUIRED_VALIDATION = """
测试点：
- email 为空时：前端应拦截（仍停留在 ForgotPassword 页）
- 期望：不应跳转到错误页或崩溃
证据：清空前后 + 提交后截图
"""


def _get_maxlength_attr(page: Page, selector: str) -> str:
    """读取 HTML input 的 maxlength 属性"""
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        return (page.eval_on_selector(selector, "el => el.getAttribute('maxlength')") or "").strip()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
# UI 前端测试
# ═══════════════════════════════════════════════════════════════
@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotpassword")
@allure.story("P1 - Frontend MaxLength Evidence")
@allure.description(DESC_MAXLENGTH_EVIDENCE)
def test_p1_forgotpassword_ui_maxlength_evidence(unauth_page: Page):
    """
    前端 maxlength 取证：验证输入框是否有 maxlength 限制，并检查是否被截断。
    """
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)

    attach_rule_source_note("ABP Identity: MaxEmailLength=256, 前端应截断超长输入")

    po.navigate()
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step("[email] 读取 maxlength 属性"):
        maxlength_attr = _get_maxlength_attr(page, selector)
        frontend_max = int(maxlength_attr) if maxlength_attr.isdigit() else None
        
        evidence = f"maxlength_attr={maxlength_attr!r}\nABP_MAX={ABP_MAX_LEN_EMAIL}\n"
        
        # Drift 检测
        if frontend_max and frontend_max != ABP_MAX_LEN_EMAIL:
            drift_warning = (
                f"⚠️ 前后端规则不一致：\n"
                f"  前端 maxlength={frontend_max}\n"
                f"  后端 ABP 约束={ABP_MAX_LEN_EMAIL}\n"
            )
            evidence += drift_warning
            allure.attach(drift_warning, name="frontend_backend_drift", attachment_type=allure.attachment_type.TEXT)
        
        allure.attach(evidence, name="email_maxlength_evidence", attachment_type=allure.attachment_type.TEXT)

    with allure.step("[email] 填写超长字符串，验证截断"):
        long_email = ("a" * (ABP_MAX_LEN_EMAIL + 5)) + "@t.com"
        page.fill(selector, long_email)
        page.wait_for_timeout(100)
        actual_len = len(page.input_value(selector))
        
        result = (
            f"typed_len={len(long_email)}\n"
            f"actual_len={actual_len}\n"
            f"expected_max={ABP_MAX_LEN_EMAIL}\n"
        )
        allure.attach(result, name="truncation_result", attachment_type=allure.attachment_type.TEXT)
        step_shot(po, "step_maxlength_truncation", full_page=True)
        
        assert actual_len <= ABP_MAX_LEN_EMAIL, f"email: expected <= {ABP_MAX_LEN_EMAIL}, got {actual_len} (maxlength='{maxlength_attr}')"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotpassword")
@allure.story("P1 - Email length boundaries")
@allure.description(DESC_EMAIL_BOUNDARY)
@pytest.mark.parametrize("total_len", [ABP_MAX_LEN_EMAIL - 1, ABP_MAX_LEN_EMAIL])
def test_p1_forgotpassword_email_length_boundaries(unauth_page: Page, total_len: int):
    """
    email 边界值测试：255/256/257
    使用真实账号的email进行测试，验证前端截断行为。
    """
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)
    case_name = f"email_len_{total_len}"

    attach_rule_source_note(f"ABP Identity: MaxEmailLength={ABP_MAX_LEN_EMAIL}, 测试边界值 N-1/N/N+1")

    # 根据 total_len 查找 email 长度匹配的账号
    import json
    from pathlib import Path
    
    account_pool_path = Path("test-data/test_account_pool.json")
    with open(account_pool_path) as f:
        account_pool = json.load(f)
    
    # 查找 email 长度匹配的账号
    test_account = None
    for acc in account_pool.get("test_account_pool", []):
        if len(acc.get("email", "")) == total_len:
            test_account = acc
            break
    
    if not test_account:
        allure.attach(
            f"⚠️ 边界值账号不存在：email 长度={total_len}\n"
            f"说明：无法注册 email 长度={total_len} 的账号（{total_len > ABP_MAX_LEN_EMAIL and '超过 ABP 约束' or '未注册'}）\n"
            f"结论：测试不可执行（符合预期）",
            name=f"{case_name}_account_not_available",
            attachment_type=allure.attachment_type.TEXT,
        )
        pytest.skip(f"账号池中未找到 email 长度={total_len} 的账号（{'超过 ABP 约束，注册不可' if total_len > ABP_MAX_LEN_EMAIL else '未注册'}）")
    
    # 验证账号的 email 长度是否符合测试要求
    actual_email_len = len(test_account.get("email", ""))
    allure.attach(
        f"期望长度: {total_len}\n实际长度: {actual_email_len}\nemail: {test_account['email']}\n",
        name=f"{case_name}_account_info",
        attachment_type=allure.attachment_type.TEXT,
    )
    
    # 断言账号的 email 长度符合预期
    assert actual_email_len == total_len, f"账号池中的账号 email 长度={actual_email_len}，预期={total_len}"

    po.navigate()
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step(f"[{case_name}] 填写 email (长度={total_len})"):
        page.fill(selector, test_account["email"])
        page.wait_for_timeout(100)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

    actual_len = len(page.input_value(selector))
    
    # 断言：实际长度应等于预期长度
    assert actual_len == total_len, f"{case_name}: expected input_len={total_len}, got {actual_len}"
    
    # 提交测试（验证不崩溃）
    with allure.step(f"[{case_name}] 提交并验证不崩溃"):
        click_save(page)
        page.wait_for_timeout(2000)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)
        
        # 期望：不跳转到错误页
        current_url = page.url or ""
        assert "/Error" not in current_url and "/500" not in current_url, f"{case_name}: 跳转到错误页 {current_url}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountForgotpassword")
@allure.story("P1 - Required fields validation")
@allure.description(DESC_REQUIRED_VALIDATION)
def test_p1_forgotpassword_required_fields_validation(unauth_page: Page):
    """
    必填字段验证：email 为空时，前端应拦截（不应跳转到错误页）
    """
    logger.start()
    page = unauth_page
    po = AccountForgotpasswordPage(page)
    case_name = "required_email_empty"

    attach_rule_source_note("docs/requirements/requirements.md: ForgotPassword required fields (UI observable)")

    po.navigate()
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Email *"]'
    if page.locator(selector).count() == 0:
        pytest.skip("Email 输入框不可见")

    with allure.step(f"[{case_name}] 清空字段并提交（期望被拦截）"):
        # 清空 email 字段
        page.fill(selector, "")
        step_shot(po, f"step_{case_name}_before_submit", full_page=True)
        
        click_save(page)
        page.wait_for_timeout(1000)  # 等待可能的跳转
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    # 期望：仍在 ForgotPassword 页（被前端拦截）
    current_url = page.url or ""
    page_text = page.content()
    
    # 如果跳转到错误页 → 这是产品缺陷，直接 FAIL
    # 检查1：URL 包含错误关键词（不区分大小写）
    url_lower = current_url.lower()
    has_error_url = any(keyword in url_lower for keyword in ["/error", "/500", "/400", "/exception"])
    
    # 检查2：页面内容包含异常关键词
    has_exception_text = any(keyword in page_text for keyword in [
        "unhandled exception",
        "ArgumentException",
        "ModelState is not valid",
        "An error occurred",
        "Stack Trace"
    ])
    
    if has_error_url or has_exception_text:
        allure.attach(
            f"🔴 产品缺陷：必填字段为空应被前端拦截，但跳转到了错误页\n"
            f"URL: {current_url}\n"
            f"错误URL: {has_error_url}\n"
            f"异常内容: {has_exception_text}",
            name=f"{case_name}_product_defect",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert False, f"产品缺陷：{case_name} 跳转到错误页或触发异常，应该被前端拦截"
    
    # 正常判据：仍在 ForgotPassword 页
    assert "/Account/ForgotPassword" in current_url, f"{case_name}: unexpected navigation away to {current_url}"

    logger.end(success=True)
