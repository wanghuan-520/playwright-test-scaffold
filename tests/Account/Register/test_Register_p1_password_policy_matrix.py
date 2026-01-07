import allure
import pytest
import time
import uuid
from typing import Optional
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Register._helpers import (
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
    get_validation_message,
    has_any_error_ui,
    wait_response_by_url_substring,
)


def _unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


@pytest.mark.P1
@pytest.mark.security
@allure.feature("AccountRegister")
@allure.story("P1 - Password Policy Matrix")
@allure.description(
    """
对齐参考用例（ui-automation/aevatar_station/test_register.py ABP密码策略）：
- 不符合密码策略的密码必须被拦截（前端可观测 + 或后端 4xx）
- 每个场景：截图 + 响应码/错误UI

规则来源：docs/requirements/requirements.md（Identity PasswordPolicy）

Baseline 输入（每条 case 初始值）：\n
- Username：pwd_{workerId}_{timestamp}_{uuid}\n
- Email：pwd_{workerId}_{timestamp}_{uuid}@testmail.com\n
- Password：<weak_password>\n
\n
判据：必须出现至少一种拦截证据：\n
- Password 输入框 validationMessage\n
- error UI\n
- 后端 4xx（若校验落在后端）\n
"""
)
@pytest.mark.parametrize(
    "case_name,pwd",
    [
        ("missing_digit", "ValidPass!!!"),
        ("missing_uppercase", "validpass123!"),
        ("missing_lowercase", "VALIDPASS123!"),
        ("missing_non_alphanumeric", "ValidPass123"),
        ("too_short_5", "Aa1!a"),  # 5
    ],
)
def test_p1_register_password_policy_should_reject_weak_passwords(
    unauth_page: Page, xdist_worker_id: str, case_name: str, pwd: str
):
    attach_rule_source_note("reference: ui-automation/tests/aevatar_station/test_register.py (password policy matrix)")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step(f"[{case_name}] baseline + 填写弱密码并提交（应被拦截）"):
        po.navigate()
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_navigate", full_page=True)

        suf = _unique_suffix(xdist_worker_id)
        po.fill_username(f"pwd_{suf}")
        po.fill_email_address(f"pwd_{suf}@testmail.com")
        po.fill_password(pwd)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        # 可能被前端原生校验阻断（无网络请求），避免长等待
        resp = None
        try:
            resp = wait_response_by_url_substring(page, "/api/account/register", timeout_ms=2500)
        except Exception:
            resp = None
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        assert not fatal, f"[{case_name}] fatal error page detected: {fatal}"

        msg = get_validation_message(page, po.PASSWORD_INPUT)
        if msg:
            allure.attach(msg, name=f"{case_name}_validationMessage", attachment_type=allure.attachment_type.TEXT)

        if resp is not None:
            assert resp.status < 500, f"[{case_name}] unexpected 5xx status={resp.status}"

        # 拦截判据：留在注册页 + (validationMessage / error UI / 4xx)
        assert "/Account/Register" in (page.url or ""), f"[{case_name}] unexpected navigation: {page.url}"
        assert msg or has_any_error_ui(page) or (resp is not None and 400 <= resp.status < 500), (
            f"[{case_name}] expected rejection evidence (validationMessage/error UI/4xx), got status={getattr(resp,'status',None)}"
        )


