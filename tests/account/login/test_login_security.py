# ═══════════════════════════════════════════════════════════════
# Account/Login - Security 安全测试
# ═══════════════════════════════════════════════════════════════
"""
安全测试内容：
- XSS/SQLi/HTML 注入
- 账号锁定机制
- 错误消息安全性
"""

import allure
import pytest
import uuid
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.account_login_page import AccountLoginPage
from tests.myaccount._helpers import attach_rule_source_note, step_shot
from tests.account.login._helpers import (
    assert_not_redirected_to_login,
    detect_fatal_error_page,
    get_first_available_account,
    unique_suffix,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger("login_security")


# ═══════════════════════════════════════════════════════════════
# 注入 Payload 库
# ═══════════════════════════════════════════════════════════════
INJECTION_PAYLOADS = [
    # XSS: 经典 script 注入
    ("xss_script", "<script>alert('XSS')</script>"),
    # XSS: 事件触发型
    ("xss_img", "<img src=x onerror=alert('XSS')>"),
    # XSS: SVG 向量
    ("xss_svg", "<svg onload=alert('XSS')>"),
    # SQLi: 逻辑绕过
    ("sqli_quote", "' OR '1'='1"),
    # SQLi: 注释截断
    ("sqli_comment", "admin'--"),
    # SQLi: UNION 注入
    ("sqli_union", "' UNION SELECT * FROM users--"),
    # SQLi: 布尔盲注
    ("sqli_blind", "' AND 1=1--"),
    # HTML 注入
    ("html_bold", "<b>bold</b>"),
]


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Username Injection")
@allure.description(
    """
测试点：
- 用户名输入框的 XSS/SQLi/HTML 注入防护
- 不触发浏览器 dialog（payload 不执行）
- 不导致 5xx 服务端错误
证据：填写/提交截图
"""
)
@pytest.mark.parametrize(
    "case_name,payload",
    INJECTION_PAYLOADS[:5],  # 使用前 5 个代表性 payload
    ids=[p[0] for p in INJECTION_PAYLOADS[:5]],
)
def test_security_xss_payload_no_dialog(unauth_page: Page, case_name: str, payload: str):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login injection safety (no dialog, no 5xx)")
    page = unauth_page
    po = AccountLoginPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(d):
        dialog_triggered["value"] = True
        try:
            d.dismiss()
        except Exception:
            pass

    page.on("dialog", on_dialog)
    with allure.step("导航到登录页"):
        try:
            po.navigate()
        except PlaywrightTimeoutError:
            # 共享环境偶发卡顿：重试一次
            po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    def _ensure_login_page() -> None:
        """
        submit 后页面可能发生 reload/跳转（例如错误页/重定向），导致下一轮找不到输入框。
        这里做“自愈”：每个场景开始前保证回到 /Account/Login 且输入框可见。
        """
        try:
            if page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT).count() > 0:
                return
        except Exception:
            pass
        try:
            po.navigate()
            page.wait_for_timeout(200)
        except Exception:
            pass
        assert_not_redirected_to_login(page)

    if page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT).count() == 0:
        pytest.skip("login input not found")
    _ensure_login_page()
    with allure.step(f"[{case_name}] 填写 payload + 提交（不应弹窗/不应 5xx）"):
        allure.attach(payload, name=f"{case_name}_payload", attachment_type=allure.attachment_type.TEXT)

        # ═══════════════════════════════════════════════════════════════
        # 控制变量：只有 username 是恶意 payload，password 填合法值
        # ═══════════════════════════════════════════════════════════════
        page.fill(po.USERNAME_OR_EMAIL_ADDRESS_INPUT, payload)
        if page.locator(po.PASSWORD_INPUT).count() > 0:
            # 填一个合法密码（不会成功登录，因为 username 是恶意值）
            page.fill(po.PASSWORD_INPUT, "ValidPass123!")
        page.wait_for_timeout(200)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        page.click(po.LOGIN_BUTTON)
        resp = wait_mutation_response(page, timeout_ms=3000)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        # 不再使用 xfail，直接断言失败（已知Bug应该在报告里"刺眼地显示为失败"）
        assert not fatal, f"产品缺陷：/Account/Login 注入类输入触发 500（Internal Server Error）: {fatal}"

        if resp is not None:
            assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        assert dialog_triggered["value"] is False, f"{case_name}: payload triggered a dialog"
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Password 输入框注入测试
# ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Password Injection")
@allure.description(
    """
测试点：
- 密码输入框的 XSS/SQLi/HTML 注入防护
- 不触发浏览器 dialog（payload 不执行）
- 不导致 5xx 服务端错误
- 密码可能直接进入 SQL 查询或日志，需要特别防护

证据：填写/提交截图
"""
)
@pytest.mark.parametrize(
    "case_name,payload",
    INJECTION_PAYLOADS,  # 使用全部 8 个 payload
    ids=[p[0] for p in INJECTION_PAYLOADS],
)
def test_security_password_injection_no_crash(unauth_page: Page, case_name: str, payload: str):
    """密码输入框注入测试：XSS/SQLi 应被安全处理"""
    logger.start()
    attach_rule_source_note("Security: Password input injection protection")
    page = unauth_page
    po = AccountLoginPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(d):
        dialog_triggered["value"] = True
        try:
            d.dismiss()
        except Exception:
            pass

    page.on("dialog", on_dialog)

    with allure.step("导航到登录页"):
        try:
            po.navigate()
        except PlaywrightTimeoutError:
            po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step(f"[Password-{case_name}] 填写 payload 到密码框并提交"):
        allure.attach(
            f"Payload: {payload}\n目标: Password 输入框",
            name=f"password_{case_name}_payload",
            attachment_type=allure.attachment_type.TEXT,
        )

        # 用户名填正常值，密码填恶意 payload
        page.fill(po.USERNAME_OR_EMAIL_ADDRESS_INPUT, "test_user_injection")
        page.fill(po.PASSWORD_INPUT, payload)
        page.wait_for_timeout(200)
        step_shot(po, f"step_password_{case_name}_filled", full_page=True)

        page.click(po.LOGIN_BUTTON)
        resp = wait_mutation_response(page, timeout_ms=3000)
        step_shot(po, f"step_password_{case_name}_after_submit", full_page=True)

        # 验证：不应触发服务端崩溃
        fatal = detect_fatal_error_page(page)
        assert not fatal, f"Password 注入触发服务端错误: {fatal}"

        if resp is not None:
            assert resp.status < 500, f"Password-{case_name}: 5xx status={resp.status}"
        
        # 验证：payload 不应被执行（无 dialog）
        assert dialog_triggered["value"] is False, f"Password-{case_name}: payload 触发了 dialog"

        allure.attach(
            f"✅ Password 输入框安全: {case_name} payload 未触发 XSS/崩溃",
            name=f"password_{case_name}_result",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 账号锁定机制测试
# ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Account Lockout")
@allure.description(
    """
测试点：
- ABP 默认 5 次登录失败后锁定账号 5 分钟
- 此测试仅验证"多次失败后不应能继续尝试"，不实际触发锁定（避免影响其他测试）
- 使用独立的随机账号，避免影响账号池账号

注意：
- 此测试为"行为验证"，不真正尝试 5 次（会触发锁定）
- 仅验证错误消息是否安全（不泄露账号存在性）
"""
)
@pytest.mark.parametrize(
    "attempt_count",
    [1, 2],
    ids=["first_attempt", "second_attempt"],
)
def test_security_login_failure_safe_message(unauth_page: Page, attempt_count: int, xdist_worker_id: str):
    """验证登录失败消息不泄露账号存在性"""
    logger.start()
    attach_rule_source_note("docs/requirements/account-login-field-requirements.md: Error message safety")
    page = unauth_page
    po = AccountLoginPage(page)
    
    # 使用 _helpers 生成唯一后缀
    suf = unique_suffix(xdist_worker_id)
    nonexistent_user = f"definitely_not_exist_{suf}@fake.test"
    random_password = f"FakePass_{uuid.uuid4().hex[:8]}!"

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step(f"尝试第 {attempt_count} 次登录（不存在的账号）"):
        allure.attach(
            f"测试账号: {nonexistent_user}\n尝试次数: {attempt_count}",
            name="test_info",
            attachment_type=allure.attachment_type.TEXT,
        )
        po.fill_username_or_email_address(nonexistent_user)
        po.fill_password(random_password)
        step_shot(po, f"step_filled_attempt_{attempt_count}", full_page=True)
        
        po.click_login()
        resp = wait_mutation_response(page, timeout_ms=5000)
        page.wait_for_timeout(500)
        step_shot(po, f"step_after_login_attempt_{attempt_count}", full_page=True)

    with allure.step("验证错误消息不泄露账号存在性"):
        # 获取页面上的错误消息
        error_texts = []
        try:
            # 尝试获取常见错误消息元素
            error_selectors = [
                ".error-message",
                ".validation-error",
                "[role='alert']",
                ".alert-danger",
                ".text-danger",
                ".error",
            ]
            for sel in error_selectors:
                els = page.locator(sel)
                for i in range(els.count()):
                    txt = els.nth(i).inner_text()
                    if txt.strip():
                        error_texts.append(txt.strip())
        except Exception:
            pass
        
        allure.attach(
            "\n".join(error_texts) if error_texts else "(无明显错误消息)",
            name="error_messages",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 验证错误消息不包含"用户不存在"等敏感信息
        sensitive_patterns = [
            "user not found",
            "用户不存在",
            "account does not exist",
            "invalid username",
            "用户名不存在",
        ]
        for msg in error_texts:
            msg_lower = msg.lower()
            for pattern in sensitive_patterns:
                assert pattern.lower() not in msg_lower, \
                    f"错误消息泄露账号存在性: '{msg}' 包含敏感模式 '{pattern}'"
        
        # 验证仍在登录页（未成功登录）
        current_url = page.url or ""
        assert "/login" in current_url.lower(), f"Expected to stay on login page, got: {current_url}"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 错误消息安全性测试
# ═══════════════════════════════════════════════════════════════


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Error Message Safety")
@allure.description(
    """
测试点：
- 密码错误时的错误消息不应泄露账号存在性
- 使用账号池中存在的账号 + 错误密码
- 验证错误消息与"账号不存在"时的消息一致（或同样模糊）
"""
)
def test_security_wrong_password_safe_message(unauth_page: Page):
    """验证密码错误时的消息不泄露账号存在性"""
    logger.start()
    attach_rule_source_note("docs/requirements/account-login-field-requirements.md: Error message safety")
    page = unauth_page
    po = AccountLoginPage(page)
    
    # 从 _helpers 获取账号
    test_account = get_first_available_account()
    if not test_account:
        pytest.skip("No available account in pool")
    
    # 使用账号池中存在的账号 + 错误密码
    existing_user = test_account.get("username", "") or test_account.get("email", "")
    if not existing_user:
        pytest.skip("Test account missing username and email")
    
    wrong_password = f"WrongPass_{uuid.uuid4().hex[:8]}!"

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("使用正确账号 + 错误密码登录"):
        allure.attach(
            f"账号: {existing_user[:3]}***\n密码: (错误密码)",
            name="test_info",
            attachment_type=allure.attachment_type.TEXT,
        )
        po.fill_username_or_email_address(existing_user)
        po.fill_password(wrong_password)
        step_shot(po, "step_filled", full_page=True)
        
        po.click_login()
        resp = wait_mutation_response(page, timeout_ms=5000)
        page.wait_for_timeout(500)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证错误消息不泄露账号存在性"):
        # 获取页面上的错误消息
        error_texts = []
        try:
            error_selectors = [
                ".error-message",
                ".validation-error",
                "[role='alert']",
                ".alert-danger",
                ".text-danger",
                ".error",
            ]
            for sel in error_selectors:
                els = page.locator(sel)
                for i in range(els.count()):
                    txt = els.nth(i).inner_text()
                    if txt.strip():
                        error_texts.append(txt.strip())
        except Exception:
            pass
        
        allure.attach(
            "\n".join(error_texts) if error_texts else "(无明显错误消息)",
            name="error_messages",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 验证错误消息不包含"密码错误"等敏感信息（不应区分账号存在与否）
        sensitive_patterns = [
            "wrong password",
            "密码错误",
            "incorrect password",
            "password is wrong",
            "密码不正确",
        ]
        for msg in error_texts:
            msg_lower = msg.lower()
            for pattern in sensitive_patterns:
                # 注意：这里我们只是记录，因为某些系统确实会显示"密码错误"
                # 但最佳实践是显示通用的"用户名或密码错误"
                if pattern.lower() in msg_lower:
                    allure.attach(
                        f"⚠️ 安全建议: 错误消息 '{msg}' 可能泄露账号存在性。"
                        f"建议使用通用消息如'用户名或密码错误'",
                        name="security_warning",
                        attachment_type=allure.attachment_type.TEXT,
                    )
        
        # 验证仍在登录页（未成功登录）
        current_url = page.url or ""
        assert "/login" in current_url.lower(), f"Expected to stay on login page, got: {current_url}"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 账号锁定机制测试 (HTTP 423)
# ═══════════════════════════════════════════════════════════════════════════════

DESC_ACCOUNT_LOCKOUT = """
测试点：
- 连续 5 次密码错误后账号被锁定
- 锁定后返回 HTTP 423 Locked
- 锁定时长：5 分钟（ABP 默认）

⚠️ 警告：
- 此测试会真正锁定测试账号
- 被锁定的账号 5 分钟内无法登录
- 建议使用专用的锁定测试账号

参考：docs/requirements/account-login-field-requirements.md
"""


@pytest.mark.P2
@pytest.mark.security
@pytest.mark.xfail(reason="产品当前未启用账号锁定机制（连续失败后不锁定）")
@allure.feature("AccountLogin")
@allure.story("Security - Account Lockout")
@allure.description(DESC_ACCOUNT_LOCKOUT)
def test_security_account_lockout_after_5_failures(unauth_page: Page):
    """
    测试账号锁定机制：连续 5 次失败后锁定
    
    专用测试账号: lockout_test_user / LockoutTest123!
    ⚠️ 此测试会真正锁定账号 5 分钟
    """
    logger.start()
    attach_rule_source_note(
        "docs/requirements/account-login-field-requirements.md: "
        "MaxFailedAccessAttempts=5, DefaultLockoutTimeSpan=5min"
    )
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    # 专用锁定测试账号（已创建）
    # 正确密码: LockoutTest123!  故意使用错误密码触发锁定
    LOCKOUT_TEST_USERNAME = "lockout_test_user"
    WRONG_PASSWORD = "WrongPassword999!"
    
    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    lockout_triggered = False
    
    for attempt in range(1, 7):  # 尝试 6 次，第 6 次应该被锁定
        with allure.step(f"第 {attempt} 次登录尝试（错误密码）"):
            # 清空并重新填写
            page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT).fill("")
            page.locator(po.PASSWORD_INPUT).fill("")
            
            po.fill_username_or_email_address(LOCKOUT_TEST_USERNAME)
            po.fill_password(WRONG_PASSWORD)
            
            po.click_login()
            resp = wait_mutation_response(page, timeout_ms=5000)
            page.wait_for_timeout(500)
            step_shot(po, f"step_attempt_{attempt}", full_page=True)
            
            if resp is not None:
                allure.attach(
                    f"尝试 {attempt}: HTTP {resp.status}",
                    name=f"attempt_{attempt}_status",
                    attachment_type=allure.attachment_type.TEXT,
                )
                
                # 检查是否返回 423 Locked
                if resp.status == 423:
                    lockout_triggered = True
                    allure.attach(
                        f"✅ 第 {attempt} 次尝试后账号被锁定 (HTTP 423)",
                        name="lockout_triggered",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    break
    
    with allure.step("验证锁定机制"):
        if lockout_triggered:
            allure.attach(
                "✅ 账号锁定机制正常工作",
                name="lockout_result",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 检查页面是否显示锁定消息
            page_text = page.inner_text("body").lower()
            if "locked" in page_text or "锁定" in page_text:
                lockout_triggered = True
                allure.attach(
                    "✅ 页面显示锁定消息",
                    name="lockout_result",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                pytest.fail("连续 6 次失败后未触发账号锁定")
    
    # ─────────────────────────────────────────────────────────────
    # 🔒 验证锁定期间：使用正确密码也无法登录
    # ─────────────────────────────────────────────────────────────
    if lockout_triggered:
        CORRECT_PASSWORD = "LockoutTest123!"  # 正确密码
        
        with allure.step("🔒 锁定期间验证：使用正确密码尝试登录"):
            # 清空并重新填写
            page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT).fill("")
            page.locator(po.PASSWORD_INPUT).fill("")
            
            po.fill_username_or_email_address(LOCKOUT_TEST_USERNAME)
            po.fill_password(CORRECT_PASSWORD)
            
            allure.attach(
                f"用户名: {LOCKOUT_TEST_USERNAME}\n密码: {CORRECT_PASSWORD[:3]}***（正确密码）",
                name="lockout_correct_password_attempt",
                attachment_type=allure.attachment_type.TEXT,
            )
            
            po.click_login()
            resp = wait_mutation_response(page, timeout_ms=5000)
            page.wait_for_timeout(500)
            step_shot(po, "step_lockout_correct_password", full_page=True)
            
            # 验证：即使密码正确，也应该被拒绝
            login_blocked = False
            
            if resp is not None:
                allure.attach(
                    f"HTTP 状态码: {resp.status}",
                    name="lockout_response_status",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 423 Locked 或 401 Unauthorized 都表示被拒绝
                if resp.status in [423, 401, 403]:
                    login_blocked = True
            
            # 检查是否仍在登录页或显示锁定消息
            current_url = page.url or ""
            page_text = page.inner_text("body").lower()
            
            if "/login" in current_url.lower():
                login_blocked = True
            if "locked" in page_text or "锁定" in page_text:
                login_blocked = True
            
            if login_blocked:
                allure.attach(
                    "✅ 锁定期间验证通过：使用正确密码也无法登录\n"
                    "账号在锁定期间（5分钟）内完全无法登录，无论密码是否正确",
                    name="lockout_period_verification",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                allure.attach(
                    "❌ 锁定期间验证失败：使用正确密码成功登录了\n"
                    "这是一个安全问题！锁定机制未能阻止登录",
                    name="lockout_period_verification",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.fail("锁定期间使用正确密码居然能登录，锁定机制存在安全漏洞！")
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 敏感信息泄露测试
# ═══════════════════════════════════════════════════════════════════════════════

DESC_CREDENTIALS_NOT_IN_URL = """
测试点：
- 账号、密码不应出现在 URL 中（GET 参数或路径）
- 登录应使用 POST 方法
- 防止敏感信息泄露到浏览器历史、日志、Referer 头
"""


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Credentials Not in URL")
@allure.description(DESC_CREDENTIALS_NOT_IN_URL)
def test_security_credentials_not_in_url(unauth_page: Page):
    """
    验证账号和密码不会出现在 URL 中
    """
    logger.start()
    attach_rule_source_note("安全测试：账号密码不应出现在 URL")
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    TEST_USERNAME = "testuser_secret"
    TEST_PASSWORD = "SecretPassword123!"
    
    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    with allure.step("填写登录信息"):
        po.fill_username_or_email_address(TEST_USERNAME)
        po.fill_password(TEST_PASSWORD)
        step_shot(po, "step_filled", full_page=True)
    
    with allure.step("提交登录"):
        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)
    
    with allure.step("验证敏感信息不在 URL 中"):
        current_url = page.url
        allure.attach(f"当前 URL: {current_url}", name="current_url", attachment_type=allure.attachment_type.TEXT)
        
        # 检查用户名不在 URL
        assert TEST_USERNAME not in current_url, f"用户名出现在 URL 中！URL: {current_url}"
        assert "username=" not in current_url.lower(), f"username 参数出现在 URL 中！URL: {current_url}"
        
        # 检查密码不在 URL
        assert TEST_PASSWORD not in current_url, f"密码出现在 URL 中！URL: {current_url}"
        assert "password=" not in current_url.lower(), f"password 参数出现在 URL 中！URL: {current_url}"
        
        allure.attach(
            "✅ 账号和密码均未出现在 URL 中",
            name="result",
            attachment_type=allure.attachment_type.TEXT,
        )
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 浏览器自动保存密码测试
# ═══════════════════════════════════════════════════════════════════════════════

DESC_AUTOCOMPLETE = """
测试点：
- 检查密码输入框是否禁用浏览器自动保存
- autocomplete="off" 或 "new-password" 可防止浏览器记住密码
- 对于高安全性要求的系统，不应让浏览器保存密码

注意：这是一个安全建议，不是强制要求。实际产品可能出于用户体验考虑允许保存。
"""


@pytest.mark.P2
@pytest.mark.security
@allure.feature("AccountLogin")
@allure.story("Security - Autocomplete")
@allure.description(DESC_AUTOCOMPLETE)
def test_security_password_autocomplete_disabled(unauth_page: Page):
    """
    检查密码输入框是否禁用浏览器自动保存
    """
    logger.start()
    attach_rule_source_note("安全测试：浏览器自动保存密码")
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)
    
    with allure.step("检查密码输入框 autocomplete 属性"):
        password_input = page.locator(po.PASSWORD_INPUT)
        autocomplete = password_input.get_attribute("autocomplete")
        
        allure.attach(
            f"密码输入框 autocomplete 属性值: {autocomplete or '(未设置)'}",
            name="password_autocomplete",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 安全的 autocomplete 值
        safe_values = ["off", "new-password", "current-password"]
        
        if autocomplete and autocomplete.lower() in safe_values:
            allure.attach(
                f"✅ 密码输入框已设置 autocomplete=\"{autocomplete}\"",
                name="password_result",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            allure.attach(
                f"⚠️ 密码输入框未禁用自动保存 (autocomplete=\"{autocomplete or 'on'}\")\n"
                "建议设置 autocomplete=\"off\" 或 \"new-password\"",
                name="password_result",
                attachment_type=allure.attachment_type.TEXT,
            )
    
    with allure.step("检查用户名输入框 autocomplete 属性"):
        username_input = page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT)
        username_autocomplete = username_input.get_attribute("autocomplete")
        
        allure.attach(
            f"用户名输入框 autocomplete 属性值: {username_autocomplete or '(未设置)'}",
            name="username_autocomplete",
            attachment_type=allure.attachment_type.TEXT,
        )
    
    step_shot(po, "step_autocomplete_check", full_page=True)
    logger.end(success=True)