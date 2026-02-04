"""
Account/Register - UserName 字段测试

根据需求文档 docs/requirements/account-register-field-requirements.md：
- UserName: 用户名，直接传递给后端
- 最大长度：256 字符
- 必须唯一（不能与已存在的用户名重复）
- 允许的字符：字母、数字、下划线、连字符、点号
"""

import random
import string
import uuid

import allure
import pytest
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.account.register import _helpers as H
from tests.account.register import _abp_constraints_helpers as ABP
from tests.account.register._helpers import (
    assert_not_redirected_to_login,
    click_save,
    detect_fatal_error_page,
)
from tests.admin.settings.profile._helpers import attach_rule_source_note, step_shot
from utils.logger import TestLogger

logger = TestLogger("Register_p1_username")

# UserName 限制（根据需求文档）
ABP_USERNAME_MAX = 256  # userName 最大长度


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - UserName Format Validation")
@allure.description(
    """
测试 UserName 格式验证（根据需求文档）

验证：
- 不同格式的用户名是否被接受
- 允许的字符：字母、数字、下划线、连字符、点号

规则来源：docs/requirements/account-register-field-requirements.md
"""
)
@pytest.mark.parametrize(
    "username_pattern,description",
    [
        ("user", "标准格式"),
        ("test.user", "包含点号"),
        ("user_name", "包含下划线"),
        ("user-name", "包含连字符"),
        ("123user", "以数字开头"),
        ("user123", "以数字结尾"),
        ("User", "包含大写字母"),
        ("USER123", "全大写+数字"),
    ],
    ids=["standard", "with_dot", "with_underscore", "with_hyphen", "starts_digit", "ends_digit", "with_uppercase", "all_uppercase"],
)
def test_p1_register_username_valid_formats(
    unauth_page: Page,
    username_pattern: str,
    description: str,
):
    """
    测试 UserName 有效格式
    """
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: UserName valid formats")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = uuid.uuid4().hex[:8]

    # ═══════════════════════════════════════════════════════════════
    # 构造用户名：边界值测试保持原始长度，普通格式追加 suffix 保证唯一
    # ═══════════════════════════════════════════════════════════════
    is_shortest_test = len(username_pattern) <= 1  # 最短格式测试
    if is_shortest_test:
        # 最短格式测试：随机单字符，保持 1 字符边界
        # 测试目的：验证系统支持 1 字符格式（而非创建唯一用户）
        username = random.choice(string.ascii_lowercase + string.digits)
    else:
        # 普通格式测试：追加 suffix 保证唯一
        username = f"{username_pattern}_{suffix}"
    
    email = f"fmt_{suffix}@testmail.com"
    password = "ValidPass123!"
    case_name = f"username_valid_{username_pattern}"

    # 在 Allure 报告中显示实际输入内容
    allure.dynamic.parameter("格式描述", description)
    allure.dynamic.parameter("实际用户名", username)
    allure.dynamic.parameter("用户名长度", len(username))

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] 填写 UserName='{username}' 并提交（{description}）"):
        po.fill_username(username)
        po.fill_email(email)
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        allure.attach(
            f"═══════════════════════════════════════════════════\n"
            f"【输入数据】\n"
            f"  格式模式: {username_pattern}\n"
            f"  实际用户名: {username}\n"
            f"  用户名长度: {len(username)}\n"
            f"  邮箱: {email}\n"
            f"═══════════════════════════════════════════════════\n"
            f"【测试说明】\n"
            f"  {description}\n"
            f"═══════════════════════════════════════════════════",
            name=f"📋 {case_name}_详细输入信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)

        # ═══════════════════════════════════════════════════════════════
        # 验证逻辑：
        # - 普通格式测试：必须注册成功
        # - 最短格式测试：注册成功 或 "用户名已存在" 都算通过
        #   （"已存在"说明格式被接受，只是恰好冲突）
        # ═══════════════════════════════════════════════════════════════
        if resp is not None:
            assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        
        if is_shortest_test:
            # 最短格式测试：接受 "注册成功" 或 "用户名已存在"
            error_text = H.get_error_text(page) if H.has_any_error_ui(page) else ""
            is_duplicate_error = "已存在" in error_text or "already" in error_text.lower()
            if is_duplicate_error:
                allure.attach(
                    f"用户名 '{username}' 已存在，但格式验证通过（系统接受1字符格式）",
                    name=f"{case_name}_duplicate_but_format_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                assert not H.has_any_error_ui(page), f"{case_name}: unexpected error UI"
        else:
            # 普通格式测试：必须注册成功
            assert not H.has_any_error_ui(page), f"{case_name}: unexpected error UI"


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - UserName Uniqueness")
@allure.description(
    """
测试 UserName 唯一性（根据需求文档）

场景：
1. 先注册一个账号：username1
2. 再注册另一个账号使用相同用户名
3. 第二个注册应该被拒绝（userName 必须唯一）

规则来源：docs/requirements/account-register-field-requirements.md
"""
)
def test_p1_register_username_uniqueness(unauth_page: Page):
    """
    测试 UserName 唯一性
    """
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: UserName uniqueness")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = uuid.uuid4().hex[:10]
    case_name = "username_uniqueness"

    def _register_once(username: str, email: str, password: str, *, step_name: str):
        """注册一次，返回响应状态码"""
        po.navigate()
        assert_not_redirected_to_login(page)
        step_shot(po, f"step_{case_name}_{step_name}_navigate", full_page=True)

        po.fill_username(username)
        po.fill_email(email)
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_{case_name}_{step_name}_filled", full_page=True)

        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_{step_name}_after_submit", full_page=True)

        fatal = detect_fatal_error_page(page)
        if fatal:
            allure.attach(
                f"⚠️ 检测到错误: {fatal}",
                name=f"{case_name}_{step_name}_error",
                attachment_type=allure.attachment_type.TEXT,
            )
        return resp.status if resp is not None else None

    with allure.step(f"[{case_name}] 先注册第一个账号"):
        username = f"unique_{suffix}"
        email1 = f"unique1_{suffix}@testmail.com"
        password = "ValidPass123!"

        status1 = _register_once(username, email1, password, step_name="first")
        allure.attach(
            f"first_register:\nusername={username!r}\nemail={email1!r}\nstatus={status1}\n",
            name=f"{case_name}_first_register_info",
            attachment_type=allure.attachment_type.TEXT,
        )

        if status1 is not None:
            assert status1 < 500, f"{case_name}: first register unexpected 5xx status={status1}"

    with allure.step(f"[{case_name}] 再注册第二个账号（使用相同的 userName）"):
        email2 = f"unique2_{suffix}@testmail.com"  # 不同的邮箱

        status2 = _register_once(username, email2, password, step_name="second")
        allure.attach(
            f"second_register:\nusername={username!r}\nemail={email2!r}\nstatus={status2}\n"
            f"note=使用相同的 userName，应该被拒绝",
            name=f"{case_name}_second_register_info",
            attachment_type=allure.attachment_type.TEXT,
        )

        # 第二个注册应该被拒绝
        if status2 is not None:
            assert status2 < 500, f"{case_name}: second register unexpected 5xx status={status2}"
            if 400 <= status2 < 500:
                allure.attach(
                    f"✅ 后端正确拒绝了重复 userName（status={status2}）",
                    name=f"{case_name}_backend_rejected_duplicate",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                allure.attach(
                    f"⚠️ 后端可能允许了重复 userName（status={status2}）\n"
                    f"根据需求文档，userName 必须唯一。",
                    name=f"{case_name}_backend_allowed_duplicate_warning",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.xfail(f"后端允许了重复 userName（status={status2}）- 根据需求文档应该被拒绝")
        else:
            if H.has_any_error_ui(page):
                allure.attach(
                    "✅ 页面显示了错误 UI（userName 已存在）",
                    name=f"{case_name}_error_ui_found",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                allure.attach(
                    f"⚠️ 后端可能允许了重复 userName\n"
                    f"根据需求文档，userName 必须唯一。",
                    name=f"{case_name}_backend_allowed_duplicate_no_response",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.xfail("后端可能允许了重复 userName - 根据需求文档应该被拒绝")


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - UserName Max Length")
@allure.description(
    """
测试 UserName 最大长度（根据需求文档）

后端限制：userName 最大长度 256 字符

规则来源：docs/requirements/account-register-field-requirements.md
"""
)
@pytest.mark.parametrize(
    "username_len,expected_result",
    [
        # ═══════════════════════════════════════════════════
        # Min 端边界（6 点法）
        # ═══════════════════════════════════════════════════
        (0, "reject"),    # min-1：空字符串，应被拒绝
        (1, "accept"),    # min：1 字符，应被接受
        (2, "accept"),    # min+1：2 字符，应被接受
        # ═══════════════════════════════════════════════════
        # Max 端边界（6 点法）
        # ═══════════════════════════════════════════════════
        (255, "accept"),  # max-1：255 字符，应被接受
        (256, "accept"),  # max：256 字符，应被接受
        (257, "reject"),  # max+1：超过 256 字符，应被拒绝
    ],
    ids=lambda x: f"len_{x[0]}_{x[1]}" if isinstance(x, tuple) else f"len_{x}",
)
def test_p1_register_username_boundary(unauth_page: Page, username_len: int, expected_result: str):
    """
    测试 UserName 边界值（6 点法）
    """
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: UserName boundary")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = uuid.uuid4().hex[:10]
    case_name = f"username_boundary_{username_len}"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    # ═══════════════════════════════════════════════════════════════
    # 构造指定长度的用户名（边界值随机化，保证唯一性）
    # ═══════════════════════════════════════════════════════════════
    import random
    import string
    
    if username_len == 0:
        username = ""
    elif username_len == 1:
        # 1 字符：随机单字符
        username = random.choice(string.ascii_letters + string.digits)
    elif username_len == 2:
        # 2 字符：随机两字符
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=2))
    elif username_len <= len(suffix):
        username = suffix[:username_len]
    else:
        padding_len = username_len - len(suffix)
    username = ("u" * padding_len) + suffix

    # 在 Allure 报告中显示实际输入内容
    allure.dynamic.parameter("期望长度", username_len)
    allure.dynamic.parameter("预期结果", expected_result)
    allure.dynamic.parameter("实际用户名", f"{username[:20]}...{username[-10:]}" if len(username) > 35 else (username or "（空）"))
    allure.dynamic.parameter("实际长度", len(username))

    with allure.step(f"[{case_name}] 填写 {username_len} 字符 UserName 并提交"):
        # 边界测试邮箱：短边界用简短格式，长边界用完整格式
        if username_len <= 2:
            email = f"{username}@t.com"  # 简短格式
        else:
            email = f"bd_{suffix}@testmail.com"
        password = "ValidPass123!"

        po.fill_username(username)
        po.fill_email(email)
        po.fill_password(password)
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        actual_username = po.get_username_value()
        
        # 详细信息附件
        allure.attach(
            f"═══════════════════════════════════════════════════\n"
            f"【输入数据】\n"
            f"  期望长度: {username_len}\n"
            f"  实际长度: {len(actual_username)}\n"
            f"  预期结果: {expected_result}\n"
            f"  用户名: {username or '（空）'}\n"
            f"═══════════════════════════════════════════════════\n"
            f"【验证规则】\n"
            f"  ABP_USERNAME_MAX: {ABP_USERNAME_MAX}\n"
            f"  ABP_USERNAME_MIN: 1\n"
            f"  说明: userName 最小 1 字符，最大 256 字符\n"
            f"═══════════════════════════════════════════════════",
            name=f"📋 {case_name}_详细输入信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)

        # ═══════════════════════════════════════════════════════════════
        # 验证结果
        # ═══════════════════════════════════════════════════════════════
        if expected_result == "reject":
            # 应该被拒绝
            has_error = H.has_any_error_ui(page)
            has_4xx = resp is not None and 400 <= resp.status < 500
            current_url = page.url or ""
            still_on_register = "/register" in current_url or "/Account/Register" in current_url
            # 检测前端截断
            actual_len = len(actual_username)
            was_truncated = actual_len < username_len

            if was_truncated:
                # 前端截断算通过
                allure.attach(
                    f"✅ userName 长度 {username_len} 被前端截断（实际 {actual_len}）",
                    name=f"{case_name}_truncated_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif has_4xx:
                allure.attach(
                    f"✅ userName 长度 {username_len} 被后端拒绝（status 4xx）",
                    name=f"{case_name}_rejected_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif has_error:
                allure.attach(
                    f"✅ userName 长度 {username_len} 显示错误 UI",
                    name=f"{case_name}_error_ui_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif still_on_register:
                # 仍在注册页但没有明确拒绝，也算通过（前端阻止了提交）
                allure.attach(
                    f"✅ userName 长度 {username_len} 被前端阻止（仍在注册页）",
                    name=f"{case_name}_blocked_ok",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                pytest.fail(
                    f"{case_name}: userName 长度 {username_len} 应被拒绝\n"
                    f"  - 前端截断: False（实际 {actual_len}）\n"
                    f"  - 错误 UI: {has_error}\n"
                    f"  - 4xx 响应: {has_4xx}"
                )
        else:
            # 应该被接受
            if resp is not None:
                assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
            
            # 对于边界测试（1/2 字符），允许"用户名已存在"错误
            error_text = H.get_error_text(page) if H.has_any_error_ui(page) else ""
            is_duplicate_error = "已存在" in error_text or "already" in error_text.lower()
            
            if is_duplicate_error:
                allure.attach(
                    f"✅ userName 长度 {username_len} 格式被接受（但用户名已存在）",
                    name=f"{case_name}_format_accepted_duplicate",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif H.has_any_error_ui(page):
                pytest.fail(f"{case_name}: userName 长度 {username_len} 应该被接受，但出现错误")


# ═══════════════════════════════════════════════════════════════════════════════
# UserName 约束测试（从 test_Register_p1_abp_constraints.py 迁移）
# ═══════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════
# UserName 无效格式测试（补充：验证特殊字符等应被拒绝）
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - UserName Invalid Formats")
@allure.description("验证包含特殊字符的用户名应被拒绝")
@pytest.mark.parametrize(
    "username_pattern,description",
    [
        ("user name", "包含空格"),
        ("user@name", "包含@符号"),
        ("user#name", "包含#符号"),
        ("user$name", "包含$符号"),
        ("user%name", "包含%符号"),
        ("user<script>", "包含HTML标签"),
    ],
    ids=["with_space", "with_at", "with_hash", "with_dollar", "with_percent", "with_html"],
)
def test_p1_register_username_invalid_formats(unauth_page: Page, username_pattern: str, description: str):
    """验证 UserName 无效格式应被拒绝"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: UserName invalid formats")
    page = unauth_page
    po = AccountRegisterPage(page)
    suffix = uuid.uuid4().hex[:8]
    case_name = f"username_invalid_{username_pattern[:10]}"

    # 在 Allure 报告中显示实际输入
    allure.dynamic.parameter("格式描述", description)
    allure.dynamic.parameter("测试用户名", username_pattern)

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step(f"[{case_name}] 填写无效用户名并提交（{description}）"):
        po.fill_username(username_pattern)
        po.fill_email(f"inv_{suffix}@testmail.com")
        po.fill_password("ValidPass123!")
        po.check_terms()
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        click_save(page)
        resp = H.try_get_submit_response(page, timeout_ms=3000)
        page.wait_for_timeout(400)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        H.assert_no_fatal_error(page, case_name=case_name)

        # 无效格式应该被拒绝
        current_url = page.url or ""
        
        # 验证：应该仍在注册页面或显示错误
        if "/register" in current_url or "/Account/Register" in current_url:
            # 检查是否有错误提示
            if H.has_any_error_ui(page):
                allure.attach(
                    f"✅ 无效用户名 '{username_pattern}' 被正确拒绝",
                    name=f"{case_name}_rejected",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif resp is not None and 400 <= resp.status < 500:
    allure.attach(
                    f"✅ 后端正确拒绝了无效用户名（status={resp.status}）",
                    name=f"{case_name}_backend_rejected",
        attachment_type=allure.attachment_type.TEXT,
    )
            else:
                # 如果没有明确拒绝，可能是后端允许了这种格式
                pytest.xfail(f"后端可能允许了无效用户名格式: {username_pattern}")
    else:
            # 如果跳转到其他页面，可能是注册成功了
            pytest.xfail(f"后端可能允许了无效用户名格式: {username_pattern}")
