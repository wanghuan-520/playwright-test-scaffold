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
    wait_mutation_response,
)


def _unique_suffix(xdist_worker_id: Optional[str] = None) -> str:
    wid = (xdist_worker_id or "").strip() or "master"
    ts = str(int(time.time() * 1000))[-8:]
    return f"{wid}_{ts}_{uuid.uuid4().hex[:6]}"


def _ensure_register_page(page: Page, po: AccountRegisterPage) -> None:
    """
    复用 Register 页，降低每个参数化 case 都 Page.goto 的压力。
    - 若 submit 导致跳转/错误页，则重新导航
    """
    try:
        if page.locator(po.USERNAME_INPUT).count() > 0:
            return
    except Exception:
        pass
    po.navigate()
    page.wait_for_timeout(200)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email Format Matrix")
@allure.description(
    """
对齐参考用例（ui-automation/aevatar_station/test_register.py 邮箱验证矩阵）：
- emailAddress 的 format=email 应被前端/后端拦截
- 每个场景：截图 + 校验证据（validationMessage / error UI / 4xx）

规则来源：docs/requirements/requirements.md（Register.emailAddress format=email）

Baseline 输入（每条 case 初始值）：\n
- Username：em_{workerId}_{timestamp}_{uuid}\n
- Email：<invalid_email>\n
- Password：ValidPass123!\n
\n
判据：必须出现至少一种可观测证据：\n
- validationMessage（浏览器原生）\n
- error UI（页面校验提示/summary/toast）\n
- 后端 4xx（若校验落在后端）\n
"""
)
@pytest.mark.parametrize(
    "case_name,email",
    [
        ("email_no_at", "not-an-email"),
        ("email_only_at", "@t.com"),
        ("email_missing_domain", "a@"),
        # NOTE: "a@t" 可能被部分实现视为可接受邮箱（正则/浏览器差异大），避免制造误报
        ("email_double_at", "a@@t.com"),
        ("email_space", "a b@t.com"),
        ("email_double_dot", "a@t..com"),
    ],
)
def test_p1_register_email_invalid_format_matrix_should_show_evidence(
    unauth_page: Page, xdist_worker_id: str, case_name: str, email: str
):
    attach_rule_source_note("reference: ui-automation/tests/aevatar_station/test_register.py (invalid email matrix)")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step(f"[{case_name}] baseline + 填写无效邮箱并提交（应被拦截）"):
        _ensure_register_page(page, po)
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_navigate", full_page=True)

        suf = _unique_suffix(xdist_worker_id)
        po.fill_username(f"em_{suf}")
        po.fill_email_address(email)
        po.fill_password("ValidPass123!")
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        assert not fatal, f"[{case_name}] fatal error page detected: {fatal}"

        # 证据：优先 validationMessage，其次 error UI，其次 4xx
        msg = get_validation_message(page, po.EMAIL_ADDRESS_INPUT)
        if msg:
            allure.attach(msg, name=f"{case_name}_validationMessage", attachment_type=allure.attachment_type.TEXT)
        resp = wait_mutation_response(page, timeout_ms=1500)
        if resp is not None:
            assert resp.status < 500, f"[{case_name}] unexpected 5xx status={resp.status}"

        assert "/Account/Register" in (page.url or ""), f"[{case_name}] unexpected navigation: {page.url}"
        assert msg or has_any_error_ui(page) or (resp is not None and 400 <= resp.status < 500), (
            f"[{case_name}] expected validation evidence (validationMessage/error UI/4xx)"
        )


