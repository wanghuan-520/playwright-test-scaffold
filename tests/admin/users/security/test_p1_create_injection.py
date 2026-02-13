# ═══════════════════════════════════════════════════════════════
# Admin Users - 安全验证：Create User 弹窗注入（精简版）
# ═══════════════════════════════════════════════════════════════
"""
Create User 6 个输入框的注入攻击验证（精简：消除冗余，保留覆盖面）

┌──────────────┬──────────┬───────┬─────────────────────────────┐
│ 输入框        │ 安全防线  │ 载荷数 │ 精简理由                     │
├──────────────┼──────────┼───────┼─────────────────────────────┤
│ Username *   │ ABP 白名单│ 3     │ 同一防线拦截，3 个代表性载荷  │
│ Email *      │ 格式校验  │ 2     │ 同一防线拦截，2 个代表性载荷  │
│ First Name   │ 无限制    │ 7     │ 核心：XSS 不执行验证，全保留  │
│ Last Name    │ 无限制    │ 1     │ 与 First Name 同行为，1 个代表│
│ Password *   │ 不回显    │ 1     │ 密码不展示，1 个代表性验证    │
│ Phone Number │ 无强限制  │ 7     │ 无前端截断，全保留           │
├──────────────┼──────────┼───────┼─────────────────────────────┤
│ 合计          │          │ 21    │ 从 38 精简到 21              │
└──────────────┴──────────┴───────┴─────────────────────────────┘
"""

import time
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import generate_unique_user, delete_test_user
from utils.logger import TestLogger


# ── 完整载荷集（7 个）────────────────────────────────────────
PAYLOADS_FULL = [
    ("xss_script", "<script>alert('XSS')</script>", "XSS: script 标签"),
    ("xss_img", '<img src=x onerror="alert(1)">', "XSS: img onerror"),
    ("xss_svg", '"><svg onload=alert(1)>', "XSS: SVG onload"),
    ("sql_or", "' OR 1=1 --", "SQL: OR 1=1"),
    ("sql_drop", "'; DROP TABLE users;--", "SQL: DROP TABLE"),
    ("tmpl_jinja", "{{7*7}}", "模板注入: Jinja2"),
    ("null_byte", "test\x00inject", "空字节: NULL"),
]

# ── 代表性载荷（3 个：XSS + SQL + 模板）──────────────────────
PAYLOADS_REPR_3 = [
    ("xss_script", "<script>alert('XSS')</script>", "XSS: script 标签"),
    ("sql_or", "' OR 1=1 --", "SQL: OR 1=1"),
    ("tmpl_jinja", "{{7*7}}", "模板注入: Jinja2"),
]

# ── 代表性载荷（2 个：XSS + SQL）─────────────────────────────
PAYLOADS_REPR_2 = [
    ("xss_script", "<script>alert('XSS')</script>", "XSS: script 标签"),
    ("sql_or", "' OR 1=1 --", "SQL: OR 1=1"),
]


def _safe(ts):
    return {
        "email": f"sec_{ts}@test.com",
        "username": f"sec_{ts}",
        "password": "Test@123456",
        "first_name": "Safe", "last_name": "User", "phone": "",
    }


# ═══════════════════════════════════════════════════════════════
# 1. Username 注入（3 个）→ ABP 白名单拦截
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - Username")
@allure.title("test_p1_sec_create_username - Username 注入")
@pytest.mark.parametrize("case_id,payload,desc", PAYLOADS_REPR_3)
def test_p1_sec_create_username(auth_page: Page, case_id, payload, desc):
    """❌ 预期失败 | ABP 白名单拦截 Username 中的非法字符"""
    logger = TestLogger(f"sec_username[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    with allure.step(f"注入到 Username: {desc}"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded()
        page_obj.click_add_user()
        auth_page.wait_for_timeout(500)
        vals = _safe(ts)
        vals["username"] = f"sec_{ts}_{payload}"
        page_obj.fill_create_user_form(**vals)
        step_shot(page_obj, "step_filled")
        page_obj.click_create_user()
        auth_page.wait_for_timeout(2000)
        step_shot(page_obj, "step_result")
    with allure.step("验证被拦截"):
        assert page_obj.is_add_user_dialog_visible(), f"Username 注入应被拦截: {desc}"
    page_obj.close_dialog()
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 2. Email 注入（2 个）→ 邮箱格式校验拦截
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - Email")
@allure.title("test_p1_sec_create_email - Email 注入")
@pytest.mark.parametrize("case_id,payload,desc", PAYLOADS_REPR_2)
def test_p1_sec_create_email(auth_page: Page, case_id, payload, desc):
    """❌ 预期失败 | 邮箱格式校验拦截非法 Email"""
    logger = TestLogger(f"sec_email[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    with allure.step(f"注入到 Email: {desc}"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded()
        page_obj.click_add_user()
        auth_page.wait_for_timeout(500)
        vals = _safe(ts)
        vals["email"] = payload
        page_obj.fill_create_user_form(**vals)
        step_shot(page_obj, "step_filled")
        page_obj.click_create_user()
        auth_page.wait_for_timeout(2000)
        step_shot(page_obj, "step_result")
    with allure.step("验证被拦截"):
        assert page_obj.is_add_user_dialog_visible(), f"Email 注入应被拦截: {desc}"
    page_obj.close_dialog()
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 3. First Name 注入（7 个）→ 核心：XSS 不执行
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - First Name")
@allure.title("test_p1_sec_create_first_name - First Name 注入")
@pytest.mark.parametrize("case_id,payload,desc", PAYLOADS_FULL)
def test_p1_sec_create_first_name(auth_page: Page, case_id, payload, desc):
    """✅ 可能成功 | ABP 不限制 Name 字符集，但页面不执行脚本"""
    logger = TestLogger(f"sec_fname[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    created = []
    dialog_triggered = []
    auth_page.on("dialog", lambda d: (dialog_triggered.append(d.message), d.dismiss()))
    try:
        with allure.step(f"注入到 First Name: {desc}"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            vals = _safe(ts)
            vals["username"] = f"sec_fn_{ts}_{case_id}"
            vals["email"] = f"sec_fn_{ts}_{case_id}@test.com"
            vals["first_name"] = payload
            page_obj.fill_create_user_form(**vals)
            step_shot(page_obj, "step_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            if not page_obj.is_add_user_dialog_visible():
                created.append(vals["username"])
            step_shot(page_obj, "step_result")
        with allure.step("验证无脚本执行"):
            assert len(dialog_triggered) == 0, f"不应触发 alert: {dialog_triggered}"
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
# 4. Last Name 注入（1 个代表性）→ 与 First Name 同行为
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - Last Name")
@allure.title("test_p1_sec_create_last_name - Last Name XSS 注入（代表性）")
def test_p1_sec_create_last_name(auth_page: Page):
    """✅ 与 First Name 同行为（ABP 不限制），1 个 XSS 代表性验证"""
    logger = TestLogger("sec_lname")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    created = []
    dialog_triggered = []
    auth_page.on("dialog", lambda d: (dialog_triggered.append(d.message), d.dismiss()))
    try:
        with allure.step("注入 XSS 到 Last Name"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            vals = _safe(ts)
            vals["username"] = f"sec_ln_{ts}"
            vals["email"] = f"sec_ln_{ts}@test.com"
            vals["last_name"] = "<script>alert('XSS')</script>"
            page_obj.fill_create_user_form(**vals)
            step_shot(page_obj, "step_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            if not page_obj.is_add_user_dialog_visible():
                created.append(vals["username"])
            step_shot(page_obj, "step_result")
        with allure.step("验证无脚本执行"):
            assert len(dialog_triggered) == 0, f"不应触发 alert: {dialog_triggered}"
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
# 5. Password 注入（1 个代表性）→ 密码不回显
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - Password")
@allure.title("test_p1_sec_create_password - Password XSS 注入（代表性）")
def test_p1_sec_create_password(auth_page: Page):
    """✅ 密码不回显，XSS 无安全风险，1 个代表性验证"""
    logger = TestLogger("sec_pwd")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    created = []
    try:
        with allure.step("注入 XSS 到 Password"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            vals = _safe(ts)
            vals["username"] = f"sec_pwd_{ts}"
            vals["email"] = f"sec_pwd_{ts}@test.com"
            vals["password"] = "Aa1!<script>alert(1)</script>"
            page_obj.fill_create_user_form(**vals)
            step_shot(page_obj, "step_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            if not page_obj.is_add_user_dialog_visible():
                created.append(vals["username"])
            step_shot(page_obj, "step_result")
        with allure.step("页面应正常可交互"):
            assert auth_page.title(), "页面正常"
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
# 6. Phone Number 注入（7 个）→ 无前端截断，全保留
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Create 安全 - Phone")
@allure.title("test_p1_sec_create_phone - Phone Number 注入")
@pytest.mark.parametrize("case_id,payload,desc", PAYLOADS_FULL)
def test_p1_sec_create_phone(auth_page: Page, case_id, payload, desc):
    """✅ 页面不崩溃 | Phone 无前端截断，注入后不导致 500"""
    logger = TestLogger(f"sec_phone[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    created = []
    try:
        with allure.step(f"注入到 Phone: {desc}"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            vals = _safe(ts)
            vals["username"] = f"sec_ph_{ts}_{case_id}"
            vals["email"] = f"sec_ph_{ts}_{case_id}@test.com"
            vals["phone"] = payload
            page_obj.fill_create_user_form(**vals)
            step_shot(page_obj, "step_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            if not page_obj.is_add_user_dialog_visible():
                created.append(vals["username"])
            step_shot(page_obj, "step_result")
        with allure.step("页面正常"):
            assert auth_page.title(), "页面正常"
        if page_obj.is_add_user_dialog_visible():
            page_obj.close_dialog()
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass
