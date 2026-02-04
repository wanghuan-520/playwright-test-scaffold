"""
Account/Login - 边界测试

测试内容：
- 使用真实边界账号的登录成功测试
- Username 边界: 255/256 字符
- Password 边界: 127/128 字符

前置条件：
- 需要先运行 `python3 utils/create_boundary_accounts.py` 创建边界账号
- 边界账号信息保存在 `test-data/boundary_accounts.json`

参考文档：docs/requirements/account-login-field-requirements.md
"""

import json
import allure
import pytest
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.settings.profile._helpers import attach_rule_source_note, step_shot
from tests.account.login._helpers import (
    assert_not_redirected_to_login,
    detect_fatal_error_page,
    has_any_error_ui,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ABP 常量（与后端保持一致）
# ═══════════════════════════════════════════════════════════════════════════════
ABP_MAX_USERNAME_LENGTH = 256
ABP_MAX_PASSWORD_LENGTH = 128


# ═══════════════════════════════════════════════════════════════════════════════
# 边界账号加载
# ═══════════════════════════════════════════════════════════════════════════════

def _load_boundary_accounts() -> dict:
    """加载边界账号配置"""
    boundary_file = Path("test-data/boundary_accounts.json")
    if not boundary_file.exists():
        return {"boundary_accounts": []}
    
    try:
        return json.loads(boundary_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ 加载边界账号失败: {e}")
        return {"boundary_accounts": []}


def _get_boundary_account(account_type: str, boundary: str) -> Optional[dict]:
    """获取指定类型和边界的账号"""
    data = _load_boundary_accounts()
    for account in data.get("boundary_accounts", []):
        if account.get("type") == account_type and account.get("boundary") == boundary:
            return account
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Username 边界登录测试
# ═══════════════════════════════════════════════════════════════════════════════

DESC_USERNAME_BOUNDARY = """
测试点：
- 使用预先创建的边界用户名账号进行真实登录
- 验证 255/256 字符用户名能够正常登录成功

边界值：
- len_255: 最大-1（255 字符用户名）
- len_256: 最大值（256 字符用户名）
"""


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Username Boundary Login")
@allure.description(DESC_USERNAME_BOUNDARY)
@pytest.mark.parametrize(
    "account_type,boundary",
    [
        pytest.param("username_boundary", "len_255", id="username_len_255"),
        pytest.param("username_boundary", "len_256", id="username_len_256"),
    ],
)
def test_p1_login_username_boundary(unauth_page: Page, account_type: str, boundary: str):
    """使用真实边界用户名账号登录（用户名登录）"""
    account = _get_boundary_account(account_type, boundary)
    if not account:
        pytest.skip(f"边界账号未创建: {account_type}:{boundary}，请先运行 create_boundary_accounts.py")
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    attach_rule_source_note(
        f"test-data/boundary_accounts.json: {account_type}:{boundary}"
    )
    
    username = account["username"]
    password = account["password"]
    
    with allure.step(f"账号信息: {boundary}"):
        allure.attach(
            f"边界: {boundary}\n"
            f"用户名长度: {len(username)}\n"
            f"用户名前20字符: {username[:20]}...\n"
            f"邮箱: {account.get('email', 'N/A')}\n"
            f"密码长度: {len(password)}",
            name="boundary_account_info",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写边界用户名并登录"):
        po.fill_username_or_email_address(username)
        po.fill_password(password)
        step_shot(po, "step_before_login", full_page=True)
        
        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录结果"):
        current_url = page.url or ""
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)
        
        if has_any_error_ui(page):
            pytest.fail(f"边界账号登录失败: {boundary}，出现错误UI")
        
        if "/login" in current_url.lower() or "/account/login" in current_url.lower():
            fatal = detect_fatal_error_page(page)
            if fatal:
                pytest.fail(f"边界账号登录失败: {boundary}，触发致命错误: {fatal}")


# ═══════════════════════════════════════════════════════════════════════════════
# Password 边界登录测试
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# Email 边界登录测试
# ═══════════════════════════════════════════════════════════════════════════════

DESC_EMAIL_BOUNDARY = """
测试点：
- 使用预先创建的边界邮箱账号进行真实登录
- 验证 255/256 字符邮箱能够正常登录成功

边界值：
- len_255: 最大-1（255 字符邮箱）
- len_256: 最大值（256 字符邮箱）
"""


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Email Boundary Login")
@allure.description(DESC_EMAIL_BOUNDARY)
@pytest.mark.parametrize(
    "account_type,boundary",
    [
        pytest.param("email_boundary", "len_255", id="email_len_255"),
        pytest.param("email_boundary", "len_256", id="email_len_256"),
    ],
)
def test_p1_login_email_boundary(unauth_page: Page, account_type: str, boundary: str):
    """使用真实边界邮箱账号登录（邮箱登录）"""
    account = _get_boundary_account(account_type, boundary)
    if not account:
        pytest.skip(f"边界账号未创建: {account_type}:{boundary}，请先运行 create_boundary_accounts.py")
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    attach_rule_source_note(
        f"test-data/boundary_accounts.json: {account_type}:{boundary}"
    )
    
    email = account["email"]
    password = account["password"]
    
    with allure.step(f"账号信息: {boundary}"):
        allure.attach(
            f"边界: {boundary}\n"
            f"邮箱长度: {len(email)}\n"
            f"邮箱前50字符: {email[:50]}...\n"
            f"用户名: {account.get('username', 'N/A')}\n"
            f"密码长度: {len(password)}",
            name="boundary_account_info",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写边界邮箱并登录"):
        po.fill_username_or_email_address(email)
        po.fill_password(password)
        step_shot(po, "step_before_login", full_page=True)
        
        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录结果"):
        current_url = page.url or ""
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)
        
        if has_any_error_ui(page):
            pytest.fail(f"边界账号登录失败: {boundary}，出现错误UI")
        
        if "/login" in current_url.lower() or "/account/login" in current_url.lower():
            fatal = detect_fatal_error_page(page)
            if fatal:
                pytest.fail(f"边界账号登录失败: {boundary}，触发致命错误: {fatal}")


# ═══════════════════════════════════════════════════════════════════════════════
# Password 边界登录测试
# ═══════════════════════════════════════════════════════════════════════════════

DESC_PASSWORD_BOUNDARY = """
测试点：
- 使用预先创建的边界密码账号进行真实登录
- 验证 127/128 字符密码能够正常登录成功

边界值：
- len_127: 最大-1（127 字符密码）
- len_128: 最大值（128 字符密码）
"""


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Password Boundary Login")
@allure.description(DESC_PASSWORD_BOUNDARY)
@pytest.mark.parametrize(
    "account_type,boundary",
    [
        pytest.param("password_boundary", "len_127", id="password_len_127"),
        pytest.param("password_boundary", "len_128", id="password_len_128"),
    ],
)
def test_p1_login_password_boundary(unauth_page: Page, account_type: str, boundary: str):
    """使用真实边界密码账号登录"""
    account = _get_boundary_account(account_type, boundary)
    if not account:
        pytest.skip(f"边界账号未创建: {account_type}:{boundary}，请先运行 create_boundary_accounts.py")
    
    page = unauth_page
    po = AccountLoginPage(page)
    
    attach_rule_source_note(
        f"test-data/boundary_accounts.json: {account_type}:{boundary}"
    )
    
    username = account["username"]
    password = account["password"]
    
    with allure.step(f"账号信息: {boundary}"):
        allure.attach(
            f"边界: {boundary}\n"
            f"用户名: {username}\n"
            f"邮箱: {account.get('email', 'N/A')}\n"
            f"密码长度: {len(password)}",
            name="boundary_account_info",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("导航到登录页"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写边界密码账号并登录"):
        po.fill_username_or_email_address(username)
        po.fill_password(password)
        step_shot(po, "step_before_login", full_page=True)
        
        po.click_login()
        page.wait_for_timeout(2000)
        step_shot(po, "step_after_login", full_page=True)

    with allure.step("验证登录结果"):
        current_url = page.url or ""
        allure.attach(current_url, name="final_url", attachment_type=allure.attachment_type.TEXT)
        
        if has_any_error_ui(page):
            pytest.fail(f"边界账号登录失败: {boundary}，出现错误UI")
        
        if "/login" in current_url.lower() or "/account/login" in current_url.lower():
            fatal = detect_fatal_error_page(page)
            if fatal:
                pytest.fail(f"边界账号登录失败: {boundary}，触发致命错误: {fatal}")
