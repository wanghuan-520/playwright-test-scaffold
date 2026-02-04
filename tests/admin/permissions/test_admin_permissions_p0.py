# ═══════════════════════════════════════════════════════════════
# Admin Permissions P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Permissions 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- Tab 切换正常
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Permissions")
@allure.story("P0 - 页面加载")
class TestAdminPermissionsP0:
    """Admin Permissions 页面 P0 测试"""
    
    @allure.title("test_p0_admin_permissions_page_load - 页面可打开且核心控件可见")
    def test_p0_admin_permissions_page_load(self, auth_page: Page):
        """
        验证：
        1. 页面可导航到 /admin/permissions
        2. 页面标题 "Permissions" 可见
        3. Tab 选项卡可见
        4. 角色选择器可见
        """
        logger = TestLogger("test_p0_admin_permissions_page_load")
        logger.start()
        
        page_obj = AdminPermissionsPage(auth_page)
        
        with allure.step("导航到 Admin Permissions 页面"):
            page_obj.navigate()
            auth_page.wait_for_timeout(2000)  # 等待数据加载
            step_shot(page_obj, "step_navigate")
        
        with allure.step("验证页面标题可见"):
            assert page_obj.is_loaded(), "页面未加载完成"
        
        with allure.step("验证核心控件可见"):
            assert page_obj.is_visible(page_obj.ROLE_PERMISSIONS_TAB, timeout=5000), "Role Permissions Tab 不可见"
            assert page_obj.is_visible(page_obj.MEMBER_ROLE_BUTTON, timeout=5000), "member 角色按钮不可见"
            step_shot(page_obj, "step_verify_controls")
        
        logger.end(success=True)
    
    @allure.title("test_p0_admin_permissions_tab_switch - Tab 切换正常")
    def test_p0_admin_permissions_tab_switch(self, auth_page: Page):
        """
        验证：
        1. 可以切换到 User Permissions Tab
        2. 可以切换回 Role Permissions Tab
        """
        logger = TestLogger("test_p0_admin_permissions_tab_switch")
        logger.start()
        
        page_obj = AdminPermissionsPage(auth_page)
        
        with allure.step("导航到 Admin Permissions 页面"):
            page_obj.navigate()
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_initial")
        
        with allure.step("切换到 User Permissions Tab"):
            page_obj.switch_to_user_permissions()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_user_permissions_tab")
        
        with allure.step("切换回 Role Permissions Tab"):
            page_obj.switch_to_role_permissions()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_role_permissions_tab")
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Permissions")
@allure.story("P1 - Bug 验证")
class TestAdminPermissionsBugs:
    """Admin Permissions 页面 Bug 验证测试"""
    
    @allure.title("test_p1_bug_i18n_inconsistency - Bug#3: 国际化不一致")
    @pytest.mark.xfail(reason="已知 Bug: 权限名称是中文，界面是英文")
    def test_p1_bug_i18n_inconsistency(self, auth_page: Page):
        """
        Bug #3: 国际化不一致
        
        现象：
        - 权限名称是中文（身份标识管理、角色管理、创建、编辑...）
        - 但 UI 界面是英文（Permissions、Role Permissions、Grant All...）
        
        预期：
        - 权限名称应该与界面语言一致
        - 要么全中文，要么全英文
        """
        logger = TestLogger("test_p1_bug_i18n_inconsistency")
        logger.start()
        
        page_obj = AdminPermissionsPage(auth_page)
        
        with allure.step("导航到 Admin Permissions 页面"):
            page_obj.navigate()
            auth_page.wait_for_timeout(3000)  # 等待数据加载
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("检查是否存在中文权限名称"):
            has_chinese = page_obj.has_chinese_permission_names()
            allure.attach(f"存在中文权限名称: {has_chinese}", "i18n 检查")
        
        with allure.step("获取权限分组名称"):
            group_names = page_obj.get_permission_group_names()
            allure.attach("\n".join(group_names[:10]), "权限分组名称（前10个）")
        
        with allure.step("验证 i18n 一致性"):
            if has_chinese:
                pytest.xfail("Bug 确认: 权限名称是中文，但界面是英文，i18n 不一致")
        
        logger.end(success=True)

