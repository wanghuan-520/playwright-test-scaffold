import uuid

import allure
import pytest
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from .test_Register_known_bugs import BUG_REG_REQUIRED_EMPTY_500, bug_reason, bug_xfail
from tests.Account.Register import _abp_constraints_helpers as H
from tests.Account.Register._helpers import assert_not_redirected_to_login, click_save
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from utils.logger import TestLogger

logger = TestLogger("Register_p1_abp_constraints")


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - ABP Constraints (UI)")
@allure.description(H.DESC_MAXLENGTH_EVIDENCE)
def test_p1_register_ui_maxlength_evidence(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Register UI constraints (scenarios in steps)")

    page = unauth_page
    po = AccountRegisterPage(page)
    with allure.step("导航到 /Account/Register"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("前端 maxlength 取证：超长输入应被截断/阻止在 max 以内"):
        fields = [
            ("username", po.USERNAME_INPUT, H.ABP_MAX_LEN_COMMON),
            ("email", po.EMAIL_ADDRESS_INPUT, H.ABP_MAX_LEN_COMMON),
            ("password", po.PASSWORD_INPUT, H.ABP_PASSWORD_MAX),
        ]
        for field, selector, expected_max in fields:
            maxlength_attr = H.get_maxlength_attr(page, selector)
            long_text = ("x" * (expected_max + 10)) if field != "email" else (("a" * (expected_max + 5)) + "@t.com")
            page.fill(selector, long_text)
            page.wait_for_timeout(100)
            actual = page.input_value(selector)
            allure.attach(
                f"field={field}\nmaxlength_attr={maxlength_attr!r}\ntyped_len={len(long_text)}\nactual_len={len(actual)}\nexpected_max={expected_max}\n",
                name=f"{field}_maxlength_evidence",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(po, f"step_{field}_maxlength_evidence", full_page=True)
            assert len(actual) <= expected_max, f"{field}: expected <= {expected_max}, got {len(actual)} (maxlength={maxlength_attr!r})"


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Required attribute evidence")
@allure.description(H.DESC_REQUIRED_ATTR_EVIDENCE)
@pytest.mark.parametrize(
    "field, selector",
    [
        ("username", "USERNAME_INPUT"),
        ("email", "EMAIL_ADDRESS_INPUT"),
        ("password", "PASSWORD_INPUT"),
    ],
)
def test_p1_register_ui_required_attr_evidence(unauth_page: Page, field: str, selector: str):
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = f"required_attr_{field}"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    sel = getattr(po, selector)
    required = H.get_attr(page, sel, "required")
    aria_required = H.get_attr(page, sel, "aria-required")
    data_val_required = H.get_attr(page, sel, "data-val-required")
    allure.attach(
        f"field={field}\nselector={sel}\nrequired={required!r}\naria-required={aria_required!r}\ndata-val-required={data_val_required!r}\n",
        name=f"{case_name}_attrs",
        attachment_type=allure.attachment_type.TEXT,
    )
    step_shot(po, f"step_{case_name}", full_page=True)

    if not any([required, aria_required, data_val_required]):
        pytest.xfail(f"{bug_reason(BUG_REG_REQUIRED_EMPTY_500)} | {case_name}: no observable required marker on frontend")


@pytest.mark.P1
@pytest.mark.validation
# 已知Bug不再使用 xfail，直接让用例失败（已知Bug应该在报告里"刺眼地显示为失败"）
# @bug_xfail(BUG_REG_REQUIRED_EMPTY_500, strict=False)
@allure.feature("AccountRegister")
@allure.story("Known Bugs - Required empty should not 500")
@allure.description(H.DESC_REQUIRED_EMPTY_KNOWN_BUG)
@pytest.mark.parametrize("field, selector", [("username", "USERNAME_INPUT"), ("email", "EMAIL_ADDRESS_INPUT"), ("password", "PASSWORD_INPUT")])
def test_bug_register_required_empty_should_not_500(unauth_page: Page, field: str, selector: str):
    attach_rule_source_note("docs/requirements/requirements.md: Register required fields must be validated (no 500)")
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = f"required_{field}_empty"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] baseline + 清空字段并提交（不应 500）"):
        H.fill_baseline(po, suffix="baseline")
        H.set_field(po, field, "")
        step_shot(po, f"step_{case_name}_filled", full_page=True)
        click_save(page)
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    H.assert_no_fatal_error(page, case_name=case_name)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Password min length evidence")
@allure.description(H.DESC_PASSWORD_MIN_EVIDENCE)
def test_p1_register_password_min_length_should_show_validation_evidence(unauth_page: Page):
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = "password_min_len_5"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] baseline + 填入 len=5 密码并提交"):
        H.fill_baseline(po, suffix=uuid.uuid4().hex[:10])
        H.set_field(po, "password", "Aa1!a")  # len=5，仅违反 min=6
        step_shot(po, f"step_{case_name}_filled", full_page=True)
        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    H.assert_no_fatal_error(page, case_name=case_name)
    H.attach_register_payload_lens(resp, name=f"{case_name}_register_request_payload_lens")
    H.assert_validation_evidence(page, po.PASSWORD_INPUT, case_name=case_name)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Username length boundaries")
@allure.description(H.DESC_USERNAME_BOUNDARY)
@pytest.mark.parametrize("total_len", [H.ABP_MAX_LEN_COMMON - 1, H.ABP_MAX_LEN_COMMON])
def test_p1_register_username_length_boundaries(unauth_page: Page, total_len: int):
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = f"username_len_{total_len}"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    suffix = uuid.uuid4().hex[:10]
    value = ""
    with allure.step(f"[{case_name}] baseline + 填 username"):
        H.fill_baseline(po, suffix=suffix)
        value = H.mk_username_with_len(total_len, suffix)
        H.set_field(po, "username", value)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

    actual_len = H.read_input_len(page, po.USERNAME_INPUT)
    assert actual_len == total_len, f"{case_name}: expected input_len={total_len}, got {actual_len}"

    expect_ok = total_len in {H.ABP_MAX_LEN_COMMON - 1, H.ABP_MAX_LEN_COMMON}

    with allure.step(f"[{case_name}] 提交注册并断言结果"):
        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=2000 if expect_ok else 3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)
        H.attach_register_payload_lens(resp, name=f"{case_name}_register_request_payload_lens")

        if expect_ok:
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
                assert resp.status < 400, f"{case_name}: expected success (non-4xx) but got {resp.status}"
            assert not H.has_any_error_ui(page), f"{case_name}: unexpected error UI"
        else:
            H.assert_validation_evidence(page, po.USERNAME_INPUT, case_name=case_name)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email length boundaries")
@allure.description(H.DESC_EMAIL_BOUNDARY)
@pytest.mark.parametrize("total_len", [H.ABP_MAX_LEN_COMMON - 1, H.ABP_MAX_LEN_COMMON])
def test_p1_register_email_length_boundaries(unauth_page: Page, total_len: int):
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = f"email_len_{total_len}"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    suffix = uuid.uuid4().hex[:10]
    value = ""
    with allure.step(f"[{case_name}] baseline + 填 email"):
        H.fill_baseline(po, suffix=suffix)
        value = H.mk_email_with_len(total_len, suffix)
        H.set_field(po, "email", value)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

    actual_len = H.read_input_len(page, po.EMAIL_ADDRESS_INPUT)
    assert actual_len == total_len, f"{case_name}: expected input_len={total_len}, got {actual_len}"

    expect_ok = total_len in {H.ABP_MAX_LEN_COMMON - 1, H.ABP_MAX_LEN_COMMON}

    with allure.step(f"[{case_name}] 提交注册并断言结果"):
        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=2000 if expect_ok else 3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)
        H.attach_register_payload_lens(resp, name=f"{case_name}_register_request_payload_lens")

        if expect_ok:
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
                assert resp.status < 400, f"{case_name}: expected success (non-4xx) but got {resp.status}"
            assert not H.has_any_error_ui(page), f"{case_name}: unexpected error UI"
        else:
            H.assert_validation_evidence(page, po.EMAIL_ADDRESS_INPUT, case_name=case_name)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Password length boundaries")
@allure.description(H.DESC_PASSWORD_BOUNDARY)
@pytest.mark.parametrize("total_len", [H.ABP_PASSWORD_MAX - 1, H.ABP_PASSWORD_MAX])
def test_p1_register_password_length_boundaries(unauth_page: Page, total_len: int):
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = f"password_len_{total_len}"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    suffix = uuid.uuid4().hex[:10]
    value = ""
    with allure.step(f"[{case_name}] baseline + 填 password"):
        if total_len < 4:
            value = "a1!a"
        else:
            value = ("A" * (total_len - 4)) + "a1!a"
        H.fill_baseline(po, suffix=suffix)
        H.set_field(po, "password", value)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

    actual_len = H.read_input_len(page, po.PASSWORD_INPUT)
    assert actual_len == total_len, f"{case_name}: expected input_len={total_len}, got {actual_len}"

    expect_ok = total_len in {H.ABP_PASSWORD_MAX - 1, H.ABP_PASSWORD_MAX}

    with allure.step(f"[{case_name}] 提交注册并断言结果"):
        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=2000 if expect_ok else 3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)
        H.attach_register_payload_lens(resp, name=f"{case_name}_register_request_payload_lens")

        if expect_ok:
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
                assert resp.status < 400, f"{case_name}: expected success (non-4xx) but got {resp.status}"
            assert not H.has_any_error_ui(page), f"{case_name}: unexpected error UI"
        else:
            H.assert_validation_evidence(page, po.PASSWORD_INPUT, case_name=case_name)


