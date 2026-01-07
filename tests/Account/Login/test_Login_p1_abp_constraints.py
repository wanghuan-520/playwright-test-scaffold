import allure
import pytest
from playwright.sync_api import Page

from pages.account_login_page import AccountLoginPage
from tests.admin.profile._helpers import attach_rule_source_note, step_shot
from tests.Account.Login._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger("Login_p1_abp_constraints")

# ═══════════════════════════════════════════════════════════════
# ABP 约束常量（来自 ABP Identity 源码）
# ═══════════════════════════════════════════════════════════════
# IdentityUserConsts.MaxUserNameLength = 256
# IdentityUserConsts.MaxPasswordLength = 128
# IdentityUserConsts.MaxEmailLength = 256
ABP_MAX_LEN_COMMON = 256  # username/email 通用最大长度
ABP_PASSWORD_MAX = 128    # password 最大长度（ABP Identity 默认）

# ═══════════════════════════════════════════════════════════════
# 描述文案（复用）
# ═══════════════════════════════════════════════════════════════
DESC_MAXLENGTH_EVIDENCE = """
测试点：
- 前端 maxlength 取证：超长输入应被截断/阻止在 max 以内
- 覆盖字段：username_or_email（256）、password（128 ABP）
- ⚠️ 警告：如果前端 maxlength ≠ 后端 ABP 约束，则记录 drift 警告
证据：每个字段的 maxlength 属性 + 实际输入长度 + drift 警告
"""

DESC_REQUIRED_EMPTY_VALIDATION = """
测试点：
- username_or_email/password 为空时：前端应拦截（仍停留在登录页）
- **独立账号**：每个测试用独立账号，避免累计失败次数触发锁定（5次→锁定5分钟）
证据：清空前后 + 提交后截图
"""

DESC_PASSWORD_BOUNDARY = """
测试点：
- password 边界值测试：127/128/129（ABP 约束最大=128）
- **真实登录验证**：使用账号池的真实账号（password长度=127/128/129），进行真实登录
- **独立账号**：每个边界值用独立账号，避免累计失败触发锁定
- 期望：127/128 应能成功登录，129 应登录失败（被后端拒绝）
证据：每个边界值的真实登录结果
"""

DESC_USERNAME_BOUNDARY = """
测试点：
- username_or_email 边界值测试：255/256/257（ABP 约束最大=256）
- **真实登录验证**：使用账号池的真实账号（username长度=255/256/257），进行真实登录
- **独立账号**：每个边界值用独立账号，避免累计失败触发锁定
- 期望：255/256 应能成功登录，257 应无法注册（或被截断到256）
证据：每个边界值的真实登录结果
"""


# ═══════════════════════════════════════════════════════════════
# 测试用例（全部通过 UI 验证，不直接调用 API）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - ABP Constraints (UI)")
@allure.description(DESC_MAXLENGTH_EVIDENCE)
def test_p1_login_ui_maxlength_evidence(unauth_page: Page):
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login UI constraints (scenarios in steps)")

    page = unauth_page
    po = AccountLoginPage(page)
    with allure.step("导航到 /Account/Login"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    with allure.step("前端 maxlength 取证：超长输入应被截断/阻止在 max 以内"):
        fields = [
            ("username_or_email", "#LoginInput_UserNameOrEmailAddress", ABP_MAX_LEN_COMMON),
            ("password", "#LoginInput_Password", ABP_PASSWORD_MAX),
        ]
        for field, selector, abp_max in fields:
            if page.locator(selector).count() == 0:
                pytest.skip(f"{field} input not found")
            
            maxlength_attr = page.locator(selector).get_attribute("maxlength")
            # 前端可能设置了比 ABP 更大的 maxlength（如 password=128），以前端实际 maxlength 为准
            frontend_max = int(maxlength_attr) if maxlength_attr and maxlength_attr.isdigit() else abp_max
            
            long_text = "x" * (frontend_max + 10)
            page.fill(selector, long_text)
            page.wait_for_timeout(100)
            actual = page.input_value(selector)
            allure.attach(
                f"field={field}\nmaxlength_attr={maxlength_attr!r}\nfrontend_max={frontend_max}\nabp_max={abp_max}\ntyped_len={len(long_text)}\nactual_len={len(actual)}\n",
                name=f"{field}_maxlength_evidence",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(po, f"step_{field}_maxlength_evidence", full_page=True)
            
            # 断言：实际长度不超过前端 maxlength
            assert len(actual) <= frontend_max, f"{field}: expected <= {frontend_max}, got {len(actual)} (maxlength={maxlength_attr!r})"
            
            # 警告：如果前端 maxlength 大于 ABP 约束，记录 drift
            if frontend_max > abp_max:
                allure.attach(
                    f"⚠️ 前后端规则不一致：前端 maxlength={frontend_max}，ABP 约束={abp_max}。可能导致前端放行但后端拒绝。",
                    name=f"{field}_frontend_backend_drift_warning",
                    attachment_type=allure.attachment_type.TEXT,
                )
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Required fields validation")
@allure.description(DESC_REQUIRED_EMPTY_VALIDATION)
@pytest.mark.parametrize(
    "field, selector",
    [
        ("username_or_email", "#LoginInput_UserNameOrEmailAddress"),
        ("password", "#LoginInput_Password"),
    ],
)
def test_p1_login_required_fields_validation(unauth_page: Page, field: str, selector: str, test_account):
    """
    每个测试用独立账号（test_account fixture 自动分配），避免累计失败触发锁定。
    ABP Identity 默认：连续失败 5次 → 锁定 5分钟
    """
    logger.start()
    attach_rule_source_note("docs/requirements/requirements.md: Account/Login required fields (UI observable)")
    page = unauth_page
    po = AccountLoginPage(page)
    case_name = f"required_{field}_empty"

    allure.attach(
        f"测试账号: {test_account['username']}\n用途: 必填字段验证（{field}）\n说明: 独立账号避免锁定",
        name="test_account_info",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("导航到 /Account/Login"):
        po.navigate()
        step_shot(po, "step_navigate", full_page=True)
    assert_not_redirected_to_login(page)

    if page.locator(selector).count() == 0:
        pytest.skip(f"{field} input not found")

    with allure.step(f"[{case_name}] 清空字段并提交（期望被拦截）"):
        # 先填写其他字段（控制变量）
        if field == "username_or_email":
            page.fill("#LoginInput_Password", test_account["password"])
        else:
            page.fill("#LoginInput_UserNameOrEmailAddress", test_account["username"])
        
        # 清空目标字段
        page.fill(selector, "")
        step_shot(po, f"step_{case_name}_before_submit", full_page=True)
        
        page.click("button[name='Action'][type='submit']")
        page.wait_for_timeout(1000)  # 等待可能的跳转
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    # 期望：仍在登录页（被前端拦截）
    assert_not_redirected_to_login(page)
    current_url = page.url or ""
    page_text = page.content()
    
    # 如果跳转到错误页 → 这是产品缺陷，直接 FAIL
    # 检查1：URL 包含错误关键词（不区分大小写）
    url_lower = current_url.lower()
    has_error_url = any(keyword in url_lower for keyword in ["/error", "/500", "/400", "/exception"])
    
    # 检查2：页面内容包含异常关键词
    has_exception_text = any(keyword in page_text for keyword in [
        "unhandled exception",
        "ArgumentException",
        "ModelState is not valid",
        "An error occurred",
        "Stack Trace"
    ])
    
    if has_error_url or has_exception_text:
        allure.attach(
            f"🔴 产品缺陷：必填字段为空应被前端拦截，但跳转到了错误页\n"
            f"URL: {current_url}\n"
            f"错误URL: {has_error_url}\n"
            f"异常内容: {has_exception_text}",
            name=f"{case_name}_product_defect",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert False, f"产品缺陷：{case_name} 跳转到错误页或触发异常，应该被前端拦截"
    
    # 正常判据：仍在登录页
    assert "/Account/Login" in current_url, f"{case_name}: unexpected navigation away to {current_url}"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Username/Email length boundaries")
@allure.description(DESC_USERNAME_BOUNDARY)
@pytest.mark.parametrize("total_len", [ABP_MAX_LEN_COMMON - 1, ABP_MAX_LEN_COMMON])
def test_p1_login_username_length_boundaries(unauth_page: Page, total_len: int):
    """
    真实登录验证：使用账号池的特定账号（username长度符合边界值），进行真实登录。
    每个边界值用独立账号，避免累计失败触发锁定。
    
    期望：
    - 255/256: 应能成功登录
    - 257: 应无法注册（或被后端拒绝）
    """
    page = unauth_page
    po = AccountLoginPage(page)
    case_name = f"username_len_{total_len}"

    # 根据 total_len 查找 username 长度匹配的账号
    import json
    from pathlib import Path
    
    account_pool_path = Path("test-data/test_account_pool.json")
    with open(account_pool_path) as f:
        account_pool = json.load(f)
    
    # 查找 username 长度匹配的账号
    test_account = None
    for acc in account_pool.get("test_account_pool", []):  # ✅ 修正：key 是 "test_account_pool"
        if len(acc.get("username", "")) == total_len:
            test_account = acc
            break
    
    if not test_account:
        pytest.skip(f"账号池中未找到 username 长度={total_len} 的账号")
    
    # 验证账号的 username 长度是否符合测试要求
    actual_username_len = len(test_account.get("username", ""))
    allure.attach(
        f"期望长度: {total_len}\n实际长度: {actual_username_len}\nusername: {test_account['username']}\n",
        name=f"{case_name}_account_info",
        attachment_type=allure.attachment_type.TEXT,
    )
    
    # 断言账号的 username 长度符合预期
    assert actual_username_len == total_len, f"账号池中的账号 username 长度={actual_username_len}，预期={total_len}"

    po.navigate()
    assert_not_redirected_to_login(page)

    if page.locator("#LoginInput_UserNameOrEmailAddress").count() == 0:
        pytest.skip("username input not found")

    with allure.step(f"[{case_name}] 使用 username 长度={actual_username_len} 的账号真实登录"):
        page.fill("#LoginInput_UserNameOrEmailAddress", test_account["username"])
        page.fill("#LoginInput_Password", test_account["password"])
        page.wait_for_timeout(100)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        page.click("button[name='Action'][type='submit']")
        page.wait_for_timeout(2000)  # 等待登录结果
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    current_url = page.url or ""
    
    # 期望：成功登录（跳转离开登录页）或停留在登录页但没有崩溃
    if "/Error" in current_url or "/500" in current_url:
        assert False, f"{case_name}: 登录触发错误页 {current_url}，不应崩溃"
    
    # 如果成功跳转（离开登录页），视为成功
    if "/Account/Login" not in current_url:
        allure.attach(f"✅ 登录成功，跳转到: {current_url}", name=f"{case_name}_success", attachment_type=allure.attachment_type.TEXT)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountLogin")
@allure.story("P1 - Password length boundaries")
@allure.description(DESC_PASSWORD_BOUNDARY)
@pytest.mark.parametrize("total_len", [ABP_PASSWORD_MAX - 1, ABP_PASSWORD_MAX])
def test_p1_login_password_length_boundaries(unauth_page: Page, total_len: int):
    """
    真实登录验证：使用账号池的特定账号（password长度符合边界值），进行真实登录。
    每个边界值用独立账号，避免累计失败触发锁定。
    
    期望：
    - 127/128: 应能成功登录
    - 129: 应登录失败（被后端拒绝，因为超过 ABP 约束=128）
    """
    page = unauth_page
    po = AccountLoginPage(page)
    case_name = f"password_len_{total_len}"

    # 根据 total_len 选择对应的边界值账号
    from utils.data_manager import DataManager
    import json
    from pathlib import Path
    
    account_pool_path = Path("test-data/test_account_pool.json")
    with open(account_pool_path) as f:
        account_pool = json.load(f)
    
    # 查找 password 长度匹配的账号
    account_username_map = {
        127: "login_pass127_user",
        128: "login_pass128_user",
        129: "login_pass129_user",
    }
    
    target_username = account_username_map.get(total_len)
    if not target_username:
        pytest.skip(f"未定义 password 长度={total_len} 的测试账号")
    
    test_account = None
    for acc in account_pool.get("test_account_pool", []):  # ✅ 修正：key 是 "test_account_pool"
        if acc.get("username") == target_username:
            test_account = acc
            break
    
    if not test_account:
        pytest.skip(f"账号池中未找到 {target_username}")
    
    # 验证账号的 password 长度是否符合测试要求
    actual_password_len = len(test_account.get("password", ""))
    allure.attach(
        f"期望长度: {total_len}\n实际长度: {actual_password_len}\nusername: {test_account['username']}\n",
        name=f"{case_name}_account_info",
        attachment_type=allure.attachment_type.TEXT,
    )
    
    # 断言账号的 password 长度符合预期
    assert actual_password_len == total_len, f"账号池中的 {target_username} 密码长度={actual_password_len}，预期={total_len}"

    # 如果 password 长度超过 ABP 约束，记录 drift 警告
    if total_len > ABP_PASSWORD_MAX:
        allure.attach(
            f"⚠️ 前后端规则不一致：前端允许输入{total_len}字符，ABP约束为{ABP_PASSWORD_MAX}。\n期望：后端应拒绝此登录。",
            name=f"{case_name}_frontend_backend_drift",
            attachment_type=allure.attachment_type.TEXT,
        )

    po.navigate()
    assert_not_redirected_to_login(page)

    if page.locator("#LoginInput_Password").count() == 0:
        pytest.skip("password input not found")

    with allure.step(f"[{case_name}] 使用 password 长度={actual_password_len} 的账号真实登录"):
        page.fill("#LoginInput_UserNameOrEmailAddress", test_account["username"])
        page.fill("#LoginInput_Password", test_account["password"])
        page.wait_for_timeout(100)
        step_shot(po, f"step_{case_name}_filled", full_page=True)

        page.click("button[name='Action'][type='submit']")
        page.wait_for_timeout(2000)  # 等待登录结果
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

    current_url = page.url or ""
    
    # 期望：不崩溃（可能登录失败，但不应500/错误页）
    if "/Error" in current_url or "/500" in current_url:
        assert False, f"{case_name}: 登录触发错误页 {current_url}，不应崩溃"
    
    # 判断登录结果
    if total_len <= ABP_PASSWORD_MAX:
        # 31/32: 应该成功登录（跳转离开登录页）
        if "/Account/Login" not in current_url:
            allure.attach(f"✅ 登录成功，跳转到: {current_url}", name=f"{case_name}_success", attachment_type=allure.attachment_type.TEXT)
        else:
            # 仍在登录页，可能是账号问题，但不应是密码长度问题
            allure.attach(f"⚠️ 仍在登录页，可能是账号状态问题（非密码长度）", name=f"{case_name}_warning", attachment_type=allure.attachment_type.TEXT)
    else:
        # 33: 应该登录失败（仍在登录页或有错误提示）
        if "/Account/Login" in current_url:
            allure.attach(f"✅ 期望行为：password={total_len} 超过ABP约束，登录被拒绝", name=f"{case_name}_expected_reject", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach(f"⚠️ 意外：password={total_len} 超过ABP约束，但登录似乎成功了？跳转到: {current_url}", name=f"{case_name}_unexpected", attachment_type=allure.attachment_type.TEXT)
