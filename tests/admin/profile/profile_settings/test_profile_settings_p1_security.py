# ═══════════════════════════════════════════════════════════════
# Profile Settings (Personal Settings) - Security
# ═══════════════════════════════════════════════════════════════
"""
Security：字段维度最小载荷集（XSS/SQLi），核心断言：
- 不弹 dialog（XSS 不执行）
- 不异常跳转（不被踢出登录，除非本身未登录场景）
- 提交后不应出现 5xx 级"崩溃态"（这里以"页面仍可用 + 未崩溃"为主）

优化：拆分为参数化测试，每个字段独立执行，便于并行和精准定位
"""

import pytest
import allure
from playwright.sync_api import Page

from utils.logger import TestLogger
from tests.admin.profile._helpers import (
    attach_rule_source_note,
    assert_no_dialog,
    step_shot,
    abp_profile_put,
    settle_toasts,
    attach_backend_text,
)


# ═══════════════════════════════════════════════════════════════
# XSS Payload 测试参数化
# ═══════════════════════════════════════════════════════════════
def _xss_test_scenarios():
    """
    生成XSS测试场景：5个字段独立测试
    - userName/email: 应被前端拦截
    - name/surname/phoneNumber: 允许提交但不执行
    """
    xss_payload = '<img src=x onerror=alert(1) />'
    
    scenarios = [
        ("userName", "USERNAME_INPUT", {"userName": f"bad<{xss_payload}>"}, True, False),
        ("email", "EMAIL_INPUT", {"email": f"bad{xss_payload}"}, True, True),
        ("name", "NAME_INPUT", {"name": xss_payload}, False, False),
        ("surname", "SURNAME_INPUT", {"surname": xss_payload}, False, False),
        ("phoneNumber", "PHONE_INPUT", {"phoneNumber": xss_payload}, False, False),
    ]
    
    return [
        pytest.param(field, selector_attr, patch, should_block, need_validation, id=f"xss_{field}")
        for field, selector_attr, patch, should_block, need_validation in scenarios
    ]


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Profile Settings")
@allure.story("Security - XSS Injection")
@allure.description(
    """
测试点（XSS）- 单字段版本：
- userName/email：必须前端拦截（不发 profileUpdate）+ 有可见错误证据
- name/surname/phoneNumber：允许提交但必须不执行脚本/不崩溃/不污染数据
- 证据：提交前后关键截图
"""
)
@pytest.mark.parametrize(
    "field,selector_attr,patch,should_block,need_validation",
    _xss_test_scenarios(),
)
def test_security_xss_payload_does_not_execute(
    profile_settings,
    field: str,
    selector_attr: str,
    patch: dict,
    should_block: bool,
    need_validation: bool,
):
    """
    Security: XSS payload 不执行（无 dialog）- 单字段测试
    """
    attach_rule_source_note()
    logger = TestLogger(f"test_security_xss_payload_does_not_execute[{field}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    selector = getattr(page_obj, selector_attr)

    # Dialog监听
    dialog_seen = {"type": None, "message": None}

    def on_dialog(d):
        dialog_seen["type"] = d.type
        dialog_seen["message"] = d.message
        try:
            d.dismiss()
        except Exception:
            pass

    auth_page.on("dialog", on_dialog)

    def _assert_frontend_blocked(validation_message_required: bool) -> None:
        """断言：不发 profileUpdate + 有错误证据"""
        blocked = page_obj.wait_for_profile_update_response(timeout_ms=1500)
        assert blocked is None, f"[{field}] frontend should block (no profileUpdate request expected)"

        has_visible = False
        try:
            evidence = auth_page.eval_on_selector(
                selector,
                """el => {
  const ariaInvalid = el.getAttribute('aria-invalid') || '';
  const className = (el.className || '').toString();
  const ariaDescribedBy = el.getAttribute('aria-describedby') || '';
  const described = ariaDescribedBy ? (document.getElementById(ariaDescribedBy)?.innerText || '') : '';
  const msg = (el.validationMessage || '').toString();
  return { ariaInvalid, className, ariaDescribedBy, described, validationMessage: msg };
}""",
            )
            if str((evidence or {}).get("validationMessage") or "").strip():
                has_visible = True
            if str((evidence or {}).get("ariaInvalid") or "").lower() == "true":
                has_visible = True
            if str((evidence or {}).get("described") or "").strip():
                has_visible = True
            cls_low = str((evidence or {}).get("className") or "").lower()
            if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
                has_visible = True
        except Exception:
            pass

        if field == "email":
            try:
                if auth_page.get_by_text("Email is required").is_visible(timeout=300):
                    has_visible = True
            except Exception:
                pass

        if validation_message_required and not has_visible:
            assert False, f"[{field}] expected visible error evidence"

        assert has_visible, f"[{field}] expected visible error evidence"

    # 执行测试
    with allure.step(f"[{field}] 填写并提交 XSS payload"):
        settle_toasts(page_obj)
        page_obj.fill_form(patch)
        
        if field in ("userName", "email"):
            try:
                auth_page.locator(selector).blur()
            except Exception:
                pass
        
        step_shot(page_obj, f"step_{field}_filled_xss")
        resp = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
        
        if resp is not None and (not resp.ok):
            attach_backend_text(f"profile_update_status_{field}", str(getattr(resp, "status", None)))
        
        auth_page.wait_for_timeout(500)
        
        if field == "email":
            try:
                auth_page.eval_on_selector(page_obj.EMAIL_INPUT, "el => el.reportValidity && el.reportValidity()")
            except Exception:
                pass
        
        step_shot(page_obj, f"step_{field}_result_xss")

    # 断言（不在Allure steps中显示）
    assert_no_dialog(auth_page, dialog_seen)
    assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login"
    assert page_obj.is_loaded(), f"[{field}] page should remain usable"

    if should_block:
        _assert_frontend_blocked(validation_message_required=need_validation)
        # 回填UI
        page_obj.fill_form({field: baseline.get(field, "")})
        assert_no_dialog(auth_page, dialog_seen)
    else:
        # 可选字段：检查不污染
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        assert page_obj.is_loaded(), f"[{field}] reload after submit should be ok"
        current = page_obj.read_form_values()
        if (current.get(field) or "") != (baseline.get(field) or ""):
            r = abp_profile_put(auth_page, baseline, {})
            attach_backend_text(f"force_restore_via_api_{field}", str(r))
            assert r.get("ok"), f"[{field}] restore blocked"
            auth_page.reload()
            auth_page.wait_for_timeout(800)
            current2 = page_obj.read_form_values()
            assert (current2.get(field) or "") == (baseline.get(field) or ""), f"[{field}] should not be polluted after restore"

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# SQLi Payload 测试参数化
# ═══════════════════════════════════════════════════════════════
def _sqli_test_scenarios():
    """
    生成SQLi测试场景：5个字段独立测试
    """
    sqli_payload = "' OR 1=1 --"
    
    scenarios = [
        ("userName", "USERNAME_INPUT", {"userName": sqli_payload}, True, False),
        ("email", "EMAIL_INPUT", {"email": f"bad{sqli_payload}"}, True, True),
        ("name", "NAME_INPUT", {"name": sqli_payload}, False, False),
        ("surname", "SURNAME_INPUT", {"surname": sqli_payload}, False, False),
        ("phoneNumber", "PHONE_INPUT", {"phoneNumber": sqli_payload}, False, False),
    ]
    
    return [
        pytest.param(field, selector_attr, patch, should_block, need_validation, id=f"sqli_{field}")
        for field, selector_attr, patch, should_block, need_validation in scenarios
    ]


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Profile Settings")
@allure.story("Security - SQLi Injection")
@allure.description(
    """
测试点（SQLi 风格输入）- 单字段版本：
- userName/email：必须前端拦截（不发 profileUpdate）+ 有可见错误证据
- name/surname/phoneNumber：允许提交但必须不崩溃/不污染数据
- 证据：提交前后关键截图
"""
)
@pytest.mark.parametrize(
    "field,selector_attr,patch,should_block,need_validation",
    _sqli_test_scenarios(),
)
def test_security_sqli_style_input_does_not_crash(
    profile_settings,
    field: str,
    selector_attr: str,
    patch: dict,
    should_block: bool,
    need_validation: bool,
):
    """
    Security: SQLi 风格输入不导致异常行为 - 单字段测试
    """
    attach_rule_source_note()
    logger = TestLogger(f"test_security_sqli_style_input_does_not_crash[{field}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    selector = getattr(page_obj, selector_attr)

    def _assert_frontend_blocked(validation_message_required: bool) -> None:
        blocked = page_obj.wait_for_profile_update_response(timeout_ms=1500)
        assert blocked is None, f"[{field}] frontend should block (no profileUpdate request expected)"
        
        has_visible = False
        try:
            evidence = auth_page.eval_on_selector(
                selector,
                """el => {
  const ariaInvalid = el.getAttribute('aria-invalid') || '';
  const className = (el.className || '').toString();
  const ariaDescribedBy = el.getAttribute('aria-describedby') || '';
  const described = ariaDescribedBy ? (document.getElementById(ariaDescribedBy)?.innerText || '') : '';
  const msg = (el.validationMessage || '').toString();
  return { ariaInvalid, className, ariaDescribedBy, described, validationMessage: msg };
}""",
            )
            if str((evidence or {}).get("validationMessage") or "").strip():
                has_visible = True
            if str((evidence or {}).get("ariaInvalid") or "").lower() == "true":
                has_visible = True
            if str((evidence or {}).get("described") or "").strip():
                has_visible = True
            cls_low = str((evidence or {}).get("className") or "").lower()
            if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
                has_visible = True
        except Exception:
            pass
        
        if validation_message_required and not has_visible:
            assert False, f"[{field}] expected visible error evidence"
        assert has_visible, f"[{field}] expected visible error evidence"

    # 执行测试
    with allure.step(f"[{field}] 填写并提交 SQLi payload"):
        settle_toasts(page_obj)
        page_obj.fill_form(patch)
        
        if field in ("userName", "email"):
            try:
                auth_page.locator(selector).blur()
            except Exception:
                pass
        
        step_shot(page_obj, f"step_{field}_filled_sqli")
        resp = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
        
        if resp is not None and (not resp.ok):
            attach_backend_text(f"profile_update_status_{field}", str(getattr(resp, "status", None)))
        
        auth_page.wait_for_timeout(600)
        step_shot(page_obj, f"step_{field}_result_sqli")

    # 断言
    assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login"
    assert page_obj.is_loaded(), f"[{field}] page should remain usable"

    if should_block:
        _assert_frontend_blocked(validation_message_required=need_validation)
        page_obj.fill_form({field: baseline.get(field, "")})
    else:
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        
        if not page_obj.is_loaded():
            try:
                page_obj.navigate()
                auth_page.wait_for_timeout(500)
            except Exception:
                pass
        
        assert page_obj.is_loaded(), f"[{field}] reload after submit should be ok"
        current = page_obj.read_form_values()
        if (current.get(field) or "") != (baseline.get(field) or ""):
            r = abp_profile_put(auth_page, baseline, {})
            attach_backend_text(f"force_restore_via_api_{field}", str(r))
            assert r.get("ok"), f"[{field}] restore blocked"
            auth_page.reload()
            auth_page.wait_for_timeout(800)
            current2 = page_obj.read_form_values()
            assert (current2.get(field) or "") == (baseline.get(field) or ""), f"[{field}] should not be polluted after restore"

    logger.end(success=True)
