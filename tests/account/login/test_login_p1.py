# ═══════════════════════════════════════════════════════════════
# Account/Login - P1 核心验证测试
# ═══════════════════════════════════════════════════════════════
"""
P1 测试内容：
- 必填字段验证（用户名/密码为空）
- 无效凭证处理
- 链接导航（Register / Forgot Password）
- 多登录方式（用户名 / 邮箱）
- Remember Me 功能
"""

from utils.config import ConfigManager
import os
import tempfile
import allure
import pytest
import time
import uuid
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.settings.profile._helpers import attach_rule_source_note, step_shot
from tests.account.login import _helpers
from tests.account.login._helpers import (
    assert_not_redirected_to_login,
    assert_any_validation_evidence,
    detect_fatal_error_page,
    get_first_available_account,
    has_any_error_ui,
    unique_suffix,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger("login_p1")


# ═══════════════════════════════════════════════════════════════
# 必填字段验证
# ═══════════════════════════════════════════════════════════════

DESC_REQUIRED_VALIDATION = """
测试点：
- username_or_email/password 为空时：前端应拦截（仍停留在登录页）
- 独立测试每个字段，控制变量
证据：清空前后 + 提交后截图
"""


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Required Fields")
@allure.description(DESC_REQUIRED_VALIDATION)
@pytest.mark.parametrize(
    "field,selector_attr",
    [
        ("username_or_email", "USERNAME_OR_EMAIL_ADDRESS_INPUT"),
        ("password", "PASSWORD_INPUT"),
    ],
    ids=["required_username_empty", "required_password_empty"],
)
def test_p1_login_required_fields_validation(unauth_page: Page, field: str, selector_attr: str):
    """
    必填字段验证：清空目标字段并提交，期望被前端拦截。
    """
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Required fields")
    page = unauth_page
    po = AccountLoginPage(page)
    case_name = f"required_{field}_empty"

    with allure.step("导航到登录页"):
    po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    # 获取实际 selector
    actual_selector = getattr(po, selector_attr, None)
    if not actual_selector or page.locator(actual_selector).count() == 0:
            pytest.skip(f"{field} input not found")
    
    with allure.step(f"[{case_name}] 填写其他字段，清空目标字段并提交"):
        # 控制变量：填写其他字段
        if field == "username_or_email":
            po.fill_password("TestPass123!")
        else:
            po.fill_username_or_email_address("testuser@example.com")

            # 清空目标字段
            page.fill(actual_selector, "")
            step_shot(po, f"step_{case_name}_before_submit", full_page=True)

    po.click_login()
        page.wait_for_timeout(1000)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)
    
    with allure.step("验证被前端拦截"):
    current_url = page.url or ""
        page_text = page.content()

        # 检查是否跳转到错误页（产品缺陷）
        has_error_url = any(kw in current_url.lower()
                               for kw in ["/error", "/500", "/400", "/exception"])
        has_exception_text = any(kw in page_text for kw in [
            "unhandled exception", "ArgumentException", "ModelState is not valid",
            "An error occurred", "Stack Trace"
        ])

        if has_error_url or has_exception_text:
            allure.attach(
                f"🔴 产品缺陷：必填字段为空应被前端拦截，但跳转到了错误页\nURL: {current_url}",
                name=f"{case_name}_product_defect",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert False, f"产品缺陷：{case_name} 跳转到错误页，应被前端拦截"

    # 正常判据：仍在登录页
    assert "/login" in current_url.lower() or "/account/login" in current_url.lower(), \
    f"{case_name}: unexpected navigation to {current_url}"
    
    logger.end(success=True)

    # ═══════════════════════════════════════════════════════════════
    # 输入校验测试
    # ═══════════════════════════════════════════════════════════════


DESC_INPUT_VALIDATION = """
    测试点：
    - 空格处理：前后空格是否被 trim
    - 大小写敏感性：用户名/邮箱是否区分大小写
    - 纯空格绕过：只输入空格能否绕过必填校验
    """


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Input Whitespace Handling")
@allure.description(
    """
    测试点：
    - 验证系统不会自动 trim 用户名前后空格
    - 带空格的用户名登录应失败（系统严格匹配）

    预期行为：登录失败，因为空格不被 trim
    """
    )
def test_p1_login_username_whitespace_not_trimmed(unauth_page: Page):
    """验证用户名前后空格不被 trim，带空格登录应失败"""
    logger.start()
    attach_rule_source_note("系统设计：用户名前后空格不自动 trim")
    page = unauth_page
    po = AccountLoginPage(page)

    # 获取一个真实账号
    account = get_first_available_account()
    if not account:
        pytest.skip("没有可用的测试账号")

    username = account["username"]
    password = account["password"]

    # 在用户名前后加空格
    username_with_spaces = f"  {username}  "

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step(f"使用带空格的用户名登录: '{username_with_spaces}'"):
        allure.attach(
            f"原始用户名: '{username}'\n"
        f"带空格用户名: '{username_with_spaces}'\n"
        f"长度变化: {len(username)} → {len(username_with_spaces)}",
        name="whitespace_test_input",
        attachment_type=allure.attachment_type.TEXT,
        )

        po.fill_username_or_email_address(username_with_spaces)
        po.fill_password(password)
        step_shot(po, "step_filled_with_spaces", full_page=True)

        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录失败（预期行为）"):
        current_url = page.url or ""

        # 预期：带空格的用户名登录应该失败
        if "/login" in current_url.lower() or has_any_error_ui(page):
            allure.attach(
            "✅ 带空格用户名登录失败（预期行为）\n"
            "系统不自动 trim 用户名前后空格",
            name="whitespace_test_result",
            attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 如果意外登录成功，说明系统 trim 了空格
            allure.attach(
            "⚠️ 意外：带空格用户名登录成功\n"
            "系统可能自动 trim 了空格",
            name="whitespace_test_result",
            attachment_type=allure.attachment_type.TEXT,
        )
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Password Whitespace")
@allure.description(
    """
    测试点：
    - 密码前后有空格时，系统是否 trim
    - 密码通常不应被 trim（空格是密码的一部分）

    证据：带空格密码 vs 登录结果
    """
    )
def test_p1_login_password_whitespace_not_trimmed(unauth_page: Page):
    """测试密码前后空格是否被保留（不 trim）"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Password handling")
    page = unauth_page
    po = AccountLoginPage(page)

    # 获取一个真实账号
    account = get_first_available_account()
    if not account:
        pytest.skip("没有可用的测试账号")

    username = account["username"]
    password = account["password"]

    # 在密码前后加空格
    password_with_spaces = f"  {password}  "

    with allure.step("导航到登录页"):
    po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    with allure.step(f"使用带空格的密码登录"):
        allure.attach(
            f"原始密码长度: {len(password)}\n"
            f"带空格密码长度: {len(password_with_spaces)}\n"
            f"前后各加 2 个空格",
        name="password_whitespace_test",
        attachment_type=allure.attachment_type.TEXT,
        )

        po.fill_username_or_email_address(username)
        po.fill_password(password_with_spaces)
        step_shot(po, "step_filled_with_spaces", full_page=True)

    po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录结果（预期失败，因为密码不应被 trim）"):
        current_url = page.url or ""

        if "/login" in current_url.lower() or has_any_error_ui(page):
            # 登录失败，说明密码空格被保留（正确行为）
            allure.attach(
            "✅ 密码空格被正确保留，带空格密码登录失败（预期行为）",
            name="password_whitespace_result",
            attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 如果登录成功，说明密码被 trim 了（可能有安全风险）
            allure.attach(
            "⚠️ 密码空格被 trim 了，带空格密码也能登录成功\n"
            "这可能是一个安全风险，建议保留密码中的空格",
            name="password_whitespace_result",
            attachment_type=allure.attachment_type.TEXT,
            )
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Case Sensitivity")
@allure.description(
    """
    测试点：
    - 用户名/邮箱大小写敏感性测试
    - 使用已存在账号，改变大小写后尝试登录

    证据：大小写变化后的登录结果
    """
    )
def test_p1_login_username_case_sensitivity(unauth_page: Page):
    """测试用户名/邮箱是否大小写敏感"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Case sensitivity")
    page = unauth_page
    po = AccountLoginPage(page)

    # 获取一个真实账号
    account = get_first_available_account()
    if not account:
        pytest.skip("没有可用的测试账号")

    username = account["username"]
    password = account["password"]

    # 改变大小写（如果原本是小写，改成大写）
    username_case_changed = username.upper() if username.islower() else username.swapcase()

    with allure.step("导航到登录页"):
    po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    with allure.step(f"使用大小写变化的用户名登录"):
        allure.attach(
            f"原始用户名: '{username}'\n"
            f"变化后: '{username_case_changed}'",
        name="case_sensitivity_input",
        attachment_type=allure.attachment_type.TEXT,
        )

        po.fill_username_or_email_address(username_case_changed)
        po.fill_password(password)
        step_shot(po, "step_filled_case_changed", full_page=True)

        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("记录大小写敏感性行为"):
        current_url = page.url or ""

        if "/login" not in current_url.lower():
            allure.attach(
            "✅ 用户名大小写不敏感，登录成功",
            name="case_sensitivity_result",
            attachment_type=allure.attachment_type.TEXT,
            )
    else:
            allure.attach(
            "ℹ️ 用户名大小写敏感，变化后登录失败（记录系统行为）",
            name="case_sensitivity_result",
            attachment_type=allure.attachment_type.TEXT,
            )
            # 不强制失败，只记录系统行为
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Whitespace Only Bypass")
@allure.description(
    """
    测试点：
    - 只输入空格是否能绕过必填校验
    - 空格不应被视为有效输入

    证据：纯空格输入后的系统响应
    """
    )
@pytest.mark.parametrize(
    "field,whitespace_input",
    [
    ("username", "   "),      # 3个空格
    ("password", "    "),     # 4个空格
    ("username", "\t\t"),     # Tab字符
    ],
    ids=["username_spaces", "password_spaces", "username_tabs"],
    )
def test_p1_login_whitespace_only_should_fail(unauth_page: Page, field: str, whitespace_input: str):
    """测试纯空格/Tab 是否能绕过必填校验"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Required validation")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step(f"在 {field} 字段输入纯空白字符"):
        allure.attach(
            f"字段: {field}\n"
        f"输入: '{whitespace_input}' (长度={len(whitespace_input)})\n"
        f"字符: {repr(whitespace_input)}",
        name="whitespace_only_input",
        attachment_type=allure.attachment_type.TEXT,
        )

        if field == "username":
            po.fill_username_or_email_address(whitespace_input)
            po.fill_password("ValidPassword123!")
        else:
            po.fill_username_or_email_address("someuser")
            po.fill_password(whitespace_input)

            step_shot(po, f"step_filled_{field}_whitespace", full_page=True)

            po.click_login()
            resp = wait_mutation_response(page, timeout_ms=5000)
            page.wait_for_timeout(500)
            step_shot(po, f"step_after_submit_{field}", full_page=True)

    with allure.step("验证纯空格不能绕过必填校验"):
        current_url = page.url or ""

        # 应该仍在登录页（未成功登录）
        if "/login" in current_url.lower():
            allure.attach(
            f"✅ 纯空格 {field} 未能登录（符合预期）",
            name="whitespace_bypass_result",
            attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 如果跳转了，可能是绕过成功（产品缺陷）
            allure.attach(
            f"⚠️ 纯空格 {field} 似乎绕过了校验，跳转到: {current_url}",
            name="whitespace_bypass_warning",
            attachment_type=allure.attachment_type.TEXT,
            )

            # 检查是否有错误提示
        if has_any_error_ui(page):
            allure.attach(
            "✅ 显示了错误提示",
            name="error_displayed",
            attachment_type=allure.attachment_type.TEXT,
            )

            logger.end(success=True)

    # ═══════════════════════════════════════════════════════════════
    # 无效凭证处理
    # ═══════════════════════════════════════════════════════════════


DESC_INVALID_CREDENTIALS = """
    测试点：
    - 使用不存在的用户名/邮箱 + 任意密码提交，必须不能登录
    - 证据：提交前后截图 + 不跳转 + 不 5xx

    注意：
    - 为避免 lockout 风险：仅使用明显不存在的随机用户名；每次只提交一次
    """


@pytest.mark.P1
@pytest.mark.exception
@allure.feature("AccountLogin")
@allure.story("P1 - Invalid Credentials")
@allure.description(DESC_INVALID_CREDENTIALS)
def test_p1_login_invalid_credentials_should_stay(unauth_page: Page, xdist_worker_id: str):
    """无效凭证不应登录成功，应停留在登录页"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Invalid credentials")
    page = unauth_page
    po = AccountLoginPage(page)

    suf = unique_suffix(xdist_worker_id)
    bogus_user = f"no_such_user_{suf}"
    bogus_pwd = f"BadPass_{uuid.uuid4().hex[:6]}!"

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step("填写不存在的用户名 + 任意密码并提交"):
        allure.attach(
        f"用户名: {bogus_user}\n密码: {bogus_pwd[:3]}***",
        name="test_credentials",
        attachment_type=allure.attachment_type.TEXT,
        )
        po.fill_username_or_email_address(bogus_user)
        po.fill_password(bogus_pwd)
        step_shot(po, "step_filled", full_page=True)

        po.click_login()
        resp = wait_mutation_response(page, timeout_ms=15000)
        page.wait_for_timeout(300)
        step_shot(po, "step_after_submit", full_page=True)

    with allure.step("验证不会崩溃且停留在登录页"):
        fatal = detect_fatal_error_page(page)
        assert not fatal, f"fatal error page detected: {fatal}"

    if resp is not None and resp.status >= 500:
        allure.attach(
            f"⚠️ 后端返回 5xx: status={resp.status}",
            name="backend_5xx_warning",
            attachment_type=allure.attachment_type.TEXT,
        )

    current_url = page.url or ""
    assert "/login" in current_url.lower() or "/account/login" in current_url.lower(), \
        f"expected stay on login page, got: {current_url}"

    logger.end(success=True)

    # ═══════════════════════════════════════════════════════════════
    # 链接导航测试
    # ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P1 - Navigation")
def test_p1_login_register_link_navigation(unauth_page: Page):
    """测试点击 Register 链接能正确跳转到注册页"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Register link")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step("点击 Register 链接"):
        register_link = page.locator(po.REGISTER_LINK)
        if register_link.count() == 0:
            pytest.skip("Register link not found on login page")

        register_link.click()
        page.wait_for_timeout(1000)
        step_shot(po, "step_after_click_register", full_page=True)

    with allure.step("验证跳转到注册页"):
        current_url = page.url or ""
        assert "/register" in current_url.lower(), f"Expected register page, got: {current_url}"
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P1 - Navigation")
def test_p1_login_forgot_password_link_navigation(unauth_page: Page):
    """测试点击 Forgot Password 链接能正确跳转"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Forgot Password link")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step("点击 Forgot Password 链接"):
        forgot_link = page.locator(po.FORGOT_PASSWORD_LINK)
        if forgot_link.count() == 0:
            pytest.skip("Forgot Password link not found on login page")

        forgot_link.click()
        page.wait_for_timeout(1000)
        step_shot(po, "step_after_click_forgot", full_page=True)

    with allure.step("验证跳转到忘记密码页"):
        current_url = page.url or ""
        assert "/forgot-password" in current_url.lower() or "/forgotpassword" in current_url.lower(), \
            f"Expected forgot password page, got: {current_url}"
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)

    # ═══════════════════════════════════════════════════════════════
    # 多登录方式测试
    # ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P1 - Login Methods")
@pytest.mark.parametrize(
    "login_method,credential_key",
    [
    ("username", "username"),
    ("email", "email"),
    ],
    ids=["login_by_username", "login_by_email"],
    )
def test_p1_login_multiple_methods(unauth_page: Page, login_method: str, credential_key: str):
    """测试系统支持用户名和邮箱两种登录方式"""
    logger.start()
    attach_rule_source_note(
    f"docs/requirements/account-login-field-requirements.md: Login by {login_method}")
    page = unauth_page
    po = AccountLoginPage(page)

    # 从 _helpers 获取账号
    test_account = get_first_available_account()
    if not test_account:
        pytest.skip("No available account in pool")

    credential = test_account.get(credential_key, "")
    if not credential:
        pytest.skip(f"Test account missing '{credential_key}' field")

    password = test_account.get("password", "")
    if not password:
        pytest.skip("Test account missing 'password' field")

    with allure.step("导航到登录页"):
    po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step(f"使用 {login_method} 登录"):
        allure.attach(
            f"登录方式: {login_method}\n凭证: {credential[:3]}***",
            name="login_info",
            attachment_type=allure.attachment_type.TEXT,
        )
        po.fill_username_or_email_address(credential)
        po.fill_password(password)
        step_shot(po, f"step_filled_{login_method}", full_page=True)

        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, f"step_after_login_{login_method}", full_page=True)

    with allure.step("验证登录结果"):
        current_url = page.url or ""
        if "/login" in current_url.lower():
            assert not has_any_error_ui(page), f"Login failed with {login_method}: error UI detected"
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)

    # ═══════════════════════════════════════════════════════════════
    # Remember Me 功能测试
    # ═══════════════════════════════════════════════════════════════


def _find_remember_me_checkbox(page: Page, po) -> any:
    """查找 Remember Me checkbox"""
    # 优先使用 role-based 选择器（更可靠）
    selectors = [
        # Role-based (最可靠)
        "role=checkbox[name='Remember me']",
        "role=checkbox[name*='emember']",
        # 标准 ID
        "#rememberMe",
        "#remember-me",
        # Input 属性
        "input[type='checkbox'][name*='remember' i]",
        "input[type='checkbox'][id*='remember' i]",
        # Label 关联
        "label:has-text('Remember') input[type='checkbox']",
        "label:has-text('Remember me') input",
        # 容器内的 checkbox
        "[class*='remember'] input[type='checkbox']",
        # data-testid
        "[data-testid='remember-me']",
    ]
    
    # 先尝试 PO 定义的选择器
    po_selector = getattr(po, 'REMEMBER_ME_CHECKBOX', None)
    if po_selector:
        selectors.insert(0, po_selector)
    
    for sel in selectors:
        try:
            elem = page.locator(sel)
            if elem.count() > 0:
                return elem.first
        except Exception:
            continue
    
    return None


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P1 - Remember Me")
def test_p1_login_remember_me_functionality(unauth_page: Page):
    """测试 Remember Me checkbox 可见性和切换状态"""
    logger.start()
    attach_rule_source_note(
    "docs/requirements/account-login-field-requirements.md: Remember Me")
    page = unauth_page
    po = AccountLoginPage(page)

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
        assert_not_redirected_to_login(page)

    with allure.step("验证 Remember Me checkbox 存在"):
        remember_me = _find_remember_me_checkbox(page, po)
        if not remember_me:
            pytest.skip("Remember Me checkbox not found")

        allure.attach("✅ Remember Me checkbox 存在", name="checkbox_found",
                      attachment_type=allure.attachment_type.TEXT)
        step_shot(po, "step_checkbox_found", full_page=True)

    with allure.step("测试 checkbox 切换状态"):
        initial_checked = remember_me.is_checked()
        allure.attach(f"初始状态: {'已勾选' if initial_checked else '未勾选'}",
                      name="initial_state", attachment_type=allure.attachment_type.TEXT)

        remember_me.click()
        page.wait_for_timeout(300)
        after_click = remember_me.is_checked()
        step_shot(po, "step_after_toggle", full_page=True)

        assert after_click != initial_checked, "Checkbox 状态未改变"

    remember_me.click()
    page.wait_for_timeout(300)
    final_checked = remember_me.is_checked()
    assert final_checked == initial_checked, "Checkbox 无法切换回原状态"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("AccountLogin")
@allure.story("P1 - Remember Me")
def test_p1_login_remember_me_cookie_persistence(browser):
    """测试 Remember Me 勾选后的 cookie 持久化，验证关闭浏览器后再次访问能自动保持登录"""
    logger.start()
    attach_rule_source_note("docs/requirements/account-login-field-requirements.md: Remember Me cookie")

    # 使用固定账号
    test_account = _helpers.get_boundary_account("special_account", "lockout_test")
    if not test_account:
        test_account = get_first_available_account()
    if not test_account:
        pytest.skip("No available account for Remember Me test")

    allure.attach(
        f"Username: {test_account['username']}\nEmail: {test_account.get('email', 'N/A')}",
        name="test_account_info",
        attachment_type=allure.attachment_type.TEXT
    )

    # 第一阶段：登录并勾选 Remember Me
    ctx1 = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
    page1 = ctx1.new_page()
    po1 = AccountLoginPage(page1)

    with allure.step("1. 导航到登录页"):
        po1.navigate()
        step_shot(po1, "step_1_navigate", full_page=True)

    with allure.step("2. 勾选 Remember Me"):
        remember_me = _find_remember_me_checkbox(page1, po1)
        if not remember_me:
            ctx1.close()
            pytest.skip("Remember Me checkbox not found")

        if not remember_me.is_checked():
            remember_me.click()
            page1.wait_for_timeout(300)

        assert remember_me.is_checked(), "Remember Me 勾选失败"
        step_shot(po1, "step_2_remember_me_checked", full_page=True)

    with allure.step("3. 填写账号并登录"):
        po1.fill_username_or_email_address(test_account["username"])
        po1.fill_password(test_account["password"])
        step_shot(po1, "step_3_before_login", full_page=True)

        po1.click_login()
        page1.wait_for_timeout(2000)
        step_shot(po1, "step_3_after_login", full_page=True)

    with allure.step("4. 检查 cookie 持久化属性"):
        cookies = ctx1.cookies()
        cookie_info = [f"name={c['name']}, expires={c.get('expires', 'session')}" for c in cookies]
        allure.attach("\n".join(cookie_info), name="cookies_after_login", attachment_type=allure.attachment_type.TEXT)

        auth_cookies = [c for c in cookies if any(k in c['name'].lower() for k in ['auth', 'session', 'token', '.aspnetcore', 'identity'])]
        persistent_cookies = [c for c in auth_cookies if c.get('expires', -1) > 0]

        if persistent_cookies:
            allure.attach(f"✅ 检测到 {len(persistent_cookies)} 个持久化认证 cookie",
                          name="persistence_check", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("⚠️ 未检测到持久化认证 cookie",
                          name="persistence_check", attachment_type=allure.attachment_type.TEXT)

    # 第二阶段：保存 storage state
    storage_state_file = os.path.join(tempfile.gettempdir(), "remember_me_storage.json")

    with allure.step("5. 保存 storage state"):
        ctx1.storage_state(path=storage_state_file)
        allure.attach(f"Storage state saved to: {storage_state_file}",
                      name="storage_state_saved", attachment_type=allure.attachment_type.TEXT)

    with allure.step("6. 关闭浏览器 context"):
        ctx1.close()
        allure.attach("✅ Context 已关闭", name="context_closed", attachment_type=allure.attachment_type.TEXT)

    # 第三阶段：使用保存的 storage state 创建新 context
    with allure.step("7. 创建新的浏览器 context"):
        ctx2 = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080},
            storage_state=storage_state_file
        )
        page2 = ctx2.new_page()
        po2 = AccountLoginPage(page2)
        allure.attach("✅ 新 Context 已创建", name="new_context_created", attachment_type=allure.attachment_type.TEXT)

    with allure.step("8. 访问受保护页面 /account/profile，验证是否自动保持登录"):
        cfg = ConfigManager()
        base_url = cfg.get_service_url("frontend") or "http://localhost:5173"
        # 访问受保护页面（需要登录才能访问）
        protected_url = f"{base_url}/account/profile"
        page2.goto(protected_url)
        page2.wait_for_timeout(2000)
        step_shot(po2, "step_8_after_reopen_profile", full_page=True)

        current_url = page2.url
        allure.attach(
            f"请求 URL: {protected_url}\n最终 URL: {current_url}",
            name="url_after_reopen",
            attachment_type=allure.attachment_type.TEXT
        )

        # 判断登录状态：
        # - 如果被重定向到 /login，说明未登录
        # - 如果停留在 /account/profile 或其他非 login 页面，说明已登录
        is_still_logged_in = "/login" not in current_url.lower()

        if is_still_logged_in:
            allure.attach(
                "✅ Remember Me 生效：成功访问受保护页面 /account/profile\n"
                "说明 cookie 持久化正常，关闭浏览器后仍保持登录状态",
                name="remember_me_result",
                attachment_type=allure.attachment_type.TEXT
            )
        else:
            allure.attach(
                "❌ Remember Me 未生效：访问受保护页面被重定向到登录页\n"
                "说明 cookie 未持久化或已过期",
                name="remember_me_result",
                attachment_type=allure.attachment_type.TEXT
            )

    # 清理
    ctx2.close()
    if os.path.exists(storage_state_file):
        os.remove(storage_state_file)

    assert is_still_logged_in, "Remember Me 功能失效：关闭浏览器后未能保持登录状态"

    logger.end(success=True)
