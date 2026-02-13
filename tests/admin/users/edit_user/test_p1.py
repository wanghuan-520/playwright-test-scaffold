# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - Edit User 测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面 Edit User 功能

测试点：
- 字段修改（First Name, Last Name, Email, Phone Number）
- Email 格式验证
- Email 唯一性验证
- 角色变更（member/admin）
- Active 开关
- 字段长度边界（MongoDB 不强制）
- 必填字段验证

账号来源：
- 需要 admin 账号（account_type="admin"）用于登录
- 所有编辑操作都针对专门创建的测试用户，避免污染账号池
- 每个测试用例都会创建独立的测试用户，并在 finally 中清理
"""

import uuid
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import (
    generate_unique_user,
    create_test_user,
    delete_test_user,
    AbpUserConsts,
    step_shot
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# 基础功能测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Edit User")
@allure.title("test_p1_edit_user_success - 成功修改用户信息")
def test_p1_edit_user_success(auth_page: Page):
    """
    验证：
    1. 打开 Edit User 对话框
    2. 修改 First Name, Last Name, Email, Phone Number
    3. 保存成功
    4. 用户信息已更新
    """
    logger = TestLogger("test_p1_edit_user_success")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user, name="Original", surname="Name")
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            step_shot(page_obj, "step_user_created")
            allure.attach(f"创建的测试用户: {test_user['username']}", "test_user_info")
        
        with allure.step("打开 Edit User 对话框（仅编辑创建的测试用户）"):
            # 确保只编辑我们创建的测试用户
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_edit_dialog_opened")
        
        with allure.step("修改用户信息"):
            page_obj.fill_edit_user_form(
                first_name="Updated",
                last_name="Surname",
                phone="+1234567890",
            )
            auth_page.wait_for_timeout(500)
            allure.attach(
                "First Name: Updated\nLast Name: Surname\nPhone: +1234567890",
                "filled_values", allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_fields_filled")
        
        with allure.step("保存修改"):
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_after_save")
        
        with allure.step("验证对话框已关闭"):
            edit_dialog = auth_page.locator('[role="dialog"]')
            assert not edit_dialog.is_visible(timeout=2000), "保存成功后对话框应关闭"

        with allure.step("打开 View Details 验证编辑结果"):
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_view_details()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_view_details_after_edit", full_page=True)

            details = auth_page.locator('[role="dialog"]')
            details_text = details.text_content() or ""
            allure.attach(f"View Details:\n{details_text[:500]}",
                          "view_details", allure.attachment_type.TEXT)

            # 验证编辑后的值
            assert "Updated" in details_text, "First Name 应为 Updated"
            assert "Surname" in details_text, "Last Name 应为 Surname"

            auth_page.get_by_role("button", name="Close").click()
            auth_page.wait_for_timeout(500)

        logger.end(success=True)
        
    finally:
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass



@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Edit User")
@allure.title("test_p1_edit_user_role_change - 角色变更")
def test_p1_edit_user_role_change(auth_page: Page):
    """
    验证：
    1. 修改用户角色（member ↔ admin）
    2. 角色变更成功
    """
    logger = TestLogger("test_p1_edit_user_role_change")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_role_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户（member 角色）"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            allure.attach(f"创建的测试用户: {test_user['username']}", "test_user_info")
        
        with allure.step("打开 Edit User 对话框（仅编辑创建的测试用户）"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_edit_dialog_opened")
        
        with allure.step("记录切换前的角色状态"):
            dialog = auth_page.locator('[role="dialog"]')
            # 获取当前角色状态（切换前）
            dialog_text_before = dialog.text_content() or ""
            allure.attach(f"切换前对话框内容: {dialog_text_before[:500]}", "before_role_change")
            step_shot(page_obj, "step_before_role_change", full_page=True)
        
        with allure.step("切换角色为 admin"):
            dialog = auth_page.locator('[role="dialog"]')
            
            # 查找 admin 角色按钮
            admin_role_btn = dialog.locator('button:has-text("admin")')
            if admin_role_btn.count() > 0:
                admin_role_btn.click()
                auth_page.wait_for_timeout(500)
                step_shot(page_obj, "step_admin_role_selected", full_page=True)
            
            # 保存
            save_btn = dialog.get_by_role("button", name="Save Changes")
            save_btn.click()
            auth_page.wait_for_timeout(800)  # 优化：减少等待
            step_shot(page_obj, "step_after_save")
        
        with allure.step("验证角色已变更"):
            # 保存后，重新导航到页面，确保数据刷新
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：大幅减少超时
            auth_page.wait_for_timeout(800)  # 优化：减少等待  # 额外等待确保数据完全加载
            
            # 搜索用户，确保在当前页
            page_obj.search_user(test_user["username"])
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            
            # 方法1：检查表格中的 ROLE 列
            user_row = page_obj.get_user_by_username(test_user["username"])
            if user_row.count() == 0:
                # 如果通过用户名找不到，尝试通过邮箱查找
                user_row = auth_page.locator(f'table tbody tr:has-text("{test_user["email"]}")')
            
            assert user_row.count() > 0, "应该找到用户"
            
            # 按列名动态定位 ROLE 列（不依赖硬编码索引）
            from tests.admin.users._helpers import get_cell_by_column_name
            role_text = get_cell_by_column_name(user_row.first, auth_page, "ROLE")
            
            # 如果 ROLE 列获取失败，尝试从整行文本中提取
            if not role_text or role_text.strip() == "":
                row_text = user_row.first.text_content() or ""
                # 尝试从行文本中提取角色（可能在 "admin" 或 "member" 附近）
                import re
                role_match = re.search(r'\b(admin|member|Administrator|Member)\b', row_text, re.IGNORECASE)
                if role_match:
                    role_text = role_match.group(1)
            
            allure.attach(f"ROLE 列内容: {role_text}", "role_column_info")
            allure.attach(f"整行文本: {user_row.first.text_content() or ''}", "row_text")
            
            # 方法2：如果表格中没有角色信息，尝试打开 View Details 对话框
            has_admin_in_table = "admin" in role_text.lower() or "administrator" in role_text.lower()
            
            if not has_admin_in_table:
                # 打开 View Details 对话框检查
                page_obj.click_actions_menu_for_user(test_user["username"])
                page_obj.click_view_details()
                auth_page.wait_for_timeout(600)  # 优化：减少等待
                
                details_dialog = auth_page.locator('[role="dialog"]')
                roles_text = details_dialog.text_content() or ""
                allure.attach(f"View Details 对话框内容: {roles_text[:500]}", "view_details_info")
                
                # 查找 "Assigned Roles" 部分
                assigned_roles_section = details_dialog.locator('*:has-text("Assigned Roles"), *:has-text("Role")')
                if assigned_roles_section.count() > 0:
                    # 检查 Assigned Roles 部分的内容
                    assigned_roles_text = assigned_roles_section.first.text_content() or ""
                    has_admin_in_details = "admin" in assigned_roles_text.lower() or "administrator" in assigned_roles_text.lower()
                    allure.attach(f"Assigned Roles 部分内容: {assigned_roles_text}", "assigned_roles_info")
                else:
                    has_admin_in_details = "admin" in roles_text.lower() or "administrator" in roles_text.lower()
                
                page_obj.click_close_dialog()
                
                # 验证：表格或 View Details 中任一包含 admin 即可
                assert has_admin_in_table or has_admin_in_details, \
                    f"用户应具有 admin 角色。表格 ROLE 列: {role_text}, View Details: {roles_text[:200]}"
            else:
                # 表格中已找到 admin 角色
                assert True, f"用户具有 admin 角色（在表格 ROLE 列中）: {role_text}"
        
        logger.end(success=True)
        
    finally:
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Edit User")
@allure.title("test_p1_edit_user_active_toggle - Active 开关")
def test_p1_edit_user_active_toggle(auth_page: Page):
    """
    验证：
    1. 切换 Active 开关
    2. 用户状态变更成功
    """
    logger = TestLogger("test_p1_edit_user_active_toggle")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_active_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            allure.attach(f"创建的测试用户: {test_user['username']}", "test_user_info")
        
        with allure.step("打开 Edit User 对话框（仅编辑创建的测试用户）"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_edit_dialog_opened")
        
        with allure.step("关闭 Active 开关"):
            dialog = auth_page.locator('[role="dialog"]')
            active_switch = dialog.locator('[role="switch"]')
            
            if active_switch.count() > 0:
                is_checked = active_switch.is_checked()
                if is_checked:
                    active_switch.click()
                    auth_page.wait_for_timeout(500)
                    step_shot(page_obj, "step_active_disabled")
                
                # 保存
                save_btn = dialog.get_by_role("button", name="Save Changes")
                save_btn.click()
                auth_page.wait_for_timeout(800)  # 优化：减少等待
                step_shot(page_obj, "step_after_save")
        
        with allure.step("验证状态已变更"):
            # 保存后，重新导航到页面，确保数据刷新
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：大幅减少超时
            auth_page.wait_for_timeout(800)  # 优化：减少等待  # 额外等待确保数据完全加载
            
            # 搜索用户，确保在当前页
            page_obj.search_user(test_user["username"])
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            
            # 获取用户行
            user_row = page_obj.get_user_by_username(test_user["username"])
            if user_row.count() == 0:
                # 如果通过用户名找不到，尝试通过邮箱查找
                user_row = auth_page.locator(f'table tbody tr:has-text("{test_user["email"]}")')
            
            assert user_row.count() > 0, "应该找到用户"
            
            # 按列名动态定位 STATUS 列（不依赖硬编码索引）
            from tests.admin.users._helpers import get_cell_by_column_name
            status_text = get_cell_by_column_name(user_row.first, auth_page, "STATUS")
            
            # 如果状态列获取失败，尝试从整行文本中提取状态
            if not status_text or status_text.strip() == "":
                row_text = user_row.first.text_content() or ""
                # 尝试从行文本中提取状态（通常在 "Active" 或 "Inactive" 附近）
                import re
                status_match = re.search(r'(Active|Inactive)', row_text, re.IGNORECASE)
                if status_match:
                    status_text = status_match.group(1)
            
            allure.attach(f"状态信息: {status_text}", "status_info")
            allure.attach(f"整行文本: {user_row.first.text_content() or ''}", "row_text")
            
            # 验证状态为 Inactive（不区分大小写）
            status_lower = status_text.lower()
            assert "inactive" in status_lower, f"用户状态应为 Inactive，实际: {status_text}"
        
        logger.end(success=True)
        
    finally:
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass



# 已删除重复 case:
# - test_p1_edit_user_email_readonly → 由 test_p0_edit_user_readonly_fields 覆盖
# - test_p2_edit_user_field_length_boundary → 由 matrix len_max_plus_1 覆盖
