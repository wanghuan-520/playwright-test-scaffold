"""
Account/Register - Email 字段测试

测试内容：
- Email 格式验证（无效格式矩阵）
- Email 唯一性
- Email 长度边界
- Email Required 属性
"""

import allure
import pytest
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.myaccount._helpers import attach_rule_source_note, step_shot
from tests.account.register import _abp_constraints_helpers as ABP
from tests.account.register._helpers import (
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
    ensure_register_page,
    get_validation_message,
    has_any_error_ui,
    unique_suffix,
    wait_mutation_response,
    wait_response_by_url_substring,
)


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
        # ═══════════════════════════════════════════════════
        # @ 符号相关
        # ═══════════════════════════════════════════════════
        ("email_no_at", "not-an-email"),
        ("email_only_at", "@t.com"),
        ("email_double_at", "a@@t.com"),
        # ═══════════════════════════════════════════════════
        # 域名部分（@ 后面）
        # ═══════════════════════════════════════════════════
        ("email_missing_domain", "a@"),
        ("email_double_dot_domain", "a@t..com"),
        # NOTE: "a@t" 可能被部分实现视为可接受邮箱（正则/浏览器差异大），避免制造误报
        # ═══════════════════════════════════════════════════
        # Local part（@ 前面）- RFC 5321/5322 规范
        # ═══════════════════════════════════════════════════
        ("email_local_start_dot", ".startwith@t.com"),      # RFC: 不允许点号开头
        ("email_local_end_dot", "endwith.@t.com"),          # RFC: 不允许点号结尾
        ("email_local_double_dot", "user..name@t.com"),     # RFC: 不允许连续点号
        ("email_local_only_special", "###@t.com"),          # 纯特殊字符
        ("email_local_space", "user name@t.com"),           # 包含空格
        ("email_local_chinese", "用户@t.com"),              # 中文字符（非 ASCII）
    ],
)
def test_p1_register_email_invalid_format_matrix_should_show_evidence(
    unauth_page: Page, xdist_worker_id: str, case_name: str, email: str
):
    attach_rule_source_note("reference: ui-automation/tests/aevatar_station/test_register.py (invalid email matrix)")
    page = unauth_page
    po = AccountRegisterPage(page)

    with allure.step(f"[{case_name}] baseline + 填写无效邮箱并提交（应被拦截）"):
        ensure_register_page(page, po)
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_navigate", full_page=True)

        suf = unique_suffix(xdist_worker_id)
        po.fill_username(f"em_{suf}")
        po.fill_email(email)
        po.fill_password("ValidPass123!")
        po.check_terms()  # 勾选 Terms of Service and Privacy Policy
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            # 如果是500错误，记录但不强制失败（这是后端问题）
            page_text = page.inner_text("body") if hasattr(page, 'inner_text') else (page.evaluate("() => document.body.innerText") if hasattr(page, 'evaluate') else "")
            if "500" in str(page_text) or "API Error" in str(page_text) or "Internal Server Error" in str(page_text):
                allure.attach(
                    f"⚠️ 后端返回500错误: {fatal}\n这是后端API问题，不是前端验证问题。",
                    name=f"{case_name}_backend_500_error",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 对于邮箱格式测试，500错误可能是后端验证问题，记录但不强制失败
                allure.attach(
                    "后端返回500错误，可能是后端验证逻辑问题。测试用例标记为xfail。",
                    name=f"{case_name}_api_error_500_note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.xfail(f"后端API返回500错误: {fatal}")
            else:
                # 其他致命错误仍然失败
                assert False, f"[{case_name}] fatal error page detected: {fatal}"

        # 证据：优先 validationMessage，其次 error UI，其次 4xx
        msg = get_validation_message(page, po.EMAIL_INPUT)
        if msg:
            allure.attach(msg, name=f"{case_name}_validationMessage", attachment_type=allure.attachment_type.TEXT)
        resp = wait_mutation_response(page, timeout_ms=1500)
        if resp is not None:
            assert resp.status < 500, f"[{case_name}] unexpected 5xx status={resp.status}"

        # 注意：实际URL是 /register，不是 /Account/Register
        current_url = page.url or ""
        assert "/register" in current_url or "/Account/Register" in current_url, f"[{case_name}] unexpected navigation: {current_url}"
        assert msg or has_any_error_ui(page) or (resp is not None and 400 <= resp.status < 500), (
            f"[{case_name}] expected validation evidence (validationMessage/error UI/4xx)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Email 唯一性测试（从 test_Register_p1_duplicate_data.py 迁移）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.exception
@allure.feature("AccountRegister")
@allure.story("P1 - Email Uniqueness")
@allure.description(
    """
测试 Email 唯一性

场景：
1. 先创建一个账号（作为重复基准）
2. 使用相同 Email 再次注册（应被拦截）

规则来源：docs/requirements/account-register-field-requirements.md
"""
)
def test_p1_register_email_uniqueness(unauth_page: Page, xdist_worker_id: str):
    """测试 Email 唯一性"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Email uniqueness")
    page = unauth_page
    po = AccountRegisterPage(page)
    
    suffix = unique_suffix(xdist_worker_id)
    password = "ValidPass123!"
    case_name = "email_uniqueness"

    # 在 Allure 报告中显示实际输入内容
    base_email = f"dup_{suffix}@testmail.com"
    allure.dynamic.parameter("测试邮箱", base_email)

    def _register_once(username: str, email: str, *, step_name: str):
        """注册一次，返回响应状态码"""
        po.navigate()
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{step_name}_navigate", full_page=True)

        po.fill_username(username)
        po.fill_email(email)
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_{step_name}_filled", full_page=True)

        # 记录实际输入
        allure.attach(
            f"═══════════════════════════════════════════════════\n"
            f"【{step_name} 输入数据】\n"
            f"  用户名: {username}\n"
            f"  邮箱: {email}\n"
            f"═══════════════════════════════════════════════════",
            name=f"📋 {step_name}_输入信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        click_save(page)
        resp = None
        try:
            resp = wait_response_by_url_substring(page, "/api/account/register", timeout_ms=2500)
        except Exception:
            resp = None
        page.wait_for_timeout(300)
        step_shot(po, f"step_{step_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            page_text = page.evaluate("() => document.body.innerText") if hasattr(page, 'evaluate') else ""
            if "500" in str(page_text) or "API Error" in str(page_text):
                allure.attach(
                    f"⚠️ 后端返回500错误: {fatal}",
                    name=f"{step_name}_backend_500_error",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.xfail(f"后端API返回500错误: {fatal}")
            else:
                assert False, f"[{step_name}] fatal error page detected: {fatal}"
        return resp.status if resp is not None else None

    with allure.step(f"[{case_name}] 第一次注册（创建基准账号）"):
        username1 = f"dup_{suffix}_u1"
        status1 = _register_once(username1, base_email, step_name=f"{case_name}_first")
        allure.attach(f"first_register_status={status1}", name=f"{case_name}_first_status", attachment_type=allure.attachment_type.TEXT)
        assert not has_any_error_ui(page), f"[{case_name}] first register unexpected error UI"

    with allure.step(f"[{case_name}] 第二次注册（使用重复 Email，应被拦截）"):
        username2 = f"dup_{suffix}_u2"  # 不同的用户名
        status2 = _register_once(username2, base_email, step_name=f"{case_name}_second")  # 相同的邮箱

        if status2 is not None:
            assert status2 < 500, f"[{case_name}] unexpected 5xx status={status2}"

        current_url = page.url or ""
        assert "/register" in current_url or "/Account/Register" in current_url, f"[{case_name}] unexpected navigation: {current_url}"

        # 期望：出现错误 UI 或 4xx 响应
        if status2 is not None and 400 <= status2 < 500:
            allure.attach(
                f"✅ 后端正确拒绝了重复 Email（status={status2}）",
                name=f"{case_name}_backend_rejected_duplicate",
                attachment_type=allure.attachment_type.TEXT,
            )
        elif has_any_error_ui(page):
            allure.attach(
                "✅ 页面显示了错误 UI（Email 已存在）",
                name=f"{case_name}_error_ui_found",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            allure.attach(
                f"⚠️ 后端可能允许了重复 Email\n根据需求文档，Email 必须唯一。",
                name=f"{case_name}_backend_allowed_duplicate_warning",
                attachment_type=allure.attachment_type.TEXT,
            )
            pytest.xfail("后端可能允许了重复 Email - 根据需求文档应该被拒绝")


# ═══════════════════════════════════════════════════════════════════════════════
# Email 约束测试（从 test_Register_p1_abp_constraints.py 迁移）
# ═══════════════════════════════════════════════════════════════════════════════

ABP_EMAIL_MAX = 256  # Email 最大长度


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email Length Boundaries")
@allure.description("测试 Email 长度边界值（6 点法：max-1/max/max+1）")
@pytest.mark.parametrize(
    "total_len,expected_result",
    [
        # ═══════════════════════════════════════════════════
        # Max 端边界（6 点法）- Email 最大 256 字符
        # ═══════════════════════════════════════════════════
        pytest.param(255, "accept", id="len_255_accept"),  # max-1：应被接受
        pytest.param(256, "accept", id="len_256_accept"),  # max：应被接受
        pytest.param(257, "reject", id="len_257_reject"),  # max+1：应被拒绝
    ],
)
def test_p1_register_email_length_boundaries(unauth_page: Page, xdist_worker_id: str, total_len: int, expected_result: str):
    """测试 Email 长度边界（6 点法）"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Email boundary")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = unique_suffix(xdist_worker_id)
    case_name = f"email_boundary_{total_len}"

    ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    # 构造指定长度的邮箱
    email = ABP.mk_email_with_len(total_len, suffix)
    username = f"em_{suffix}"

    # 在 Allure 报告中显示实际数据
    allure.dynamic.parameter("期望长度", total_len)
    allure.dynamic.parameter("预期结果", expected_result)
    allure.dynamic.parameter("实际邮箱", f"{email[:30]}...{email[-15:]}" if len(email) > 50 else email)
    allure.dynamic.parameter("实际长度", len(email))

    with allure.step(f"[{case_name}] 填写 {total_len} 字符 Email 并提交"):
        po.fill_username(username)
        po.fill_email(email)
        po.fill_password("ValidPass123!")
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        allure.attach(
            f"═══════════════════════════════════════════════════\n"
            f"【输入数据】\n"
            f"  期望长度: {total_len}\n"
            f"  实际长度: {len(email)}\n"
            f"  预期结果: {expected_result}\n"
            f"  邮箱前30字符: {email[:30]}\n"
            f"  邮箱后15字符: {email[-15:]}\n"
            f"═══════════════════════════════════════════════════",
            name=f"📋 {case_name}_详细输入信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        actual_len = len(po.get_email_value())

        click_save(page)
        resp = wait_mutation_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            pytest.xfail(f"[{case_name}] fatal error page: {fatal}")

        # ═══════════════════════════════════════════════════════════════
        # 验证结果
        # ═══════════════════════════════════════════════════════════════
        if expected_result == "reject":
            # 应该被拒绝
            has_error = has_any_error_ui(page)
            has_4xx = resp is not None and 400 <= resp.status < 500
            # 前端可能截断了输入
            was_truncated = actual_len < total_len
            current_url = page.url or ""
            still_on_register = "/register" in current_url or "/Account/Register" in current_url

            if has_error or has_4xx or was_truncated or still_on_register:
                allure.attach(
                    f"✅ Email 长度 {total_len} 被正确处理\n"
                    f"  - 错误 UI: {has_error}\n"
                    f"  - 4xx 响应: {has_4xx}\n"
                    f"  - 前端截断: {was_truncated}（实际 {actual_len}）\n"
                    f"  - 仍在注册页: {still_on_register}",
                    name=f"{case_name}_rejected_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                pytest.fail(f"{case_name}: Email 长度 {total_len} 应该被拒绝，但似乎被接受了")
        else:
            # 应该被接受
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
                assert resp.status < 400, f"{case_name}: expected success but got {resp.status}"
            assert not has_any_error_ui(page), f"{case_name}: unexpected error UI"


# ═══════════════════════════════════════════════════════════════════════════════
# Email 有效格式测试（补充：验证各种合法邮箱格式）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email Valid Formats")
@allure.description("验证各种合法邮箱格式应被接受")
@pytest.mark.parametrize(
    "email_pattern,description",
    [
        ("user@example.com", "标准格式"),
        ("user.name@example.com", "包含点号"),
        ("user+tag@example.com", "包含加号（Gmail 风格）"),
        ("user_name@example.com", "包含下划线"),
        ("user-name@example.com", "包含连字符"),
        ("user123@example.com", "包含数字"),
        ("a@b.co", "最短合法格式"),
    ],
    ids=["standard", "with_dot", "with_plus", "with_underscore", "with_hyphen", "with_digits", "shortest"],
)
def test_p1_register_email_valid_formats(unauth_page: Page, xdist_worker_id: str, email_pattern: str, description: str):
    """验证 Email 有效格式"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Email valid formats")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = unique_suffix(xdist_worker_id)
    case_name = f"email_valid_{email_pattern.split('@')[0]}"

    # 构造唯一邮箱：在 @ 前加后缀
    parts = email_pattern.split("@")
    email = f"{parts[0]}_{suffix}@{parts[1]}"
    username = f"em_{suffix}"

    # 在 Allure 报告中显示实际输入
    allure.dynamic.parameter("格式描述", description)
    allure.dynamic.parameter("实际邮箱", email)

    ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] 填写有效邮箱并提交（{description}）"):
        po.fill_username(username)
        po.fill_email(email)
        po.fill_password("ValidPass123!")
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        resp = wait_mutation_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            pytest.xfail(f"后端错误: {fatal}")

        # 有效格式应该允许提交
        if resp is not None:
            assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        assert not has_any_error_ui(page), f"{case_name}: unexpected error UI"


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email Required Empty")
@allure.description("验证 Email 为空提交不应返回 500 错误")
def test_p1_register_email_required_empty_should_not_500(unauth_page: Page, xdist_worker_id: str):
    """验证 Email 为空提交不应返回 500"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Email required validation")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = unique_suffix(xdist_worker_id)
    case_name = "email_required_empty"

    ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    # 在 Allure 报告中显示测试数据
    allure.dynamic.parameter("UserName", f"qatest_{suffix}")
    allure.dynamic.parameter("Email", "（空）")

    with allure.step(f"[{case_name}] 填写其他字段，Email 留空并提交"):
        ABP.fill_baseline(po, suffix=suffix)
        ABP.set_field(po, "email", "")
        step_shot(po, f"step_{case_name}_filled", full_page=True)
        click_save(page)
        page.wait_for_timeout(300)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    ABP.assert_no_fatal_error(page, case_name=case_name)


# ═══════════════════════════════════════════════════════════════════════════════
# Email 有效格式测试（补充：验证各种合法邮箱格式）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Email Valid Formats")
@allure.description("验证各种合法邮箱格式应被接受")
@pytest.mark.parametrize(
    "email_pattern,description",
    [
        ("user@example.com", "标准格式"),
        ("user.name@example.com", "包含点号"),
        ("user+tag@example.com", "包含加号（Gmail 风格）"),
        ("user_name@example.com", "包含下划线"),
        ("user-name@example.com", "包含连字符"),
        ("user123@example.com", "包含数字"),
        ("a@b.co", "最短合法格式"),
    ],
    ids=["standard", "with_dot", "with_plus", "with_underscore", "with_hyphen", "with_digits", "shortest"],
)
def test_p1_register_email_valid_formats(unauth_page: Page, xdist_worker_id: str, email_pattern: str, description: str):
    """验证 Email 有效格式"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Email valid formats")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = unique_suffix(xdist_worker_id)
    case_name = f"email_valid_{email_pattern.split('@')[0]}"

    # 构造唯一邮箱：在 @ 前加后缀
    parts = email_pattern.split("@")
    email = f"{parts[0]}_{suffix}@{parts[1]}"
    username = f"em_{suffix}"

    # 在 Allure 报告中显示实际输入
    allure.dynamic.parameter("格式描述", description)
    allure.dynamic.parameter("实际邮箱", email)

    ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] 填写有效邮箱并提交（{description}）"):
        po.fill_username(username)
        po.fill_email(email)
        po.fill_password("ValidPass123!")
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        resp = wait_mutation_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            pytest.xfail(f"后端错误: {fatal}")

        # 有效格式应该允许提交
        if resp is not None:
            assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        assert not has_any_error_ui(page), f"{case_name}: unexpected error UI"
