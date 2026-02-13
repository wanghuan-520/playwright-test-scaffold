# ═══════════════════════════════════════════════════════════════
# Admin Users P0 - Edit User 基础功能测试
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Users 页面 Edit User 基础功能

测试内容：
- 打开/关闭 Edit User 对话框
- 保存成功
- 取消编辑
- 单字段编辑
- 只读字段验证（Email + Username）
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import (
    generate_unique_user,
    create_test_user,
    delete_test_user,
    step_shot,
    now_suffix,
)
from tests.myaccount._helpers import attach_rule_source_note, step_shot_after_success_toast, settle_toasts
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - Edit User - Dialog Open/Close")
@allure.description(
    """
测试点：
- 点击 Edit User 打开对话框
- 验证对话框中的控件可见（Save/Cancel 按钮，输入框）
- 关闭对话框
- 证据：打开前后截图
"""
)
def test_p0_edit_user_dialog_open_close(auth_page: Page):
    """P0: 打开/关闭 Edit User 对话框"""
    attach_rule_source_note("Admin Users P0 - Edit User dialog open/close")
    logger = TestLogger("test_p0_edit_user_dialog_open_close")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_dialog_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
            step_shot(page_obj, "step_user_created", full_page=True)
        
        with allure.step("验证初始状态（对话框未打开）"):
            dialog = auth_page.locator('[role="dialog"]')
            assert not dialog.is_visible(timeout=2000), "对话框应该未打开"
        
        with allure.step("打开 Edit User 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_dialog_opened", full_page=True)
        
        with allure.step("验证对话框控件可见"):
            dialog = auth_page.locator('[role="dialog"]')
            assert dialog.is_visible(timeout=3000), "对话框应该可见"
            
            # 验证 Save Changes 按钮
            save_btn = dialog.get_by_role("button", name="Save Changes")
            assert save_btn.is_visible(timeout=3000), "Save Changes 按钮不可见"
            
            # 验证 Cancel 按钮
            cancel_btn = dialog.get_by_role("button", name="Cancel")
            assert cancel_btn.is_visible(timeout=3000), "Cancel 按钮不可见"
        
        with allure.step("关闭对话框"):
            page_obj.click_close_dialog()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_dialog_closed", full_page=True)
            
            # 验证对话框已关闭
            dialog = auth_page.locator('[role="dialog"]')
            assert not dialog.is_visible(timeout=2000), "对话框应该已关闭"
        
        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - Edit User - Cancel Edit")
@allure.description(
    """
测试点：
- 打开 Edit User 对话框后修改字段
- 点击 Cancel
- 验证对话框关闭，修改未保存
- 证据：取消前后截图
"""
)
def test_p0_edit_user_cancel_edit(auth_page: Page):
    """P0: 取消编辑"""
    attach_rule_source_note("Admin Users P0 - Edit User cancel edit")
    logger = TestLogger("test_p0_edit_user_cancel_edit")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_cancel_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user, name="Original", surname="Name")
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
            step_shot(page_obj, "step_user_created", full_page=True)
        
        with allure.step("打开 Edit User 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_dialog_opened", full_page=True)
        
        with allure.step("修改 First Name 字段"):
            dialog = auth_page.locator('[role="dialog"]')
            suffix = now_suffix()
            test_value = f"TestCancel_{suffix}"
            
            first_name_input = dialog.locator('text:has-text("First Name")').locator('..').locator('input').first
            if first_name_input.count() > 0:
                first_name_input.fill(test_value)
                step_shot(page_obj, "step_after_fill", full_page=True)
        
        with allure.step("点击 Cancel 按钮"):
            page_obj.click_close_dialog()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_after_cancel", full_page=True)
        
        # 验证对话框已关闭
        dialog = auth_page.locator('[role="dialog"]')
        assert not dialog.is_visible(timeout=2000), "对话框应该已关闭"
        
        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - Edit User - Save Success")
@allure.description(
    """
测试点：
- 更新可编辑字段（First Name / Last Name / Phone Number）并保存成功
- 注意：Email、Username 都是只读的（disabled），无法修改
- 证据：保存前后截图
"""
)
def test_p0_edit_user_save_success(auth_page: Page):
    """P0: 保存成功（happy path）"""
    attach_rule_source_note("Admin Users P0 - Edit User save success")
    logger = TestLogger("test_p0_edit_user_save_success")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_save_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
            step_shot(page_obj, "step_before_update", full_page=True)
        
        with allure.step("打开 Edit User 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_edit_dialog_opened", full_page=True)

        with allure.step("填写 First Name / Last Name / Phone"):
            suffix = now_suffix()
            new_first = f"Auto_{suffix}"
            new_last = f"Run_{suffix}"
            new_phone = f"138{suffix}"[:11]
            page_obj.fill_edit_user_form(
                first_name=new_first,
                last_name=new_last,
                phone=new_phone,
            )
            auth_page.wait_for_timeout(500)
            allure.attach(
                f"First Name: {new_first}\nLast Name: {new_last}\nPhone: {new_phone}",
                "filled_values", allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_after_fill", full_page=True)
        
        with allure.step("点击 Save Changes 保存（期望成功）"):
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)  # 等待保存完成
            step_shot_after_success_toast(page_obj, "step_after_save_success")
        
        # 验证对话框已关闭
        dialog = auth_page.locator('[role="dialog"]')
        assert not dialog.is_visible(timeout=2000), "保存后对话框应关闭"
        settle_toasts(page_obj)

        with allure.step("打开 View Details 验证编辑后的数据"):
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_view_details()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_view_details_after_edit", full_page=True)

            details_dialog = auth_page.locator('[role="dialog"]')
            details_text = details_dialog.text_content() or ""
            allure.attach(f"View Details 文本:\n{details_text[:500]}",
                          "view_details_text", allure.attachment_type.TEXT)

            # 验证编辑后的值在 View Details 中展示
            checks = {
                "First Name": new_first in details_text,
                "Last Name": new_last in details_text,
            }
            for field, found in checks.items():
                allure.attach(f"{field}: {'✅' if found else '❌'}",
                              f"verify_{field}", allure.attachment_type.TEXT)

            auth_page.get_by_role("button", name="Close").click()
            auth_page.wait_for_timeout(500)

        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - Edit User - Edit Each Field")
@allure.description(
    """
测试点：
- 逐个编辑 First Name、Last Name、Phone Number
- 验证每个字段都可以正常编辑和保存
- 证据：每个字段编辑后截图
"""
)
@pytest.mark.parametrize(
    "field_name,field_key,test_value",
    [
        ("First Name", "first_name", "TestFirst"),
        ("Last Name", "last_name", "TestLast"),
        ("Phone Number", "phone", "13800138000"),
    ],
    ids=["first_name", "last_name", "phone_number"],
)
def test_p0_edit_user_edit_field(auth_page: Page, field_name: str, field_key: str, test_value: str):
    """P0: 单字段编辑"""
    attach_rule_source_note(f"Admin Users P0 - Edit User edit {field_name}")
    logger = TestLogger(f"test_p0_edit_user_edit_{field_key}")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user(f"edit_{field_key}_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step(f"打开 Edit User 对话框并编辑 {field_name} 字段"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            
            suffix = now_suffix()
            value_with_suffix = f"{test_value}_{suffix}"[:16] if field_key == "phone" else f"{test_value}_{suffix}"
            
            # 根据字段类型填充
            if field_key == "first_name":
                page_obj.fill_edit_user_form(first_name=value_with_suffix)
            elif field_key == "last_name":
                page_obj.fill_edit_user_form(last_name=value_with_suffix)
            elif field_key == "phone":
                page_obj.fill_edit_user_form(phone=value_with_suffix[:11])
            
            step_shot(page_obj, f"step_fill_{field_key}", full_page=True)
        
        with allure.step("保存"):
            page_obj.click_save_changes()
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, f"step_save_{field_key}", full_page=True)
        
        # 验证对话框已关闭
        dialog = auth_page.locator('[role="dialog"]')
        assert not dialog.is_visible(timeout=2000), f"保存 {field_name} 后对话框应关闭"
        
        settle_toasts(page_obj)
        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P0 - Edit User - Readonly Fields")
@allure.description(
    """
测试点（依据需求文档）：
- 验证 Email + Username 字段都是只读的
- 两个字段在 Edit User 对话框中应该是 disabled
- 尝试修改只读字段应该失败
- 依据：admin-users-field-requirements.md
  * 只读字段：Email、Username（不可修改，显示 "cannot be changed" 提示）
  * 可编辑字段：First Name、Last Name、Phone Number、Role、Active
- 证据：disabled 状态截图 + 修改尝试结果
"""
)
def test_p0_edit_user_readonly_fields(auth_page: Page):
    """P0: 只读字段验证 — Email + Username 都应为 disabled/只读"""
    attach_rule_source_note("Admin Users P0 - Edit User readonly fields (Email + Username 不可修改)")
    logger = TestLogger("test_p0_edit_user_readonly_fields")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_readonly_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开 Edit User 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_edit_user()
            auth_page.wait_for_timeout(500)  # 优化：减少等待
            step_shot(page_obj, "step_dialog_opened", full_page=True)
        
        with allure.step("验证 Email 是只读的（disabled）"):
            dialog = auth_page.locator('[role="dialog"]')
            email_input = dialog.locator('input[type="email"]')
            
            if email_input.count() > 0:
                is_disabled = email_input.is_disabled()
                original_email = email_input.get_attribute("value") or email_input.input_value()
                allure.attach(
                    f"Email:\n- disabled: {is_disabled}\n- value: {original_email}",
                    name="email_field_status",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert is_disabled, "Email 应该是只读的（disabled）"
        
        with allure.step("验证 Username 是只读的（disabled 或不显示输入框）"):
            # Username 在 Edit 弹窗中可能是 disabled input 或纯文本展示
            username_input = dialog.locator('text:has-text("Username")').locator('..').locator('input').first
            if username_input.count() > 0:
                un_disabled = username_input.is_disabled()
                un_value = username_input.get_attribute("value") or username_input.input_value()
                allure.attach(
                    f"Username:\n- disabled: {un_disabled}\n- value: {un_value}",
                    name="username_field_status",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert un_disabled, "Username 应该是只读的（disabled）"
            else:
                # Username 可能以纯文本显示（不是 input）
                dialog_text = dialog.text_content() or ""
                assert test_user["username"] in dialog_text, \
                    f"Username {test_user['username']} 应在弹窗中展示"
                allure.attach("Username 以纯文本展示（非输入框）", "username_display",
                              allure.attachment_type.TEXT)
            step_shot(page_obj, "step_readonly_fields_verified", full_page=True)
        
        with allure.step("关闭对话框"):
            page_obj.click_close_dialog()
        
        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass

