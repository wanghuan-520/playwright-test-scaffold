# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P1 Create Role - Default Role 开关测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Create Role 对话框 - Default Role 开关完整测试

测试点：
- Default Role 默认状态验证
- Default Role 开关功能测试
- Default Role 与其他字段的组合测试

规则来源：docs/requirements/admin-pages-requirements.md
"""

import time

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_roles_page import AdminRolesPage
from tests.admin.users_roles._helpers import (
    assert_not_redirected_to_login,
    step_shot,
    delete_test_role,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# P1 - Default Role 默认状态验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Default Role")
@allure.title("test_p1_create_role_default_role_default_state - Default Role 默认状态验证")
def test_p1_create_role_default_role_default_state(auth_page: Page):
    """验证：Default Role 默认状态为 false（未选中）"""
    logger = TestLogger("test_p1_create_role_default_role_default_state")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("打开 Create Role 对话框"):
        page_obj.click_create_role()
        page_obj.wait_for_create_role_dialog(timeout=3000)
        auth_page.wait_for_timeout(500)
    
    with allure.step("验证 Default Role 默认状态"):
        default_switch = auth_page.locator(page_obj.CREATE_ROLE_DEFAULT_SWITCH).first
        if default_switch.count() == 0:
            assert False, "未找到 Default Role 开关"
        
        default_checked = default_switch.get_attribute("aria-checked") == "true"
        assert not default_checked, "Default Role 默认应该未选中（false）"
        
        step_shot(page_obj, "step_default_state")
        allure.attach(f"Default Role 默认状态: {default_checked}", "default_state")
    
    with allure.step("关闭对话框"):
        page_obj.cancel_create_role()
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Default Role 开关功能测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Default Role")
@allure.title("test_p1_create_role_default_role_toggle - Default Role 开关功能测试")
def test_p1_create_role_default_role_toggle(auth_page: Page):
    """验证：Default Role 开关可以正常切换"""
    logger = TestLogger("test_p1_create_role_default_role_toggle")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("打开 Create Role 对话框"):
        page_obj.click_create_role()
        page_obj.wait_for_create_role_dialog(timeout=3000)
        auth_page.wait_for_timeout(500)
    
    with allure.step("获取 Default Role 初始状态"):
        default_switch = auth_page.locator(page_obj.CREATE_ROLE_DEFAULT_SWITCH).first
        if default_switch.count() == 0:
            assert False, "未找到 Default Role 开关"
        
        initial_state = default_switch.get_attribute("aria-checked") == "true"
        allure.attach(f"Default Role 初始状态: {initial_state}", "initial_state")
        step_shot(page_obj, "step_initial_state")
    
    with allure.step("切换 Default Role 开关（开启）"):
        default_switch.click()
        auth_page.wait_for_timeout(500)
        new_state = default_switch.get_attribute("aria-checked") == "true"
        assert new_state != initial_state, f"Default Role 应该切换状态，初始: {initial_state}, 切换后: {new_state}"
        step_shot(page_obj, "step_toggled_on")
    
    with allure.step("再次切换 Default Role 开关（关闭）"):
        default_switch.click()
        auth_page.wait_for_timeout(500)
        final_state = default_switch.get_attribute("aria-checked") == "true"
        assert final_state == initial_state, f"Default Role 应该恢复初始状态，初始: {initial_state}, 最终: {final_state}"
        step_shot(page_obj, "step_toggled_off")
    
    with allure.step("关闭对话框"):
        page_obj.cancel_create_role()
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - Default Role 创建角色测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Default Role")
@allure.title("test_p1_create_role_with_default_role_enabled - 创建 Default Role 角色")
def test_p1_create_role_with_default_role_enabled(auth_page: Page):
    """验证：可以创建 Default Role 为 true 的角色"""
    logger = TestLogger("test_p1_create_role_with_default_role_enabled")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_default_role_{unique_suffix}"
    
    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
        
        with allure.step("打开 Create Role 对话框"):
            page_obj.click_create_role()
            page_obj.wait_for_create_role_dialog(timeout=3000)
            auth_page.wait_for_timeout(500)
        
        with allure.step("填写角色信息并启用 Default Role"):
            auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
            
            # 启用 Default Role
            default_switch = auth_page.locator(page_obj.CREATE_ROLE_DEFAULT_SWITCH).first
            if default_switch.count() == 0:
                assert False, "未找到 Default Role 开关"
            
            current_state = default_switch.get_attribute("aria-checked") == "true"
            if not current_state:
                default_switch.click()
                auth_page.wait_for_timeout(500)
            
            step_shot(page_obj, "step_default_enabled")
        
        with allure.step("提交创建角色"):
            with auth_page.expect_response(lambda response: response.url.endswith("/api/identity/roles") and response.status in [200, 201], timeout=10000) as response_info:
                page_obj.submit_create_role()
            
            response = response_info.value
            assert response.status in [200, 201], f"创建角色失败，状态码: {response.status}"
            
            # 验证响应中包含 isDefault: true
            try:
                response_body = response.json()
                is_default = response_body.get("isDefault", False)
                assert is_default, f"创建的角色应该是 Default Role，实际: {is_default}"
                allure.attach(f"角色创建成功，isDefault: {is_default}", "create_success")
            except Exception:
                pass
            
            step_shot(page_obj, "step_role_created")
            
            # 验证角色出现在列表中
            auth_page.wait_for_timeout(2000)
            page_obj.navigate()
            page_obj.wait_for_roles_loaded(timeout=5000)
            role_exists = page_obj.is_visible(f'h3:has-text("{role_name}")', timeout=3000)
            assert role_exists, f"角色 {role_name} 应该出现在列表中"
        
        logger.end(success=True)
        
    finally:
        # 清理：删除创建的角色
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")


# ═══════════════════════════════════════════════════════════════
# P1 - Default Role 与其他字段组合测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P1 - Create Role - Default Role")
@allure.title("test_p1_create_role_default_role_combinations - Default Role 与其他字段组合测试")
@pytest.mark.parametrize(
    "is_default,is_public",
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
    ids=["default_false_public_false", "default_false_public_true", "default_true_public_false", "default_true_public_true"],
)
def test_p1_create_role_default_role_combinations(
    auth_page: Page,
    is_default: bool,
    is_public: bool,
):
    """验证：Default Role 与 Public Role 的不同组合"""
    logger = TestLogger("test_p1_create_role_default_role_combinations")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    unique_suffix = int(time.time() * 1000) % 1000000
    role_name = f"test_role_{unique_suffix}"
    
    combination_desc = f"Default={is_default}, Public={is_public}"
    allure.dynamic.parameter("组合描述", combination_desc)
    
    try:
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            assert_not_redirected_to_login(auth_page)
        
        with allure.step("打开 Create Role 对话框"):
            page_obj.click_create_role()
            page_obj.wait_for_create_role_dialog(timeout=3000)
            auth_page.wait_for_timeout(500)
        
        with allure.step(f"填写角色信息并设置开关（{combination_desc}）"):
            auth_page.locator(page_obj.CREATE_ROLE_NAME_INPUT).fill(role_name)
            
            # 设置 Default Role
            default_switch = auth_page.locator(page_obj.CREATE_ROLE_DEFAULT_SWITCH).first
            if default_switch.count() > 0:
                current_default = default_switch.get_attribute("aria-checked") == "true"
                if current_default != is_default:
                    default_switch.click()
                    auth_page.wait_for_timeout(300)
            
            # 设置 Public Role
            public_switch = auth_page.locator(page_obj.CREATE_ROLE_PUBLIC_SWITCH).first
            if public_switch.count() > 0:
                current_public = public_switch.get_attribute("aria-checked") == "true"
                if current_public != is_public:
                    public_switch.click()
                    auth_page.wait_for_timeout(300)
            
            step_shot(page_obj, f"step_combination_{is_default}_{is_public}")
        
        with allure.step("提交创建角色"):
            with auth_page.expect_response(lambda response: response.url.endswith("/api/identity/roles") and response.status in [200, 201], timeout=10000) as response_info:
                page_obj.submit_create_role()
            
            response = response_info.value
            assert response.status in [200, 201], f"创建角色失败，状态码: {response.status}"
            
            # 验证响应中的开关状态
            try:
                response_body = response.json()
                actual_default = response_body.get("isDefault", False)
                actual_public = response_body.get("isPublic", False)
                assert actual_default == is_default, f"isDefault 应该为 {is_default}，实际: {actual_default}"
                assert actual_public == is_public, f"isPublic 应该为 {is_public}，实际: {actual_public}"
                allure.attach(f"角色创建成功，isDefault: {actual_default}, isPublic: {actual_public}", "create_success")
            except Exception:
                pass
            
            step_shot(page_obj, f"step_created_{is_default}_{is_public}")
            
            # 验证角色出现在列表中
            auth_page.wait_for_timeout(2000)
            page_obj.navigate()
            page_obj.wait_for_roles_loaded(timeout=5000)
            role_exists = page_obj.is_visible(f'h3:has-text("{role_name}")', timeout=3000)
            assert role_exists, f"角色 {role_name} 应该出现在列表中"
        
        logger.end(success=True)
        
    finally:
        # 清理：删除创建的角色
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")

