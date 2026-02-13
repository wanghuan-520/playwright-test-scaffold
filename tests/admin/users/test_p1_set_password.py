# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - Set Password 测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面 Set Password 功能

测试点：
- 密码匹配验证
- 密码长度验证（≥6）
- 密码策略验证（数字、大小写、特殊字符）
- 必填字段验证
- 成功设置密码

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

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
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_success - 成功设置密码")
def test_p1_set_password_success(auth_page: Page):
    """
    验证：
    1. 打开 Set Password 对话框
    2. 输入有效密码（符合策略）
    3. 确认密码匹配
    4. 保存成功
    """
    logger = TestLogger("test_p1_set_password_success")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            step_shot(page_obj, "step_user_created")
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_set_password_dialog_opened")
        
        with allure.step("输入有效密码"):
            dialog = auth_page.locator('[role="dialog"]')
            
            # 符合策略的密码：至少 6 字符，包含数字、大小写、特殊字符
            valid_password = "NewP@ss123"
            
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            new_pwd_input.fill(valid_password)
            confirm_pwd_input.fill(valid_password)
            step_shot(page_obj, "step_password_filled")
        
        with allure.step("保存密码"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(800)  # 优化：减少等待
            step_shot(page_obj, "step_after_save")
        
        with allure.step("验证对话框已关闭"):
            dialog_visible = dialog.is_visible(timeout=1000)
            assert not dialog_visible, "保存成功后对话框应关闭"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_required_fields - 必填字段验证")
def test_p1_set_password_required_fields(auth_page: Page):
    """
    验证：
    1. New Password 为空时提交
    2. Confirm Password 为空时提交
    3. 应显示必填字段验证错误
    """
    logger = TestLogger("test_p1_set_password_required_fields")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_req_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("测试 New Password 为空"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            # 清空 New Password
            new_pwd_input.fill("")
            confirm_pwd_input.fill("Test123!")
            
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(800)  # 优化：减少等待
            step_shot(page_obj, "step_new_password_empty")
            
            # 验证对话框仍然打开（浏览器原生验证）
            dialog_visible = dialog.is_visible(timeout=1000)
            allure.attach(f"对话框可见: {dialog_visible}", "dialog_state")
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_mismatch - 密码不匹配验证")
def test_p1_set_password_mismatch(auth_page: Page):
    """
    验证：
    1. New Password 和 Confirm Password 不匹配
    2. 应显示 "Passwords do not match" 错误
    """
    logger = TestLogger("test_p1_set_password_mismatch")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_mismatch_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入不匹配的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            new_pwd_input.fill("Test123!")
            confirm_pwd_input.fill("Test1234!")
            step_shot(page_obj, "step_password_mismatch")
        
        with allure.step("尝试保存并验证错误"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查是否有错误提示（Toast 或对话框内）
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = "do not match" in dialog_text.lower() or "do not match" in page_text.lower()
            allure.attach(f"错误提示: {has_error}", "error_check")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码不匹配时对话框应保持打开"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_min_length - 最小长度验证")
def test_p1_set_password_min_length(auth_page: Page):
    """
    验证：
    1. 密码少于 6 字符
    2. 应显示 "Password must be at least 6 characters" 错误
    """
    logger = TestLogger("test_p1_set_password_min_length")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_length_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入少于 6 字符的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            short_password = "Test1"  # 5 字符
            new_pwd_input.fill(short_password)
            confirm_pwd_input.fill(short_password)
            step_shot(page_obj, "step_short_password")
        
        with allure.step("尝试保存并验证错误"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查错误提示
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = "at least 6" in dialog_text.lower() or "at least 6" in page_text.lower()
            allure.attach(f"错误提示: {has_error}", "error_check")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码长度不足时对话框应保持打开"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_policy_no_digit - 密码策略：缺少数字")
def test_p1_set_password_policy_no_digit(auth_page: Page):
    """
    验证：
    1. 密码缺少数字
    2. 后端应返回 400 错误："must have at least one digit"
    """
    logger = TestLogger("test_p1_set_password_policy_no_digit")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_nodigit_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入缺少数字的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            # 缺少数字：只有大小写和特殊字符
            password_no_digit = "Test@Pass"
            new_pwd_input.fill(password_no_digit)
            confirm_pwd_input.fill(password_no_digit)
            step_shot(page_obj, "step_password_no_digit")
        
        with allure.step("保存并验证错误提示"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查是否有错误提示（Toast 或对话框内）
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = "digit" in dialog_text.lower() or "digit" in page_text.lower()
            allure.attach(f"错误提示: {has_error}", "error_check")
            allure.attach(f"对话框文本: {dialog_text[:200]}", "dialog_text")
            allure.attach(f"页面文本片段: {page_text[:500]}", "page_text")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码策略错误时对话框应保持打开"
            
            # 验证有错误提示
            assert has_error, "应显示密码策略错误提示（包含 'digit'）"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_policy_no_uppercase - 密码策略：缺少大写字母")
def test_p1_set_password_policy_no_uppercase(auth_page: Page):
    """
    验证：
    1. 密码缺少大写字母
    2. 后端应返回 400 错误："must have at least one uppercase"
    """
    logger = TestLogger("test_p1_set_password_policy_no_uppercase")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_noupper_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入缺少大写字母的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            # 缺少大写字母：只有小写、数字和特殊字符
            password_no_upper = "test123!"
            new_pwd_input.fill(password_no_upper)
            confirm_pwd_input.fill(password_no_upper)
            step_shot(page_obj, "step_password_no_uppercase")
        
        with allure.step("保存并验证错误提示"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查是否有错误提示（Toast 或对话框内）
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = "uppercase" in dialog_text.lower() or "uppercase" in page_text.lower()
            allure.attach(f"错误提示: {has_error}", "error_check")
            allure.attach(f"对话框文本: {dialog_text[:200]}", "dialog_text")
            allure.attach(f"页面文本片段: {page_text[:500]}", "page_text")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码策略错误时对话框应保持打开"
            
            # 验证有错误提示
            assert has_error, "应显示密码策略错误提示（包含 'uppercase'）"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_policy_no_lowercase - 密码策略：缺少小写字母")
def test_p1_set_password_policy_no_lowercase(auth_page: Page):
    """
    验证：
    1. 密码缺少小写字母
    2. 后端应返回 400 错误："must have at least one lowercase"
    """
    logger = TestLogger("test_p1_set_password_policy_no_lowercase")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_nolower_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入缺少小写字母的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            # 缺少小写字母：只有大写、数字和特殊字符
            password_no_lower = "TEST123!"
            new_pwd_input.fill(password_no_lower)
            confirm_pwd_input.fill(password_no_lower)
            step_shot(page_obj, "step_password_no_lowercase")
        
        with allure.step("保存并验证错误提示"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查是否有错误提示（Toast 或对话框内）
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = "lowercase" in dialog_text.lower() or "lowercase" in page_text.lower()
            allure.attach(f"错误提示: {has_error}", "error_check")
            allure.attach(f"对话框文本: {dialog_text[:200]}", "dialog_text")
            allure.attach(f"页面文本片段: {page_text[:500]}", "page_text")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码策略错误时对话框应保持打开"
            
            # 验证有错误提示
            assert has_error, "应显示密码策略错误提示（包含 'lowercase'）"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Set Password")
@allure.title("test_p1_set_password_policy_no_special - 密码策略：缺少特殊字符")
def test_p1_set_password_policy_no_special(auth_page: Page):
    """
    验证：
    1. 密码缺少特殊字符
    2. 后端应返回 400 错误："must have at least one non alphanumeric"
    """
    logger = TestLogger("test_p1_set_password_policy_no_special")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("setpwd_nospecial_test")
    created_users = []
    
    try:
        with allure.step("创建测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            # 不需要等待数据加载，直接继续
        
        with allure.step("打开 Set Password 对话框"):
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_set_password()
            auth_page.wait_for_timeout(500)  # 减少等待时间
        
        with allure.step("输入缺少特殊字符的密码"):
            dialog = auth_page.locator('[role="dialog"]')
            new_pwd_input = dialog.locator('input[type="password"]').first
            confirm_pwd_input = dialog.locator('input[type="password"]').last
            
            # 缺少特殊字符：只有大小写和数字
            password_no_special = "Test1234"
            new_pwd_input.fill(password_no_special)
            confirm_pwd_input.fill(password_no_special)
            step_shot(page_obj, "step_password_no_special")
        
        with allure.step("保存并验证错误提示"):
            set_pwd_btn = dialog.get_by_role("button", name="Set Password")
            set_pwd_btn.click()
            auth_page.wait_for_timeout(600)  # 优化：减少等待
            step_shot(page_obj, "step_error_displayed")
            
            # 检查是否有错误提示（Toast 或对话框内）
            dialog_text = dialog.text_content() or ""
            page_text = auth_page.locator('body').text_content() or ""
            
            has_error = ("non alphanumeric" in dialog_text.lower() or "special" in dialog_text.lower() or 
                        "non alphanumeric" in page_text.lower() or "special" in page_text.lower())
            allure.attach(f"错误提示: {has_error}", "error_check")
            allure.attach(f"对话框文本: {dialog_text[:200]}", "dialog_text")
            allure.attach(f"页面文本片段: {page_text[:500]}", "page_text")
            
            # 验证对话框仍然打开
            dialog_visible = dialog.is_visible(timeout=1000)
            assert dialog_visible, "密码策略错误时对话框应保持打开"
            
            # 验证有错误提示
            assert has_error, "应显示密码策略错误提示（包含 'non alphanumeric' 或 'special'）"
        
        logger.end(success=True)
        
    finally:
        # 关闭对话框（如果还打开着），避免影响删除操作
        try:
            dialog = auth_page.locator('[role="dialog"]')
            if dialog.is_visible(timeout=500):
                cancel_btn = auth_page.locator('[role="dialog"] button:has-text("Cancel")')
                if cancel_btn.is_visible(timeout=500):
                    cancel_btn.click()
                    auth_page.wait_for_timeout(300)
        except Exception:
            pass
        
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass

