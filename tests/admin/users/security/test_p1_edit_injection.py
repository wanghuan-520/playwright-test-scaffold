# ═══════════════════════════════════════════════════════════════
# Admin Users - 安全验证：Edit User 弹窗注入（精简版）
# ═══════════════════════════════════════════════════════════════
"""
Edit User 可编辑字段注入验证（精简：消除冗余，保留覆盖面）

┌──────────────┬───────┬─────────────────────────────────┐
│ 测试类型      │ 载荷数 │ 说明                            │
├──────────────┼───────┼─────────────────────────────────┤
│ Name XSS     │ 3     │ 3 种 XSS 向量，验证不执行脚本    │
│ Phone 注入   │ 3     │ 代表性载荷（XSS + SQL + 空字节） │
│ 完整链路      │ 1     │ Edit → Save → View Details      │
├──────────────┼───────┼─────────────────────────────────┤
│ 合计          │ 7     │ 从 11 精简到 7                   │
└──────────────┴───────┴─────────────────────────────────┘
"""

import time
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import generate_unique_user, create_test_user, delete_test_user
from utils.logger import TestLogger


XSS_PAYLOADS = [
    ("xss_script", "<script>alert('XSS')</script>", "XSS: script 标签"),
    ("xss_img", '<img src=x onerror="alert(1)">', "XSS: img onerror"),
    ("xss_svg", '"><svg onload=alert(1)>', "XSS: SVG onload"),
]

PHONE_REPR = [
    ("xss_script", "<script>alert('XSS')</script>", "XSS: script 标签"),
    ("sql_or", "' OR 1=1 --", "SQL: OR 1=1"),
    ("null_byte", "test\x00inject", "空字节: NULL"),
]


def _open_edit(page_obj, auth_page, username):
    page_obj.search_user(username)
    page_obj.wait_for_filter_results()
    page_obj.click_actions_menu_for_user(username)
    page_obj.click_edit_user()
    auth_page.wait_for_timeout(1000)


# ═══════════════════════════════════════════════════════════════
# 1. Name XSS 注入（3 个）→ 不执行脚本
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Edit 安全 - Name XSS")
@allure.title("test_p1_sec_edit_name_xss - Edit Name XSS 注入")
@pytest.mark.parametrize("case_id,payload,desc", XSS_PAYLOADS)
def test_p1_sec_edit_name_xss(auth_page: Page, case_id, payload, desc):
    """✅ 保存可能成功 | 但页面不执行 XSS 脚本"""
    logger = TestLogger(f"edit_xss[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user(f"ed_xss_{case_id}")
    created = []
    dialog_triggered = []
    auth_page.on("dialog", lambda d: (dialog_triggered.append(d.message), d.dismiss()))
    try:
        with allure.step("创建用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            create_test_user(page_obj, test_user)
            created.append(test_user["username"])
            page_obj.wait_for_data_loaded()
        with allure.step(f"Edit → 注入 {desc}"):
            _open_edit(page_obj, auth_page, test_user["username"])
            page_obj.fill_edit_user_form(first_name=payload, last_name=payload)
            step_shot(page_obj, "step_xss_filled")
        with allure.step("保存"):
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_saved")
        with allure.step("验证无 XSS 执行"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            auth_page.wait_for_timeout(1000)
            assert len(dialog_triggered) == 0, f"不应触发 alert: {dialog_triggered}"
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# 2. Phone 注入（3 个代表性）→ 页面不崩溃
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Edit 安全 - Phone")
@allure.title("test_p1_sec_edit_phone - Edit Phone 注入")
@pytest.mark.parametrize("case_id,payload,desc", PHONE_REPR)
def test_p1_sec_edit_phone(auth_page: Page, case_id, payload, desc):
    """✅ 页面不崩溃 | Phone 注入后不导致 500"""
    logger = TestLogger(f"edit_phone[{case_id}]")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user(f"ed_ph_{case_id}")
    created = []
    try:
        with allure.step("创建用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            create_test_user(page_obj, test_user)
            created.append(test_user["username"])
            page_obj.wait_for_data_loaded()
        with allure.step(f"Edit → 注入 {desc} 到 Phone"):
            _open_edit(page_obj, auth_page, test_user["username"])
            page_obj.fill_edit_user_form(phone=payload)
            step_shot(page_obj, "step_injected")
        with allure.step("保存并验证"):
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
            assert auth_page.title(), "页面正常"
            step_shot(page_obj, "step_saved")
        if auth_page.locator('[role="dialog"]').is_visible(timeout=500):
            page_obj.click_close_dialog()
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# 3. 完整链路：Edit → Save → View Details（1 个）
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.security
@allure.feature("Admin Users")
@allure.story("P1 - Edit 安全 - 完整链路")
@allure.title("test_p1_sec_edit_then_view_no_xss - Edit XSS → View Details 不执行")
def test_p1_sec_edit_then_view_no_xss(auth_page: Page):
    """完整链路：Edit 注入 XSS → Save → View Details → 0 次 alert"""
    logger = TestLogger("edit_view_xss")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("ed_view_xss")
    xss = "<script>alert('HACKED')</script>"
    created = []
    dialog_triggered = []
    auth_page.on("dialog", lambda d: (dialog_triggered.append(d.message), d.dismiss()))
    try:
        with allure.step("创建 → Edit XSS → Save"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            create_test_user(page_obj, test_user)
            created.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            _open_edit(page_obj, auth_page, test_user["username"])
            page_obj.fill_edit_user_form(first_name=xss, last_name=xss)
            step_shot(page_obj, "step_xss_edit")
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
        with allure.step("View Details → 不执行脚本"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_view_details()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_view_details")
            auth_page.get_by_role("button", name="Close").click()
            auth_page.wait_for_timeout(500)
        with allure.step("核心断言：0 次 alert"):
            assert len(dialog_triggered) == 0, f"全链路不应触发 XSS: {dialog_triggered}"
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass
