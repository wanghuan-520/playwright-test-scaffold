# ═══════════════════════════════════════════════════════════════
# Admin Users - E2E 集成测试：用户全生命周期
# ═══════════════════════════════════════════════════════════════
"""
E2E 集成测试：创建 → 搜索 → 编辑 → 查看详情 → 设置密码 → 删除

验证整个用户管理的完整业务流程在一次测试中串联执行，
确保各功能模块之间的衔接没有问题。
"""

import time
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import (
    generate_unique_user, get_cell_by_column_name,
)
from utils.logger import TestLogger


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("E2E - 用户全生命周期")
@allure.title("test_e2e_user_lifecycle - 创建→搜索→编辑→查看→设置密码→删除")
def test_e2e_user_lifecycle(auth_page: Page):
    """
    E2E 全链路：
    1. 创建用户（填写所有字段）
    2. 搜索验证用户存在
    3. 编辑用户（修改 First Name / Last Name）
    4. View Details 验证编辑结果
    5. Set Password 设置新密码
    6. 删除用户
    7. 搜索验证用户已删除
    """
    logger = TestLogger("test_e2e_user_lifecycle")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    ts = int(time.time())
    user = generate_unique_user("e2e_lifecycle")
    username = user["username"]
    email = user["email"]
    password = user["password"]

    try:
        # ── Step 1: 创建用户 ─────────────────────────────────
        with allure.step("1️⃣ 创建用户（全字段）"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                first_name="E2E",
                last_name="Test",
                email=email,
                username=username,
                password=password,
                phone="13800000001",
                role="member",
                active=True,
            )
            step_shot(page_obj, "step_1_create_form")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            assert not page_obj.is_add_user_dialog_visible(), "创建应成功"
            step_shot(page_obj, "step_1_created")
            allure.attach(f"✅ 创建成功: {username}", "step_1", allure.attachment_type.TEXT)

        # ── Step 2: 搜索验证 ─────────────────────────────────
        with allure.step("2️⃣ 搜索验证用户存在"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            count = page_obj.get_visible_user_count()
            assert count > 0, f"搜索 {username} 应有结果"
            role = get_cell_by_column_name(
                page_obj.get_user_by_username(username).first, auth_page, "ROLE"
            )
            status = get_cell_by_column_name(
                page_obj.get_user_by_username(username).first, auth_page, "STATUS"
            )
            allure.attach(f"ROLE: {role}, STATUS: {status}", "step_2", allure.attachment_type.TEXT)
            step_shot(page_obj, "step_2_found")

        # ── Step 3: 编辑用户 ─────────────────────────────────
        with allure.step("3️⃣ 编辑用户（修改 First/Last Name）"):
            page_obj.click_actions_menu_for_user(username)
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(1000)
            page_obj.fill_edit_user_form(
                first_name="Updated",
                last_name="Name",
            )
            step_shot(page_obj, "step_3_edit_filled")
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_3_saved")
            allure.attach("✅ 编辑成功", "step_3", allure.attachment_type.TEXT)

        # ── Step 4: View Details 验证 ─────────────────────────
        with allure.step("4️⃣ View Details 验证编辑结果"):
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            page_obj.click_actions_menu_for_user(username)
            page_obj.click_view_details()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_4_view_details")
            dialog = auth_page.locator('[role="dialog"]')
            text = dialog.text_content() or ""
            allure.attach(f"View Details:\n{text[:400]}", "step_4", allure.attachment_type.TEXT)
            assert "Updated" in text, "First Name 应为 Updated"
            auth_page.get_by_role("button", name="Close").click()
            auth_page.wait_for_timeout(500)

        # ── Step 5: Set Password ──────────────────────────────
        with allure.step("5️⃣ Set Password"):
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            page_obj.click_actions_menu_for_user(username)
            page_obj.click_set_password()
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_5_set_password_dialog")
            # 填写新密码
            dialog = auth_page.locator('[role="dialog"]')
            pwd_inputs = dialog.locator('input[type="password"]').all()
            if len(pwd_inputs) >= 2:
                pwd_inputs[0].fill("NewP@ss123")
                pwd_inputs[1].fill("NewP@ss123")
            # 点保存
            save_btn = dialog.get_by_role("button", name="Set Password").or_(
                dialog.get_by_role("button", name="Save")
            )
            if save_btn.count() > 0:
                save_btn.first.click()
                auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_5_password_set")
            allure.attach("✅ 密码设置完成", "step_5", allure.attachment_type.TEXT)

        # ── Step 6: 删除用户 ──────────────────────────────────
        with allure.step("6️⃣ 删除用户"):
            # 关闭残留弹窗
            if auth_page.locator('[role="dialog"]').is_visible(timeout=500):
                auth_page.keyboard.press("Escape")
                auth_page.wait_for_timeout(500)
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            page_obj.delete_user(username)
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_6_deleted")
            allure.attach("✅ 删除完成", "step_6", allure.attachment_type.TEXT)

        # ── Step 7: 验证已删除 ────────────────────────────────
        with allure.step("7️⃣ 搜索验证用户已删除"):
            # 刷新页面确保删除生效
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            auth_page.wait_for_timeout(1500)
            count = page_obj.get_visible_user_count()
            step_shot(page_obj, "step_7_verified_deleted")
            # 删除后列表可能仍有 "No data" 显示为 0 行
            no_data = auth_page.locator("text=No data").or_(
                auth_page.locator("text=No users found")
            )
            if no_data.count() > 0:
                count = 0
            assert count == 0, f"用户 {username} 应已删除，但搜索到 {count} 条"
            allure.attach("✅ 用户已删除", "step_7", allure.attachment_type.TEXT)

        logger.end(success=True)

    except Exception:
        # 清理：如果测试中途失败，尝试删除用户
        try:
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.search_user(username)
            page_obj.wait_for_filter_results()
            if page_obj.get_visible_user_count() > 0:
                page_obj.delete_user(username)
        except Exception:
            pass
        raise
