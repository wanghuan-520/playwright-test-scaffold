import allure
import pytest
import time
import uuid
from typing import Optional
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Login._helpers import (
    assert_not_redirected_to_login,
    detect_fatal_error_page,
    wait_mutation_response,
)


def _unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


@pytest.mark.P1
@pytest.mark.exception
@allure.feature("AccountLogin")
@allure.story("P1 - Invalid Credentials")
@allure.description(
    """
对齐参考用例（ui-automation/aevatar_station/test_login.py 无效凭证）：
- 使用不存在的用户名/邮箱 + 任意密码提交，必须不能登录
- 证据：提交前后截图 + 不跳转 + 不 5xx

注意：
- 为避免 lockout 风险：仅使用明显不存在的随机用户名；每次只提交一次。
"""
)
def test_p1_login_invalid_credentials_should_stay_on_login(unauth_page: Page, xdist_worker_id: str):
    attach_rule_source_note("reference: ui-automation/tests/aevatar_station/test_login.py (invalid credentials)")
    page = unauth_page
    po = AccountLoginPage(page)

    suf = _unique_suffix(xdist_worker_id)
    bogus_user = f"no_such_user_{suf}"
    bogus_pwd = f"BadPass_{uuid.uuid4().hex[:6]}!"

    with allure.step("导航到 /Account/Login"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("填写不存在的用户名 + 任意密码，并提交"):
        if page.locator("#LoginInput_UserNameOrEmailAddress").count() > 0:
            page.fill("#LoginInput_UserNameOrEmailAddress", bogus_user)
        if page.locator("#LoginInput_Password").count() > 0:
            page.fill("#LoginInput_Password", bogus_pwd)
        step_shot(po, "step_filled", full_page=True)

        page.click("button[name='Action'][type='submit']")
        resp = wait_mutation_response(page, timeout_ms=15000)
        page.wait_for_timeout(300)
        step_shot(po, "step_after_submit", full_page=True)

    fatal = detect_fatal_error_page(page)
    assert not fatal, f"fatal error page detected: {fatal}"

    if resp is not None:
        assert resp.status < 500, f"unexpected 5xx status={resp.status}"

    # 必须仍在登录页（不算成功登录/不跳转到前端）
    assert "/Account/Login" in (page.url or ""), f"expected stay on login page, got: {page.url}"


