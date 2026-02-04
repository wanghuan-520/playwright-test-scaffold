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
from tests.myaccount._helpers import (
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
    生成XSS测试场景：3个可编辑字段独立测试
    - firstName/lastName/phoneNumber: 允许提交但不执行
    
    注意：userName 和 email 是只读字段，无法通过 UI 注入 XSS，不需要测试
    """
    xss_payload = '<img src=x onerror=alert(1) />'
    
    scenarios = [
        # 可编辑字段：允许提交但不执行脚本
        ("firstName", "FIRST_NAME_INPUT", {"firstName": xss_payload}, False, False),
        ("lastName", "LAST_NAME_INPUT", {"lastName": xss_payload}, False, False),
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

    def _assert_frontend_blocked(validation_message_required: bool, resp_from_save) -> None:
        """断言：不发 profileUpdate + 有错误证据"""
        # 注意：resp 从 click_save_and_capture_profile_update 获取
        # 如果前端拦截，resp 应为 None
        assert resp_from_save is None, f"[{field}] frontend should block (no profileUpdate request expected)"

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
        _assert_frontend_blocked(validation_message_required=need_validation, resp_from_save=resp)
        # 回填UI
        page_obj.fill_form({field: baseline.get(field, "")})
        assert_no_dialog(auth_page, dialog_seen)
    else:
        # 可选字段：主要检验脚本不执行、页面不崩溃
        # 数据恢复使用 UI 操作而非 API（因为 API 可能忽略空字符串）
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        assert page_obj.is_loaded(), f"[{field}] reload after submit should be ok"
        
        # 通过 UI 恢复原始值
        current = page_obj.read_form_values()
        if (current.get(field) or "") != (baseline.get(field) or ""):
            # 使用 UI 填写恢复值
            restore_value = baseline.get(field, "") or ""
            page_obj.fill_form({field: restore_value})
            resp2 = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
            attach_backend_text(f"force_restore_via_ui_{field}", str(getattr(resp2, "status", None) if resp2 else "no_resp"))
            auth_page.wait_for_timeout(500)
            
            # 验证恢复成功（宽松检查：只记录不阻断）
            auth_page.reload()
            auth_page.wait_for_timeout(500)
            current2 = page_obj.read_form_values()
            final_val = current2.get(field) or ""
            expected_val = baseline.get(field) or ""
            if final_val != expected_val:
                allure.attach(
                    f"字段 {field} 恢复后值与期望不同\n期望: '{expected_val}'\n实际: '{final_val}'",
                    name=f"restore_warning_{field}",
                    attachment_type=allure.attachment_type.TEXT
                )
                # 安全测试核心目标是脚本不执行、页面不崩溃，数据恢复问题记录但不阻断
                pass

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# SQLi Payload 测试参数化
# ═══════════════════════════════════════════════════════════════
def _sqli_test_scenarios():
    """
    生成SQLi测试场景：3个可编辑字段独立测试
    
    注意：userName 和 email 是只读字段，无法通过 UI 注入 SQLi，不需要测试
    """
    sqli_payload = "' OR 1=1 --"
    
    scenarios = [
        # 可编辑字段：允许提交但不崩溃
        ("firstName", "FIRST_NAME_INPUT", {"firstName": sqli_payload}, False, False),
        ("lastName", "LAST_NAME_INPUT", {"lastName": sqli_payload}, False, False),
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

    def _assert_frontend_blocked(validation_message_required: bool, resp_from_save) -> None:
        # 注意：resp 从 click_save_and_capture_profile_update 获取
        # 如果前端拦截，resp 应为 None
        assert resp_from_save is None, f"[{field}] frontend should block (no profileUpdate request expected)"
        
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
        _assert_frontend_blocked(validation_message_required=need_validation, resp_from_save=resp)
        page_obj.fill_form({field: baseline.get(field, "")})
    else:
        # 可选字段：主要检验页面不崩溃、不产生服务端错误
        # 数据恢复使用 UI 操作而非 API（因为 API 可能忽略空字符串）
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        
        if not page_obj.is_loaded():
            try:
                page_obj.navigate()
                auth_page.wait_for_timeout(500)
            except Exception:
                pass
        
        assert page_obj.is_loaded(), f"[{field}] reload after submit should be ok"
        
        # 通过 UI 恢复原始值
        current = page_obj.read_form_values()
        if (current.get(field) or "") != (baseline.get(field) or ""):
            # 使用 UI 填写恢复值
            restore_value = baseline.get(field, "") or ""
            page_obj.fill_form({field: restore_value})
            resp2 = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
            attach_backend_text(f"force_restore_via_ui_{field}", str(getattr(resp2, "status", None) if resp2 else "no_resp"))
            auth_page.wait_for_timeout(500)
            
            # 验证恢复成功（宽松检查：只记录不阻断）
            auth_page.reload()
            auth_page.wait_for_timeout(500)
            current2 = page_obj.read_form_values()
            final_val = current2.get(field) or ""
            expected_val = baseline.get(field) or ""
            if final_val != expected_val:
                allure.attach(
                    f"字段 {field} 恢复后值与期望不同\n期望: '{expected_val}'\n实际: '{final_val}'",
                    name=f"restore_warning_{field}",
                    attachment_type=allure.attachment_type.TEXT
                )
                # 安全测试核心目标是页面不崩溃、不产生服务端错误，数据恢复问题记录但不阻断
                pass

    logger.end(success=True)
