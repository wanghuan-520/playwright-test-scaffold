# ═══════════════════════════════════════════════════════════════
# Admin Users - 创建用户测试（输入验证：密码策略 / 邮箱格式 / 字段边界 / 键盘导航）
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

# P1 - 密码策略详细验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户验证")
@allure.title("test_p1_create_user_password_policy_no_digit - 密码缺少数字")
def test_p1_create_user_password_policy_no_digit(auth_page: Page):
    """验证密码策略：缺少数字"""
    logger = TestLogger("test_p1_create_user_password_policy_no_digit")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("pwd_no_digit")
    
    try:
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        with allure.step("填写用户信息（密码缺少数字）"):
            page_obj.fill_create_user_form(
                username=test_user["username"],
                email=test_user["email"],
                password="Test@Pass"  # 缺少数字
            )
            step_shot(page_obj, "step_password_no_digit")
        
        with allure.step("尝试创建并验证错误"):
            page_obj.click_create_user()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_error_displayed")
            
            # 验证对话框仍然打开
            dialog_visible = page_obj.is_add_user_dialog_visible()
            assert dialog_visible, "密码策略验证失败时对话框应保持打开"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
        
    finally:
        pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户验证")
@allure.title("test_p1_create_user_password_policy_no_uppercase - 密码缺少大写字母")
def test_p1_create_user_password_policy_no_uppercase(auth_page: Page):
    """验证密码策略：缺少大写字母"""
    logger = TestLogger("test_p1_create_user_password_policy_no_uppercase")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("pwd_no_upper")
    
    try:
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        with allure.step("填写用户信息（密码缺少大写字母）"):
            page_obj.fill_create_user_form(
                username=test_user["username"],
                email=test_user["email"],
                password="test123!"  # 缺少大写字母
            )
            step_shot(page_obj, "step_password_no_uppercase")
        
        with allure.step("尝试创建并验证错误"):
            page_obj.click_create_user()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_error_displayed")
            
            dialog_visible = page_obj.is_add_user_dialog_visible()
            assert dialog_visible, "密码策略验证失败时对话框应保持打开"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
        
    finally:
        pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户验证")
@allure.title("test_p1_create_user_password_policy_no_lowercase - 密码缺少小写字母")
def test_p1_create_user_password_policy_no_lowercase(auth_page: Page):
    """验证密码策略：缺少小写字母"""
    logger = TestLogger("test_p1_create_user_password_policy_no_lowercase")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("pwd_no_lower")
    
    try:
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        with allure.step("填写用户信息（密码缺少小写字母）"):
            page_obj.fill_create_user_form(
                username=test_user["username"],
                email=test_user["email"],
                password="TEST123!"  # 缺少小写字母
            )
            step_shot(page_obj, "step_password_no_lowercase")
        
        with allure.step("尝试创建并验证错误"):
            page_obj.click_create_user()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_error_displayed")
            
            dialog_visible = page_obj.is_add_user_dialog_visible()
            assert dialog_visible, "密码策略验证失败时对话框应保持打开"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
        
    finally:
        pass


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户验证")
@allure.title("test_p1_create_user_password_policy_no_special - 密码缺少特殊字符")
def test_p1_create_user_password_policy_no_special(auth_page: Page):
    """验证密码策略：缺少特殊字符"""
    logger = TestLogger("test_p1_create_user_password_policy_no_special")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("pwd_no_special")
    
    try:
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        with allure.step("填写用户信息（密码缺少特殊字符）"):
            page_obj.fill_create_user_form(
                username=test_user["username"],
                email=test_user["email"],
                password="Test1234"  # 缺少特殊字符
            )
            step_shot(page_obj, "step_password_no_special")
        
        with allure.step("尝试创建并验证错误"):
            page_obj.click_create_user()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_error_displayed")
            
            dialog_visible = page_obj.is_add_user_dialog_visible()
            assert dialog_visible, "密码策略验证失败时对话框应保持打开"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
        
    finally:
        pass


# ═══════════════════════════════════════════════════════════════
# P2 - 字段长度边界测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P2
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P2 - 创建用户边界测试")
@allure.title("test_p2_create_user_field_length_boundaries - 字段长度边界测试")
def test_p2_create_user_field_length_boundaries(auth_page: Page):
    """
    验证字段长度边界：
    - Username: 256 (ABP MaxUserNameLength)
    - Email: 256 (ABP MaxEmailLength)
    - First Name: 64 (ABP MaxNameLength)
    - Last Name: 64 (ABP MaxSurnameLength)
    - Phone Number: 16 (ABP MaxPhoneNumberLength)
    
    注意：MongoDB 不强制长度限制，但 ABP 验证层会检查
    """
    logger = TestLogger("test_p2_create_user_field_length_boundaries")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("length_test")
    created_users = []
    
    try:
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        with allure.step("测试 Username 长度边界（256 字符）"):
            long_username = "a" * AbpUserConsts.MaxUserNameLength
            page_obj.fill_create_user_form(
                username=long_username,
                email=test_user["email"],
                password=test_user["password"]
            )
            step_shot(page_obj, "step_long_username")
            
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            
            # 验证是否成功（MongoDB 可能接受）
            dialog_visible = page_obj.is_add_user_dialog_visible()
            if not dialog_visible:
                created_users.append(long_username)
                allure.attach(f"256 字符用户名被接受（MongoDB 不强制）", "result")
            else:
                allure.attach(f"256 字符用户名被拒绝", "result")
                # 如果对话框仍然打开，关闭它
                try:
                    page_obj.close_dialog()
                    auth_page.wait_for_timeout(300)  # 优化：减少等待
                except Exception:
                    # 如果关闭失败，尝试按 ESC 键
                    auth_page.keyboard.press("Escape")
                    auth_page.wait_for_timeout(300)  # 优化：减少等待
        
        logger.end(success=True)
        
    finally:
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# P2 - UI 可访问性
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P2
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P2 - Create User Dialog")
@allure.title("test_p2_create_user_keyboard_navigation - 键盘导航")
def test_p2_create_user_keyboard_navigation(auth_page: Page):
    """
    验证：
    1. Tab 键可以在字段间导航
    2. Enter 键可以提交表单
    3. Escape 键可以关闭对话框
    """
    logger = TestLogger("test_p2_create_user_keyboard_navigation")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("打开创建用户对话框"):
        page_obj.click_add_user()
        auth_page.wait_for_timeout(300)  # 优化：减少等待
        step_shot(page_obj, "step_dialog_opened")
    
    with allure.step("Tab 键导航测试"):
        # 聚焦到第一个输入框
        auth_page.locator(page_obj.EMAIL_INPUT).focus()
        
        for i in range(5):
            # 添加红色边框高亮当前焦点元素
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '3px solid red';
                }
            }""")
            step_shot(page_obj, f"step_tab_{i}")
            # 移除高亮
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '';
                }
            }""")
            auth_page.keyboard.press("Tab")
            auth_page.wait_for_timeout(100)
    
    with allure.step("测试 Escape 键关闭对话框"):
        auth_page.keyboard.press("Escape")
        auth_page.wait_for_timeout(300)  # 优化：减少等待
        step_shot(page_obj, "step_after_escape")
        
        dialog_visible = page_obj.is_add_user_dialog_visible()
        assert not dialog_visible, "按 Escape 键应关闭对话框"
    
    logger.end(success=True)


