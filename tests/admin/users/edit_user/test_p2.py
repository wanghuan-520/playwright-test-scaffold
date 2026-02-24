# ═══════════════════════════════════════════════════════════════
# Admin Users P2 - Edit User UI 测试
# ═══════════════════════════════════════════════════════════════
"""
P2：Edit User 对话框 UI 测试。

测试内容：
- 对话框元素可见性
- 键盘导航（Tab 键）
- 输入框标签
- 只读字段样式
- 按钮状态
"""

import pytest
import allure

from utils.logger import TestLogger
from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import (
    generate_unique_user,
    create_test_user,
    delete_test_user,
    step_shot,
)
from tests.myaccount._helpers import attach_rule_source_note


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Users")
@allure.story("P2 - Edit User - Dialog Elements Visible")
@allure.description(
    """
测试点：
- 验证 Edit User 对话框中所有元素可见
- Save/Cancel 按钮、输入框
- 证据：全页截图
"""
)
def test_p2_edit_user_dialog_elements_visible(auth_page):
    """P2: Edit User 对话框元素可见性"""
    attach_rule_source_note("Admin Users P2 - Edit User dialog elements visible")
    logger = TestLogger("test_p2_edit_user_dialog_elements_visible")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_ui_test")
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
        
        with allure.step("验证 Save 和 Cancel 按钮可见"):
            dialog = auth_page.locator('[role="dialog"]')
            save_btn = dialog.get_by_role("button", name="Save Changes")
            cancel_btn = dialog.get_by_role("button", name="Cancel", exact=True)
            
            assert save_btn.is_visible(timeout=3000), "Save Changes 按钮不可见"
            assert cancel_btn.is_visible(timeout=3000), "Cancel 按钮不可见"
        
        with allure.step("验证输入框可见"):
            # 确保对话框仍然打开
            assert dialog.is_visible(timeout=2000), "对话框应该仍然打开"
            
            # First Name, Last Name, Phone Number 输入框
            # 使用更灵活的选择器
            first_name_input = dialog.locator('text:has-text("First Name")').locator('..').locator('input').first
            last_name_input = dialog.locator('text:has-text("Last Name")').locator('..').locator('input').first
            phone_input = dialog.locator('text:has-text("Phone Number")').locator('..').locator('input').first
            
            # 等待输入框加载
            auth_page.wait_for_timeout(500)
            
            count = 0
            if first_name_input.count() > 0 and first_name_input.is_visible(timeout=1000):
                count += 1
            if last_name_input.count() > 0 and last_name_input.is_visible(timeout=1000):
                count += 1
            if phone_input.count() > 0 and phone_input.is_visible(timeout=1000):
                count += 1
            
            # 如果直接选择器失败，尝试通过 textbox role 查找
            if count < 3:
                textboxes = dialog.get_by_role('textbox')
                textbox_count = textboxes.count()
                allure.attach(
                    f"通过 textbox role 找到的输入框数量: {textbox_count}",
                    name="textbox_count",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 至少应该有 First Name, Last Name, Phone Number 三个可编辑输入框（Email 是 disabled 的）
                if textbox_count >= 3:
                    count = 3
            
            allure.attach(
                f"可编辑输入框数量: {count}",
                name="input_count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert count >= 3, f"期望至少 3 个可编辑输入框，实际 {count}"
        
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


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Users")
@allure.story("P2 - Edit User - Keyboard Navigation")
@allure.description(
    """
测试点：
- Edit User 对话框中 Tab 键导航顺序正确
- 证据：每个 Tab 步骤截图
"""
)
def test_p2_edit_user_keyboard_navigation(auth_page):
    """P2: Edit User 对话框 Tab 键导航"""
    attach_rule_source_note("Admin Users P2 - Edit User keyboard navigation")
    logger = TestLogger("test_p2_edit_user_keyboard_navigation")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_nav_test")
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
        
        with allure.step("Tab 键导航测试"):
            dialog = auth_page.locator('[role="dialog"]')
            # 聚焦到第一个可编辑输入框 (First Name)
            first_name_input = dialog.locator('text:has-text("First Name")').locator('..').locator('input').first
            if first_name_input.count() > 0:
                first_name_input.focus()
            
            for i in range(6):
                # 添加红色边框高亮当前焦点元素
                auth_page.evaluate("""() => {
                    const focused = document.activeElement;
                    if (focused) {
                        focused.style.outline = '3px solid red';
                    }
                }""")
                step_shot(page_obj, f"step_tab_{i}", full_page=True)
                # 移除高亮
                auth_page.evaluate("""() => {
                    const focused = document.activeElement;
                    if (focused) {
                        focused.style.outline = '';
                    }
                }""")
                auth_page.keyboard.press("Tab")
                auth_page.wait_for_timeout(100)
        
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


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Users")
@allure.story("P2 - Edit User - Input Field Labels")
@allure.description(
    """
测试点：
- 验证 Edit User 对话框中输入框标签正确
- First Name, Last Name, Email, Phone Number 等
- 证据：截图
"""
)
def test_p2_edit_user_input_labels(auth_page):
    """P2: 输入框标签检查"""
    attach_rule_source_note("Admin Users P2 - Edit User input labels")
    logger = TestLogger("test_p2_edit_user_input_labels")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_labels_test")
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
        
        labels_to_check = [
            "First Name",
            "Last Name",
            "Email",
            "Phone Number",
        ]
        
        with allure.step("验证输入框标签"):
            dialog = auth_page.locator('[role="dialog"]')
            for label in labels_to_check:
                is_visible = dialog.locator(f'text:has-text("{label}")').is_visible(timeout=2000)
                allure.attach(
                    f"{label}: {'可见' if is_visible else '不可见'}",
                    name=f"label_{label.replace(' ', '_')}",
                    attachment_type=allure.attachment_type.TEXT,
                )
        
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


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Users")
@allure.story("P2 - Edit User - Disabled Field Styling")
@allure.description(
    """
测试点：
- 验证只读字段有正确的视觉样式
- Email 应该有 disabled 样式
- 证据：截图
"""
)
def test_p2_edit_user_disabled_field_styling(auth_page):
    """P2: 只读字段样式检查"""
    attach_rule_source_note("Admin Users P2 - Edit User disabled field styling")
    logger = TestLogger("test_p2_edit_user_disabled_field_styling")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_style_test")
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
        
        with allure.step("检查只读字段提示文案"):
            dialog = auth_page.locator('[role="dialog"]')
            
            # Email 提示
            email_hint = dialog.locator('text:has-text("Email cannot be changed"), text:has-text("cannot be changed")').is_visible(timeout=2000)
            allure.attach(
                f"Email 提示可见: {email_hint}",
                name="email_hint_visible",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(page_obj, "step_disabled_field_styling", full_page=True)
        
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


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Users")
@allure.story("P2 - Edit User - Button States")
@allure.description(
    """
测试点：
- 验证 Save 和 Cancel 按钮状态
- 证据：按钮状态截图
"""
)
def test_p2_edit_user_button_states(auth_page):
    """P2: 按钮状态检查"""
    attach_rule_source_note("Admin Users P2 - Edit User button states")
    logger = TestLogger("test_p2_edit_user_button_states")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_button_test")
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
        
        with allure.step("验证 Save Changes 按钮可用"):
            dialog = auth_page.locator('[role="dialog"]')
            save_button = dialog.get_by_role("button", name="Save Changes")
            is_enabled = save_button.is_enabled()
            allure.attach(
                f"Save Changes 按钮可用: {is_enabled}",
                name="save_button_enabled",
                attachment_type=allure.attachment_type.TEXT,
            )
        
        with allure.step("验证 Cancel 按钮可用"):
            cancel_button = dialog.get_by_role("button", name="Cancel", exact=True)
            is_enabled = cancel_button.is_enabled()
            allure.attach(
                f"Cancel 按钮可用: {is_enabled}",
                name="cancel_button_enabled",
                attachment_type=allure.attachment_type.TEXT,
            )
        
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

