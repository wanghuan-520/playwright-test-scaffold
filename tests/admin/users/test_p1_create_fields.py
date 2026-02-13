# ═══════════════════════════════════════════════════════════════
# Admin Users - 创建用户测试（字段验证：Phone / Role / Active / Username 字符 / 必填非必填）
# ═══════════════════════════════════════════════════════════════

import uuid
import time
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import generate_unique_user, create_test_user, delete_test_user, AbpUserConsts, get_cell_by_column_name
from utils.logger import TestLogger

# ═══════════════════════════════════════════════════════════════
# P1 - Phone Number 验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Phone Number")
@allure.title("test_p1_create_user_with_phone - 创建用户带 Phone Number")
def test_p1_create_user_with_phone(auth_page: Page):
    """
    ✅ 预期创建成功
    Phone Number 为可选字段，填写合法号码 → 创建成功
    """
    logger = TestLogger("test_p1_create_user_with_phone")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("phone_test")
    phone = "13800138000"
    created = []

    try:
        with allure.step("导航到页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()

        with allure.step("创建用户并填写 Phone Number"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                phone=phone,
            )
            step_shot(page_obj, "step_form_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])

        with allure.step("验证创建成功"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            assert page_obj.get_visible_user_count() > 0, "用户应已创建"
            step_shot(page_obj, "step_user_created")

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Phone Number")
@allure.title("test_p1_create_user_phone_empty - Phone Number 为空（可选字段）")
def test_p1_create_user_phone_empty(auth_page: Page):
    """
    ✅ 预期创建成功
    Phone Number 为可选字段，不填 → 创建成功
    """
    logger = TestLogger("test_p1_create_user_phone_empty")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("phone_empty_test")
    created = []

    try:
        with allure.step("创建用户不填 Phone"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                phone="",  # 不填
            )
            step_shot(page_obj, "step_form_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])
            step_shot(page_obj, "step_after_create")

        with allure.step("验证创建成功"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            step_shot(page_obj, "step_user_found")
            assert page_obj.get_visible_user_count() > 0, "Phone 为空仍应创建成功"

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# P1 - Assign Roles 创建验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Assign Roles")
@allure.title("test_p1_create_user_with_admin_role - 选择 admin 角色创建")
def test_p1_create_user_with_admin_role(auth_page: Page):
    """
    ✅ 预期创建成功
    Assign Roles 选择 admin → 创建后 ROLE 列显示 admin
    """
    logger = TestLogger("test_p1_create_user_with_admin_role")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("role_admin_test")
    created = []

    try:
        with allure.step("创建 admin 角色用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                role="admin",
            )
            step_shot(page_obj, "step_admin_role_selected")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])

        with allure.step("验证 ROLE 列为 admin"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            user_row = page_obj.get_user_by_username(test_user["username"])
            assert user_row.count() > 0, "应找到用户"
            from tests.admin.users._helpers import get_cell_by_column_name
            role = get_cell_by_column_name(user_row.first, auth_page, "ROLE")
            allure.attach(f"ROLE 列: {role}", "role_value", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_role_verified")
            assert "admin" in role.lower(), f"ROLE 应为 admin，实际: {role}"

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Assign Roles")
@allure.title("test_p1_create_user_with_member_role - 默认 member 角色创建")
def test_p1_create_user_with_member_role(auth_page: Page):
    """
    ✅ 预期创建成功
    不特别选择角色（member 为默认）→ 创建后 ROLE 列显示 member
    注意：member 默认已选中，不需要额外点击
    """
    logger = TestLogger("test_p1_create_user_with_member_role")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("role_member_test")
    created = []

    try:
        with allure.step("创建用户（默认角色）"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            # 直接通过 create_test_user 创建（它内部不会做额外的角色点击）
            create_test_user(page_obj, test_user)
            created.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            step_shot(page_obj, "step_created")

        with allure.step("验证用户创建成功"):
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            user_row = page_obj.get_user_by_username(test_user["username"])
            assert user_row.count() > 0, "应找到用户"
            from tests.admin.users._helpers import get_cell_by_column_name
            role = get_cell_by_column_name(user_row.first, auth_page, "ROLE")
            allure.attach(f"ROLE 列: {role}", "role_value", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_role_verified")
            # member 是默认角色，ROLE 列应显示 member
            assert "member" in role.lower() or role == "—", \
                f"默认角色应为 member 或 —，实际: {role}"

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# P1 - Active 开关创建验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Active")
@allure.title("test_p1_create_user_inactive - Active 关闭创建用户")
def test_p1_create_user_inactive(auth_page: Page):
    """
    ✅ 预期创建成功
    Active 开关关闭 → 创建后 STATUS 列显示 Inactive（用户无法登录）
    """
    logger = TestLogger("test_p1_create_user_inactive")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("inactive_test")
    created = []

    try:
        with allure.step("创建 Inactive 用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                active=False,  # 关闭 Active
            )
            step_shot(page_obj, "step_inactive_switch")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])

        with allure.step("验证 STATUS 列为 Inactive"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            user_row = page_obj.get_user_by_username(test_user["username"])
            assert user_row.count() > 0, "应找到用户"
            from tests.admin.users._helpers import get_cell_by_column_name
            status = get_cell_by_column_name(user_row.first, auth_page, "STATUS")
            allure.attach(f"STATUS 列: {status}", "status_value", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_status_verified")
            assert "inactive" in status.lower(), f"STATUS 应为 Inactive，实际: {status}"

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Active")
@allure.title("test_p1_create_user_active_default - Active 默认开启创建用户")
def test_p1_create_user_active_default(auth_page: Page):
    """
    ✅ 预期创建成功
    Active 开关默认开启 → 创建后 STATUS 列显示 Active
    """
    logger = TestLogger("test_p1_create_user_active_default")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("active_default_test")
    created = []

    try:
        with allure.step("创建默认 Active 用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                active=True,  # 默认
            )
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])

        with allure.step("验证 STATUS 列为 Active"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            user_row = page_obj.get_user_by_username(test_user["username"])
            assert user_row.count() > 0, "应找到用户"
            from tests.admin.users._helpers import get_cell_by_column_name
            status = get_cell_by_column_name(user_row.first, auth_page, "STATUS")
            allure.attach(f"STATUS 列: {status}", "status_value", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_status_verified")
            assert "active" in status.lower() and "inactive" not in status.lower(), \
                f"STATUS 应为 Active，实际: {status}"

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# P1 - Username 各种字符混合场景
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户 Username 验证")
@allure.title("test_p1_create_user_username_mixed_chars - Username 混合字符场景")
@pytest.mark.parametrize(
    "case_id,username_suffix,should_succeed,note",
    [
        # ── 合法字符：预期创建成功 ──
        # ABP AllowedUserNameCharacters 白名单: a-zA-Z0-9 - . _ @ +
        # 后端校验: Volo.Abp.Identity:InvalidUserName（403）
        ("alphanumeric", "User123", True, "✅ 预期PASS | 字母数字 → 白名单内"),
        ("with_dot", "user.name", True, "✅ 预期PASS | . 点号 → 白名单内"),
        ("with_underscore", "user_name", True, "✅ 预期PASS | _ 下划线 → 白名单内"),
        ("with_hyphen", "user-name", True, "✅ 预期PASS | - 连字符 → 白名单内"),
        ("with_at", "user@domain", True, "✅ 预期PASS | @ 符号 → 白名单内"),
        ("with_plus", "user+test", True, "✅ 预期PASS | + 加号 → 白名单内（ASP.NET Identity 默认）"),
        ("mixed_valid", "Test.User_01-abc@x+y", True, "✅ 预期PASS | 混合全部合法字符"),
        # ── 非法字符：预期创建失败（后端返回 403 InvalidUserName）──
        ("with_space", "user name", False, "❌ 预期FAIL | 空格 → 不在白名单"),
        ("with_chinese", "用户名", False, "❌ 预期FAIL | 中文 → 不在白名单"),
        ("with_exclamation", "user!test", False, "❌ 预期FAIL | ! 感叹号 → 不在白名单"),
        ("with_hash", "user#test", False, "❌ 预期FAIL | # 井号 → 不在白名单"),
        ("with_dollar", "user$test", False, "❌ 预期FAIL | $ 美元符 → 不在白名单"),
        ("with_percent", "user%test", False, "❌ 预期FAIL | % 百分号 → 不在白名单"),
        ("with_ampersand", "user&test", False, "❌ 预期FAIL | & 与号 → 不在白名单"),
        ("with_asterisk", "user*test", False, "❌ 预期FAIL | * 星号 → 不在白名单"),
        ("with_slash", "user/test", False, "❌ 预期FAIL | / 斜杠 → 不在白名单"),
    ],
)
def test_p1_create_user_username_mixed_chars(
    auth_page: Page, case_id, username_suffix, should_succeed, note
):
    """
    ABP/ASP.NET Identity Username 校验规则：
    ─────────────────────────────────────────────
    白名单: abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@+
    校验层: 后端 ABP（Volo.Abp.Identity:InvalidUserName → HTTP 403）
    前端行为: 透传到后端，由后端校验返回错误

    ✅ 预期创建成功（should_succeed=True）: 字符全部在白名单内
    ❌ 预期创建失败（should_succeed=False）: 含白名单外字符 → 后端 403
    """
    logger = TestLogger(f"username_mixed[{case_id}]")
    logger.start()

    import time
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    username = f"u{ts}_{username_suffix}"
    email = f"u{ts}_{case_id}@test.com"
    created = []

    try:
        with allure.step(f"创建 username={username}（{note}）"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=email, username=username, password="Test@123456",
            )
            step_shot(page_obj, "step_form_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)

        with allure.step("验证结果"):
            dialog_visible = page_obj.is_add_user_dialog_visible()
            if should_succeed:
                if not dialog_visible:
                    created.append(username)
                assert not dialog_visible, f"合法({case_id}) 应成功"
            else:
                assert dialog_visible, f"非法({case_id}) 应失败"
            step_shot(page_obj, "step_result")

        if page_obj.is_add_user_dialog_visible():
            page_obj.close_dialog()
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# P1 - 必填字段逐个验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户字段验证")
@allure.title("test_p1_create_required_field_each - 必填字段逐个留空验证")
@pytest.mark.parametrize(
    "missing_field",
    ["email", "username", "password"],
    ids=["missing_email", "missing_username", "missing_password"],
)
def test_p1_create_required_field_each(auth_page: Page, missing_field: str):
    """
    必填字段验证（❌ 预期创建失败）：
    - Email*:    留空 → 对话框不关闭（前端校验 / 后端 400）
    - Username*: 留空 → 对话框不关闭（后端 400: 字段不可为空）
    - Password*: 留空 → 对话框不关闭（后端 400: 字段不可为空）
    """
    logger = TestLogger(f"required[{missing_field}]")
    logger.start()

    import time
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    form = {
        "email": f"req_{ts}@test.com",
        "username": f"req_{ts}",
        "password": "Test@123456",
    }
    form[missing_field] = ""

    with allure.step(f"{missing_field} 留空"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded()
        page_obj.click_add_user()
        auth_page.wait_for_timeout(500)
        page_obj.fill_create_user_form(**form)
        step_shot(page_obj, f"step_{missing_field}_empty")

    with allure.step("提交"):
        page_obj.click_create_user()
        auth_page.wait_for_timeout(1500)
        step_shot(page_obj, "step_after_submit")

    with allure.step(f"验证 {missing_field} 为空时创建失败"):
        assert page_obj.is_add_user_dialog_visible(), \
            f"必填字段 {missing_field} 为空应阻止创建"

    page_obj.close_dialog()
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 非必填字段全空仍可创建
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户字段验证")
@allure.title("test_p1_create_optional_fields_empty - 非必填字段全空仍可创建")
def test_p1_create_optional_fields_empty(auth_page: Page):
    """
    非必填字段验证（✅ 预期创建成功）：
    - First Name: 空 → 允许（ABP 默认可选）
    - Last Name:  空 → 允许（ABP 默认可选）
    - Phone:      空 → 允许（ABP 默认可选）
    只填 Email* + Username* + Password* → 创建成功
    """
    logger = TestLogger("optional_empty")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("opt_empty_test")
    created = []

    try:
        with allure.step("只填必填字段"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                email=test_user["email"],
                username=test_user["username"],
                password=test_user["password"],
                first_name="", last_name="", phone="",
            )
            step_shot(page_obj, "step_only_required")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)

        with allure.step("验证创建成功"):
            if not page_obj.is_add_user_dialog_visible():
                created.append(test_user["username"])
            assert not page_obj.is_add_user_dialog_visible(), \
                "只填必填字段应创建成功"
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            assert page_obj.get_visible_user_count() > 0
            step_shot(page_obj, "step_created")

        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass

# 安全验证测试已移至 tests/admin/users/security/test_p1_create_injection.py

