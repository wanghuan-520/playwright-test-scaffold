"""
Change Password - Security

优化说明：
- 拆分为参数化测试，每个独立测试点×每种payload类型
- 2个独立测试点 × 2种payload类型 = 4个独立test
- new_password和confirm_password必须相同，合并为一个测试点
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from utils.logger import TestLogger

from tests.admin.profile.change_password._helpers import attach_no_dialog_guard, step_shot


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Change Password")
@allure.story("security - auth")
@allure.description(
    """
前端限制：
- 无（未登录状态无法访问前端应用）

后端限制：
- /admin/profile/change-password 需要认证
- 未登录访问自动重定向到 /auth/login 或 /account/login

测试点：
- 未登录状态访问 change password 页面
- 预期：重定向到登录页

断言：
- page_obj.is_login_page() = true
- 或 URL 包含 /auth/login 或 /account/login
    """
)
def test_security_unauth_access_should_redirect_to_login(unauth_page: Page):
    logger = TestLogger("test_security_unauth_access_should_redirect_to_login")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(unauth_page)
    with allure.step("未登录访问 /admin/profile/change-password"):
        page_obj.navigate()
        step_shot(page_obj, "step_navigate_unauth")

    assert page_obj.is_login_page() or ("/auth/login" in (unauth_page.url or "").lower()) or ("/account/login" in (unauth_page.url or "").lower()), (
        f"expected redirect to login for unauth access, got url={unauth_page.url}"
    )
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# XSS Payload 测试参数化
# ═══════════════════════════════════════════════════════════════
def _xss_test_scenarios():
    """
    生成XSS测试场景：2个独立测试点
    - current_password (独立)
    - new_password + confirm_password (强绑定，必须相同)
    """
    xss_payload = "<img src=x onerror=alert(1)>"
    
    scenarios = [
        ("current_password", xss_payload),
        ("new_and_confirm_password", xss_payload),  # 合并new_password和confirm_password
    ]
    
    return [
        pytest.param(field, payload, id=f"xss_{field}")
        for field, payload in scenarios
    ]


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Change Password")
@allure.story("security - XSS")
@allure.description(
    """
测试点（XSS）：
- current_password: 独立注入XSS payload
- new_password + confirm_password: 同时注入相同的XSS payload（因为两者必须相同）
- 断言：不弹dialog、不异常跳转、不崩溃
- 证据：注入前后截图
"""
)
@pytest.mark.parametrize(
    "field,payload",
    _xss_test_scenarios(),
)
def test_security_xss_payload_should_not_execute(
    auth_page: Page,
    field: str,
    payload: str,
):
    logger = TestLogger(f"test_security_xss_payload_should_not_execute[{field}]")
    logger.start()

    dialog_seen = attach_no_dialog_guard(auth_page)

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step(f"[{field}] 注入XSS payload并提交"):
        # 关键：先清空表单，避免上一个测试的残留内容
        page_obj.clear_form()
        auth_page.wait_for_timeout(200)  # 等待清空操作完成
        
        # 填充所有字段（控制变量法：只有目标字段是payload，其他字段填dummy）
        if field == "current_password":
            # 测试current_password：注入payload到current_password，new和confirm保持一致的dummy值
            page_obj.fill_form(
                current_password=payload,
                new_password="Dummy123!",
                confirm_password="Dummy123!"  # new和confirm必须相同
            )
        else:  # new_and_confirm_password
            # 测试new_password+confirm_password：同时注入相同的payload
            page_obj.fill_form(
                current_password="Dummy123!",
                new_password=payload,
                confirm_password=payload  # 必须与new_password相同
            )
        
        auth_page.wait_for_timeout(300)  # 等待填充完成，确保截图准确
        step_shot(page_obj, f"step_{field}_filled_xss")
        page_obj.click_save()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, f"step_{field}_result_xss")

    # 断言
    assert dialog_seen.get("type") is None, f"[{field}] XSS should not execute dialog, but saw: {dialog_seen}"
    assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login"
    assert page_obj.is_loaded(), f"[{field}] page should remain usable"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# SQLi Payload 测试参数化
# ═══════════════════════════════════════════════════════════════
def _sqli_test_scenarios():
    """
    生成SQLi测试场景：2个独立测试点
    - current_password (独立)
    - new_password + confirm_password (强绑定，必须相同)
    """
    sqli_payload = "' OR 1=1 --"
    
    scenarios = [
        ("current_password", sqli_payload),
        ("new_and_confirm_password", sqli_payload),  # 合并new_password和confirm_password
    ]
    
    return [
        pytest.param(field, payload, id=f"sqli_{field}")
        for field, payload in scenarios
    ]


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Change Password")
@allure.story("security - SQLi")
@allure.description(
    """
测试点（SQLi 风格输入）：
- current_password: 独立注入SQLi payload
- new_password + confirm_password: 同时注入相同的SQLi payload（因为两者必须相同）
- 断言：不异常跳转、不崩溃
- 证据：注入前后截图
"""
)
@pytest.mark.parametrize(
    "field,payload",
    _sqli_test_scenarios(),
)
def test_security_sqli_style_input_does_not_crash(
    auth_page: Page,
    field: str,
    payload: str,
):
    logger = TestLogger(f"test_security_sqli_style_input_does_not_crash[{field}]")
    logger.start()

    page_obj = AdminProfileChangePasswordPage(auth_page)
    page_obj.navigate()

    with allure.step(f"[{field}] 注入SQLi payload并提交"):
        # 关键：先清空表单，避免上一个测试的残留内容
        page_obj.clear_form()
        auth_page.wait_for_timeout(200)  # 等待清空操作完成
        
        # 填充所有字段（控制变量法）
        if field == "current_password":
            # 测试current_password：注入payload到current_password，new和confirm保持一致的dummy值
            page_obj.fill_form(
                current_password=payload,
                new_password="Dummy123!",
                confirm_password="Dummy123!"  # new和confirm必须相同
            )
        else:  # new_and_confirm_password
            # 测试new_password+confirm_password：同时注入相同的payload
            page_obj.fill_form(
                current_password="Dummy123!",
                new_password=payload,
                confirm_password=payload  # 必须与new_password相同
            )
        
        auth_page.wait_for_timeout(300)  # 等待填充完成，确保截图准确
        step_shot(page_obj, f"step_{field}_filled_sqli")
        page_obj.click_save()
        auth_page.wait_for_timeout(600)
        step_shot(page_obj, f"step_{field}_result_sqli")

    # 断言
    assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login"
    assert page_obj.is_loaded(), f"[{field}] page should remain usable"

    logger.end(success=True)
