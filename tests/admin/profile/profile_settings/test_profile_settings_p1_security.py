# ═══════════════════════════════════════════════════════════════
# Profile Settings (Personal Settings) - Security
# ═══════════════════════════════════════════════════════════════
"""
Security：字段维度最小载荷集（XSS/SQLi），核心断言：
- 不弹 dialog（XSS 不执行）
- 不异常跳转（不被踢出登录，除非本身未登录场景）
- 提交后不应出现 5xx 级“崩溃态”（这里以“页面仍可用 + 未崩溃”为主）
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


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Profile Settings")
@allure.story("Security - Injection")
@allure.description(
    """
测试点（XSS）：
- 5 字段覆盖（userName/email/name/surname/phoneNumber）
- userName/email：必须前端拦截（不发 profileUpdate）+ 有可见错误证据（validationMessage/aria-invalid/内联提示）
- name/surname/phoneNumber：允许提交但必须满足
  - 不弹 dialog（payload 不执行）
  - 页面不崩溃、不跳登录
  - 最终不污染数据（如污染则走 API 强制回滚并证明回滚成功）
- 证据：每字段提交前后关键截图（filled / result）
"""
)
def test_security_profile_settings_xss_payload_does_not_execute(profile_settings):
    """
    Security: XSS payload 不执行（无 dialog）+ 5 字段覆盖。

    升级策略：
    - userName/email：重点断言“前端拦截不发请求 + 有可见错误/validationMessage”
    - name/surname/phone：重点断言“不执行脚本/不崩溃/最终不污染（必要时强制回滚）”
    """
    attach_rule_source_note()
    logger = TestLogger("test_security_profile_settings_xss_payload_does_not_execute")
    logger.start()

    auth_page, page_obj, baseline = profile_settings

    dialog_seen = {"type": None, "message": None}

    def on_dialog(d):
        dialog_seen["type"] = d.type
        dialog_seen["message"] = d.message
        try:
            d.dismiss()
        except Exception:
            pass

    auth_page.on("dialog", on_dialog)

    xss_payload = '<img src=x onerror=alert(1) />'

    def _assert_frontend_blocked(field: str, selector: str, validation_message_required: bool) -> None:
        """断言：不发 profileUpdate + 有错误证据（文案/aria-invalid/validationMessage）。"""
        blocked = page_obj.wait_for_profile_update_response(timeout_ms=1500)
        assert blocked is None, f"[{field}] frontend should block (no profileUpdate request expected)"

        has_visible = False
        # 1) 收集输入框错误证据（不绑定具体 UI 框架）
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

        # 2) 常见 required 文案（兜底）
        if field == "email":
            try:
                if auth_page.get_by_text("Email is required").is_visible(timeout=300):
                    has_visible = True
            except Exception:
                pass

        # 3) 强制要求“可见错误证据”
        if validation_message_required and not has_visible:
            assert False, f"[{field}] expected visible error evidence (validationMessage/aria-describedby/invalid styling)"

        assert has_visible, f"[{field}] expected visible error evidence (text/aria-invalid/validationMessage)"

    # 5 字段覆盖：每个字段独立提交与验证，避免互相污染
    cases = [
        # userName/email：应被前端拦截（不发请求）且有错误证据
        ("userName", page_obj.USERNAME_INPUT, {"userName": f"bad<{xss_payload}>"}, True, False),
        # email：用“携带 XSS 形态的非法字符串”验证安全边界（注意：应在前端被拦截，不会到后端）
        ("email", page_obj.EMAIL_INPUT, {"email": f"bad{xss_payload}"}, True, True),
        # 可选字段：允许提交，但必须不执行脚本/不崩溃，且最终不污染
        ("name", page_obj.NAME_INPUT, {"name": xss_payload}, False, False),
        ("surname", page_obj.SURNAME_INPUT, {"surname": xss_payload}, False, False),
        ("phoneNumber", page_obj.PHONE_INPUT, {"phoneNumber": xss_payload}, False, False),
    ]

    for field, selector, patch, should_block, need_validation_message in cases:
        with allure.step(f"[{field}] 填写并提交"):
            settle_toasts(page_obj)
            page_obj.fill_form(patch)
            # 尽量触发表单校验状态（部分框架在 blur 或 submit 后才渲染错误）
            if field in ("userName", "email"):
                try:
                    auth_page.locator(selector).blur()
                except Exception:
                    pass
            step_shot(page_obj, f"step_{field}_filled")
            resp = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
            # 后端响应状态默认不展示（需要时 ALLURE_SHOW_BACKEND=1）
            if resp is not None and (not resp.ok):
                attach_backend_text(f"profile_update_status_{field}", str(getattr(resp, "status", None)))
            auth_page.wait_for_timeout(500)
            # email：尽量触发 HTML5 validity 计算（toast 不一定存在）
            if field == "email":
                try:
                    auth_page.eval_on_selector(page_obj.EMAIL_INPUT, "el => el.reportValidity && el.reportValidity()")
                except Exception:
                    pass
            step_shot(page_obj, f"step_{field}_result")

        # 不在 Allure 展示“断言步骤”，断言仍执行；失败时通过截图/最小附件给证据
        assert_no_dialog(auth_page, dialog_seen)
        assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login: url={auth_page.url}"
        assert page_obj.is_loaded(), f"[{field}] page should remain usable"

        if should_block:
            _assert_frontend_blocked(field, selector, validation_message_required=need_validation_message)
            # 回填 UI（不保存）：保证后续字段不受影响
            page_obj.fill_form({field: baseline.get(field, "")})
            assert_no_dialog(auth_page, dialog_seen)
        else:
            # 可选字段：不强绑“必须保存/必须阻止”，但最终不得污染
            auth_page.reload()
            auth_page.wait_for_timeout(800)
            assert page_obj.is_loaded(), f"[{field}] reload after submit should be ok"
            current = page_obj.read_form_values()
            if (current.get(field) or "") != (baseline.get(field) or ""):
                r = abp_profile_put(auth_page, baseline, {})
                attach_backend_text(f"force_restore_via_api_{field}", str(r))
                assert r.get("ok"), f"[{field}] restore blocked: status={r.get('status')}"
                auth_page.reload()
                auth_page.wait_for_timeout(800)
                current2 = page_obj.read_form_values()
                assert (current2.get(field) or "") == (baseline.get(field) or ""), f"[{field}] should not be polluted after restore"

    # 收尾断言/回滚过程不展示在 Allure steps 中
    assert_no_dialog(auth_page, dialog_seen)

    auth_page.reload()
    auth_page.wait_for_timeout(800)
    current = page_obj.read_form_values()
    diff = {k: (current.get(k), baseline.get(k)) for k in baseline.keys() if (current.get(k) or "") != (baseline.get(k) or "")}
    attach_backend_text("post_security_xss_final_diff", str(diff))
    if diff:
        r = abp_profile_put(auth_page, baseline, {})
        attach_backend_text("final_force_restore_via_api", str(r))
        assert r.get("ok"), f"final restore blocked: status={r.get('status')}"
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        current2 = page_obj.read_form_values()
        diff2 = {k: (current2.get(k), baseline.get(k)) for k in baseline.keys() if (current2.get(k) or "") != (baseline.get(k) or "")}
        attach_backend_text("post_final_force_restore_diff", str(diff2))
        assert not diff2, f"final restore succeeded but UI still not baseline: {diff2}"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Profile Settings")
@allure.story("Security - Injection")
@allure.description(
    """
测试点（SQLi 风格输入）：
- 5 字段覆盖（userName/email/name/surname/phoneNumber）
- userName/email：必须前端拦截（不发 profileUpdate）+ 有可见错误证据
- name/surname/phoneNumber：允许提交但必须满足
  - 页面不崩溃、不跳登录
  - 最终不污染数据（优先 reload 比对；如污染则 API 强制回滚并证明回滚成功）
- 证据：每字段提交前后关键截图（filled / result）
"""
)
def test_security_profile_settings_sqli_style_input_does_not_crash(profile_settings):
    """
    Security: SQLi 风格输入不导致异常行为 + 5 字段覆盖。

    - userName/email：重点断言前端拦截（不发请求）+ 错误证据
    - name/surname/phone：重点断言不崩溃 + 最终不污染（必要时 API 强制回滚）
    """
    attach_rule_source_note()
    logger = TestLogger("test_security_profile_settings_sqli_style_input_does_not_crash")
    logger.start()

    auth_page, page_obj, baseline = profile_settings

    sqli_payload = "' OR 1=1 --"

    def _assert_frontend_blocked(field: str, selector: str, validation_message_required: bool) -> None:
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
            assert False, f"[{field}] expected visible error evidence (validationMessage/aria-describedby/invalid styling)"
        assert has_visible, f"[{field}] expected visible error evidence (text/aria-invalid/validationMessage)"

    cases = [
        ("userName", page_obj.USERNAME_INPUT, {"userName": sqli_payload}, True, False),
        # email：用“携带 SQLi 形态的非法字符串”验证安全边界（注意：应在前端被拦截，不会到后端）
        ("email", page_obj.EMAIL_INPUT, {"email": f"bad{sqli_payload}"}, True, True),
        ("name", page_obj.NAME_INPUT, {"name": sqli_payload}, False, False),
        ("surname", page_obj.SURNAME_INPUT, {"surname": sqli_payload}, False, False),
        ("phoneNumber", page_obj.PHONE_INPUT, {"phoneNumber": sqli_payload}, False, False),
    ]

    for field, selector, patch, should_block, need_validation_message in cases:
        with allure.step(f"[{field}] 填写并提交"):
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

        # 不在 Allure 展示“断言步骤”，断言仍执行；失败时通过截图/最小附件给证据
        assert not page_obj.is_login_page(), f"[{field}] unexpected redirect to login: url={auth_page.url}"
        assert page_obj.is_loaded(), f"[{field}] page should remain usable"

        if should_block:
            _assert_frontend_blocked(field, selector, validation_message_required=need_validation_message)
            page_obj.fill_form({field: baseline.get(field, "")})
        else:
            auth_page.reload()
            auth_page.wait_for_timeout(800)
            # 并发/弱网下偶发路由漂移：reload 可能把 SPA 带回 home，但登录态仍在。
            # 对安全用例而言，我们关注“不崩溃/不跳登录/可恢复”，所以允许一次自愈导航。
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
                assert r.get("ok"), f"[{field}] restore blocked: status={r.get('status')}"
                auth_page.reload()
                auth_page.wait_for_timeout(800)
                current2 = page_obj.read_form_values()
                assert (current2.get(field) or "") == (baseline.get(field) or ""), f"[{field}] should not be polluted after restore"

    # 最终断言/回滚过程不展示在 Allure steps 中
    assert not page_obj.is_login_page(), f"异常跳转登录页: url={auth_page.url}"
    assert page_obj.is_loaded(), "提交后页面应仍可用"

    auth_page.reload()
    auth_page.wait_for_timeout(800)
    assert page_obj.is_loaded(), "reload 后页面应仍可用"
    current = page_obj.read_form_values()
    touched = ["name", "surname", "phoneNumber"]
    changed = {k: (current.get(k), baseline.get(k)) for k in touched if (current.get(k) or "") != (baseline.get(k) or "")}
    attach_backend_text("post_reload_diff(touched_fields)", str(changed))

    if changed:
        r = abp_profile_put(auth_page, baseline, {})
        attach_backend_text("force_restore_via_api_result", str(r))
        assert r.get("ok"), f"restore blocked by backend/security policy: status={r.get('status')}"
        auth_page.reload()
        auth_page.wait_for_timeout(800)
        current2 = page_obj.read_form_values()
        changed2 = {k: (current2.get(k), baseline.get(k)) for k in touched if (current2.get(k) or "") != (baseline.get(k) or "")}
        attach_backend_text("post_force_restore_diff", str(changed2))
        assert not changed2, f"forced restore succeeded but UI still not baseline: {changed2}"

    logger.end(success=True)

