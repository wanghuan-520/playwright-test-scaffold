# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Create Role Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Create Role 对话框功能测试

测试点：
- Create Role 对话框打开/关闭
- 字段验证（必填、唯一性）
- 创建角色成功
- Default Role 和 Public Role 开关

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_roles_page import AdminRolesPage
from tests.admin.users_roles._helpers import (
    assert_not_redirected_to_login,
    step_shot,
    delete_test_role,
    TOAST_SELECTORS,
    get_toast_text,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# P1 - Create Role 对话框基础功能
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role")
@allure.title("test_p1_create_role_dialog_open_close - Create Role 对话框打开/关闭")
def test_p1_create_role_dialog_open_close(auth_page: Page):
    """验证：Create Role 对话框可以正常打开和关闭"""
    logger = TestLogger("test_p1_create_role_dialog_open_close")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        step_shot(page_obj, "step_navigate")
    
    with allure.step("打开 Create Role 对话框"):
        page_obj.click_create_role()
        dialog_opened = page_obj.wait_for_create_role_dialog(timeout=3000)
        assert dialog_opened, "Create Role 对话框未打开"
        step_shot(page_obj, "step_dialog_opened")
    
    with allure.step("验证对话框字段可见"):
        assert page_obj.is_visible(page_obj.CREATE_ROLE_NAME_INPUT, timeout=2000), "Role Name 输入框不可见"
        assert page_obj.is_visible(page_obj.CREATE_ROLE_DEFAULT_SWITCH, timeout=2000), "Default Role 开关不可见"
        assert page_obj.is_visible(page_obj.CREATE_ROLE_PUBLIC_SWITCH, timeout=2000), "Public Role 开关不可见"
    
    with allure.step("关闭对话框（Cancel）"):
        page_obj.cancel_create_role()
        auth_page.wait_for_timeout(500)
        dialog_closed = not page_obj.is_visible(page_obj.CREATE_ROLE_DIALOG, timeout=2000)
        assert dialog_closed, "Create Role 对话框未关闭"
        step_shot(page_obj, "step_dialog_closed")
    
    logger.end(success=True)


# Role Name 相关测试已移至 test_users_roles_p1_create_role_name.py


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role")
@allure.title("test_p1_create_role_success - 创建角色成功")
def test_p1_create_role_success(auth_page: Page):
    """验证：使用有效数据创建角色成功"""
    import time
    
    logger = TestLogger("test_p1_create_role_success")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_role_{unique_suffix}"
    
    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
        
        with allure.step("打开 Create Role 对话框"):
            page_obj.click_create_role()
            page_obj.wait_for_create_role_dialog(timeout=3000)
            step_shot(page_obj, "step_dialog_opened")
        
        with allure.step("填写角色信息"):
            # 直接填写字段，避免 switch 选择器问题
            auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
            # Switch 使用默认值即可
            step_shot(page_obj, "step_form_filled")
        
        with allure.step("提交创建角色"):
            with auth_page.expect_response(lambda response: response.url.endswith("/api/identity/roles") and response.status in [200, 201], timeout=10000) as response_info:
                page_obj.submit_create_role()
            
            response = response_info.value
            assert response.status in [200, 201], f"创建角色失败，状态码: {response.status}"
        
        with allure.step("验证成功 Toast 并等待对话框关闭"):
            # 等待成功 toast 出现（Notification region > ol > li）
            try:
                auth_page.wait_for_selector(TOAST_SELECTORS, state="visible", timeout=8000)
            except Exception:
                pass
            
            # 等待对话框关闭（成功后应自动关闭）
            try:
                auth_page.wait_for_selector('[role="dialog"]', state="hidden", timeout=5000)
            except Exception:
                pass
            
            # 截全页图（包含 toast + 角色列表）
            step_shot(page_obj, "step_success_toast")
            
            # 记录 toast 文本
            toast_text = get_toast_text(auth_page)
            if toast_text:
                allure.attach(f"Toast 内容:\n{toast_text}", "success_toast_text", allure.attachment_type.TEXT)
            else:
                allure.attach("未捕获到 toast 文本（可能已自动消失）", "success_toast_text", allure.attachment_type.TEXT)
        
        with allure.step("验证角色出现在列表中"):
            auth_page.wait_for_timeout(2000)
            page_obj.navigate()  # 刷新页面
            page_obj.wait_for_roles_loaded(timeout=5000)
            
            role_exists = page_obj.is_visible(f'h3:has-text("{role_name}")', timeout=3000)
            step_shot(page_obj, "step_role_in_list")
            assert role_exists, f"角色 {role_name} 应该出现在列表中"
            allure.attach(f"角色 {role_name} 创建成功并已显示在列表中", "create_success", allure.attachment_type.TEXT)
        
        logger.end(success=True)
        
    finally:
        # 清理：删除创建的角色（如果存在）
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")


# Role Name 相关测试已移至 test_users_roles_p1_create_role_name.py


# Default Role 和 Public Role 相关测试已移至：
# - test_users_roles_p1_create_role_default_role.py
# - test_users_roles_p1_create_role_public_role.py

