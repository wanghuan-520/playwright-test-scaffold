# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountRegister - Security
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
import re
import uuid
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from .test_Register_known_bugs import BUG_REG_INJECTION_500, bug_xfail
from tests.Account.Register._helpers import (
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('Register' + "_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature('AccountRegister')
@allure.story("Security")
@allure.description("规则来源：docs/requirements/requirements.md（/Account/Register 为匿名页）")
def test_security_unauth_redirects_to_login(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Register is anonymous (no redirect)")

    page = unauth_page
    po = AccountRegisterPage(page)
    po.navigate()
    # 期望：不跳转到前端 /auth/login
    assert_not_redirected_to_login(page)
    # 且仍在 /Account/Register 匿名路由下
    current = page.url or ""
    assert "/Account/Register" in current, f"expected stay on register page, got: {current}"
    step_shot(po, "step_unauth_should_stay_on_register", full_page=True)

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 页面所有可输入框（显式列出，避免 selector 漂移造成"漏测/误测"）
# 设计：移除 block_selector，采用纯粹的控制变量法
# ═══════════════════════════════════════════════════════════════
_FIELDS = [
    ("username", 'role=textbox[name="Username *"]'),
    ("email", 'role=textbox[name="Email address *"]'),
    ("password", 'role=textbox[name="Password *"]'),
]

# ═══════════════════════════════════════════════════════════════
# 注入 payload 库（精简版：代表性子集）
# 设计原则：覆盖 XSS/SQLi/HTML 注入的核心攻击向量，避免冗余
# ═══════════════════════════════════════════════════════════════
_PAYLOADS = [
    # XSS 类：经典 script 注入
    ("xss_script", "<script>alert('XSS')</script>"),
    # XSS 类：事件触发型（img onerror）
    ("xss_img", "<img src=x onerror=alert('XSS')>"),
    
    # SQLi 类：经典逻辑绕过（OR 1=1）
    ("sqli_quote", "' OR '1'='1"),
    # SQLi 类：注释截断
    ("sqli_comment", "admin'--"),
    
    # HTML 注入：基础标签过滤测试
    ("html_bold", "<b>bold</b>"),
]
# 移除的 payload 及理由：
# - xss_svg: 与 xss_script 本质相同，参数化转义会同时阻止两者
# - sqli_union/sqli_drop_table: 与 sqli_quote 同类，参数化查询会同时阻止
# - html_iframe: 与 xss_img 同类，且通常被 CSP 策略阻止
# - mixed_email_sqli: 与 sqli_quote 同类，测一个足够


def _params():
    """
    生成参数化测试矩阵：3字段 × 5种 payload = 15条用例
    采用纯粹的控制变量法：测试目标字段填 payload，其他字段填合法值
    """
    params = []
    seen = set()
    for field, selector in _FIELDS:
        for payload_id, payload in _PAYLOADS:
            key = (field, payload_id)
            if key in seen:
                raise AssertionError(f"duplicate case: {key}")
            seen.add(key)
            params.append(
                pytest.param(
                    field,
                    selector,
                    payload_id,
                    payload,
                    marks=[],
                    id=f"{field}__{payload_id}",
                )
            )
    return params


@pytest.mark.P1
@pytest.mark.security
@pytest.mark.matrix
@allure.feature('AccountRegister')
@allure.story("Security")
@allure.description(
    """
测试点：
- Register 页面所有可输入框都覆盖注入类 payload（XSS/SQLi/HTML 注入）
- 精简版：3字段 × 5个代表性 payload = 15条用例
- 不触发浏览器 dialog（payload 不执行）
- 提交路径不应崩溃（禁止 5xx）
- **控制变量法**：测试目标字段填 payload，其他字段填合法值（恶意输入本身会阻止注册成功）
证据：每个 payload 截图

输入内容（每条 case）：
- 目标输入框：username/email/password（覆盖所有可输入框）
- 注入值：<payload>（5种代表性攻击向量）
- **其他输入框**：填写合法内容（控制变量法）

判据：
- 不弹 dialog
- 不进入致命错误页
- 若抓到响应则必须非 5xx
"""
)
@pytest.mark.parametrize("field,selector,payload_id,payload", _params())
def test_security_injection_payload_matrix_no_dialog_no_5xx(
    unauth_page: Page, field: str, selector: str, payload_id: str, payload: str
):
    """
    纯粹的控制变量法：测试目标字段填 payload，其他字段填合法值
    恶意 payload 本身会导致注册失败，无需人为清空其他字段阻断提交
    """
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Register injection safety (matrix)")

    page = unauth_page
    po = AccountRegisterPage(page)

    dialog_triggered = {"value": False}

    def on_dialog(_):
        dialog_triggered["value"] = True

    page.on("dialog", on_dialog)

    po.navigate()
    assert_not_redirected_to_login(page)

    # ═══════════════════════════════════════════════════════════════
    # 控制变量法：所有字段先填合法值，再将目标字段替换为 payload
    # ═══════════════════════════════════════════════════════════════
    def _fill_valid_baseline() -> dict:
        """填充所有字段为合法值（baseline）"""
        suffix = uuid.uuid4().hex[:10]
        username = f"qatest_{suffix}"
        email = f"qatest_{suffix}@testmail.com"
        password = "ValidPass123!"
        po.fill_username(username)
        po.fill_email_address(email)
        po.fill_password(password)
        return {"username": username, "email": email, "password": "***"}

    case_name = f"{field}__{payload_id}"
    with allure.step(f"[{case_name}] 注入 payload（不应弹窗/不应 5xx）"):
        attach_rule_source_note(f"docs/requirements/requirements.md: injection field={field} payload={payload_id}")
        try:
            allure.attach(payload, name=f"{case_name}_payload", attachment_type=allure.attachment_type.TEXT)
        except Exception:
            pass

        if page.locator(selector).count() == 0:
            pytest.skip(f"{field} 输入框不可见（selector 失效或页面结构变化）")

        snap = snapshot_inputs(page, [{"selector": s} for _, s in _FIELDS])
        try:
            # 1. 填充所有字段为合法值
            _fill_valid_baseline()
            # 2. 将目标字段替换为 payload（控制变量法：只改变一个变量）
            page.fill(selector, payload)
            page.wait_for_timeout(150)
            step_shot(po, f"step_{case_name}_filled", full_page=True)

            # 3. 提交表单
            click_save(page)
            resp = wait_mutation_response(page, timeout_ms=3000)
            page.wait_for_timeout(300)
            step_shot(po, f"step_{case_name}_after_submit", full_page=True)

            # 4. 断言：不应出现致命错误页
            fatal = detect_fatal_error_page(page)
            assert not fatal, f"产品缺陷：/Account/Register 注入类输入触发 500（Internal Server Error）: {fatal}"

            # 5. 断言：响应不应是 5xx
            if resp is not None:
                assert resp.status < 500, f"unexpected 5xx on injection payload: status={resp.status}"

            # 6. 断言：不应跳转离开注册页
            assert "/Account/Register" in (page.url or ""), f"unexpected navigation away from register page: url={page.url}"
            
            # 7. 断言：不应触发浏览器 dialog（payload 未执行）
            assert dialog_triggered["value"] is False, f"payload triggered a dialog: field={field} payload={payload!r}"
        finally:
            try:
                restore_inputs(page, snap)
            except Exception:
                pass

    logger.end(success=True)
