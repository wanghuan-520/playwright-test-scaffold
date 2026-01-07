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
    has_any_error_ui,
    wait_response_by_url_substring,
)


def _unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


@pytest.mark.P1
@pytest.mark.exception
@allure.feature("AccountRegister")
@allure.story("P1 - Duplicate Data")
@allure.description(
    """
对齐参考用例（ui-automation/aevatar_station/test_register.py）：
- 重复邮箱/重复用户名应被拦截
- 证据：每次提交前后截图 + 关键响应状态/错误区域

规则来源：
- docs/requirements/requirements.md（Register：userName/email required + maxLength + email format；重复性属于业务约束）
"""
)
@pytest.mark.parametrize("kind", ["email", "username"])
def test_p1_register_duplicate_username_or_email_should_be_blocked(unauth_page: Page, xdist_worker_id: str, kind: str):
    attach_rule_source_note("reference: ui-automation/tests/aevatar_station/test_register.py (duplicate email/username)")
    page = unauth_page
    po = AccountRegisterPage(page)

    def _register_once(username: str, email: str, password: str, *, case_name: str) -> Optional[int]:
        po.navigate()
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_navigate", full_page=True)

        po.fill_username(username)
        po.fill_email_address(email)
        po.fill_password(password)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        # 可能是 form submit 或被前端阻断；避免长等待
        resp = None
        try:
            resp = wait_response_by_url_substring(page, "/api/account/register", timeout_ms=2500)
        except Exception:
            resp = None
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        assert not fatal, f"[{case_name}] fatal error page detected: {fatal}"
        return resp.status if resp is not None else None

    base_suffix = _unique_suffix(xdist_worker_id)
    password = "ValidPass123!"

    case_name = f"duplicate_{kind}"

    with allure.step(f"[{case_name}] 先创建一个新账号（作为重复基准）"):
        u1 = f"dup_{base_suffix}_{case_name}_u1"
        e1 = f"dup_{base_suffix}_{case_name}@testmail.com"
        s1 = _register_once(u1, e1, password, case_name=f"{case_name}_first")
        allure.attach(
            f"first_register_status={s1}",
            name=f"{case_name}_first_register_status",
            attachment_type=allure.attachment_type.TEXT,
        )
        # 宽松：resp 可能抓不到，但至少不应出现 error UI（否则无法形成“重复基准”）
        assert not has_any_error_ui(page), f"[{case_name}] first register unexpected error UI"

    with allure.step(f"[{case_name}] 使用重复字段再次注册（期望被拦截）"):
        # second attempt: change the other field to avoid double-duplicate ambiguity
        u2 = f"dup_{base_suffix}_{case_name}_u2"
        e2 = f"dup_{base_suffix}_{case_name}_2@testmail.com"
        if kind == "email":
            u = u2
            e = e1  # duplicate email
        else:
            u = u1  # duplicate username
            e = e2
        s2 = _register_once(u, e, password, case_name=f"{case_name}_second")

        # 证据：响应码（若能抓到）+ 错误 UI（或留在本页）
        if s2 is not None:
            assert s2 < 500, f"[{case_name}] unexpected 5xx status={s2}"

        # 期望：仍停留在 Register 页（或出现明确错误 UI）
        assert "/Account/Register" in (page.url or ""), f"[{case_name}] unexpected navigation: {page.url}"
        assert has_any_error_ui(page) or (s2 is not None and 400 <= s2 < 500), (
            f"[{case_name}] expected duplicate to be blocked (error UI or 4xx), got status={s2}"
        )


