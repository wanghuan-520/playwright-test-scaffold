# ═══════════════════════════════════════════════════════════════
# Admin Roles P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Roles 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- 角色卡片显示正常
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_roles_page import AdminRolesPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Roles")
@allure.story("P0 - 页面加载")
class TestAdminRolesP0:
    """Admin Roles 页面 P0 测试"""
    
    @allure.title("test_p0_admin_roles_page_load - 页面可打开且核心控件可见")
    def test_p0_admin_roles_page_load(self, auth_page: Page):
        """
        验证：
        1. 页面可导航到 /admin/roles
        2. 页面标题 "Roles" 可见
        3. Create Role 按钮可见
        4. 角色卡片可见
        """
        logger = TestLogger("test_p0_admin_roles_page_load")
        logger.start()
        
        page_obj = AdminRolesPage(auth_page)
        
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            step_shot(page_obj, "step_navigate")
        
        with allure.step("验证页面标题可见"):
            assert page_obj.is_loaded(), "页面未加载完成"
        
        with allure.step("验证核心控件可见"):
            assert page_obj.is_visible(page_obj.CREATE_ROLE_BUTTON, timeout=5000), "Create Role 按钮不可见"
            step_shot(page_obj, "step_verify_controls")
        
        with allure.step("验证角色卡片存在"):
            role_count = page_obj.get_role_count()
            allure.attach(f"角色数量: {role_count}", "角色统计")
            assert role_count >= 2, f"应该至少有 2 个角色（member, admin），实际: {role_count}"
        
        logger.end(success=True)
    
    @allure.title("test_p0_admin_roles_member_and_admin_visible - member 和 admin 角色可见")
    def test_p0_admin_roles_member_and_admin_visible(self, auth_page: Page):
        """
        验证：
        1. member 角色卡片可见
        2. admin 角色卡片可见
        """
        logger = TestLogger("test_p0_admin_roles_member_and_admin_visible")
        logger.start()
        
        page_obj = AdminRolesPage(auth_page)
        
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            auth_page.wait_for_timeout(1000)  # 等待数据加载
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("验证 member 角色可见"):
            assert page_obj.is_visible(page_obj.MEMBER_ROLE_CARD, timeout=5000), "member 角色卡片不可见"
        
        with allure.step("验证 admin 角色可见"):
            assert page_obj.is_visible(page_obj.ADMIN_ROLE_CARD, timeout=5000), "admin 角色卡片不可见"
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Roles")
@allure.story("P1 - Bug 验证")
class TestAdminRolesBugs:
    """Admin Roles 页面 Bug 验证测试"""
    
    @allure.title("test_p1_bug_role_user_count_inconsistent - Bug#2: 角色用户数量不一致")
    @pytest.mark.xfail(reason="已知 Bug: member 和 admin 角色都显示相同的用户数量")
    def test_p1_bug_role_user_count_inconsistent(self, auth_page: Page):
        """
        Bug #2: Roles 页面用户数量不一致
        
        现象：
        - member 角色显示 547 Users
        - admin 角色也显示 547 Users
        - 但 Users 页面统计显示只有 10 个 Admins
        
        预期：
        - 每个角色应该显示该角色的实际用户数量
        - admin 角色用户数应该 ≈ 10（Users 页面的 Admins 统计）
        """
        logger = TestLogger("test_p1_bug_role_user_count_inconsistent")
        logger.start()
        
        page_obj = AdminRolesPage(auth_page)
        
        with allure.step("导航到 Admin Roles 页面"):
            page_obj.navigate()
            auth_page.wait_for_timeout(2000)  # 等待数据加载
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("获取 member 角色用户数量"):
            member_users = page_obj.get_member_role_user_count()
            allure.attach(f"member 角色用户数: {member_users}", "member 统计")
        
        with allure.step("获取 admin 角色用户数量"):
            admin_users = page_obj.get_admin_role_user_count()
            allure.attach(f"admin 角色用户数: {admin_users}", "admin 统计")
        
        with allure.step("验证用户数量是否合理"):
            # 如果 member 和 admin 显示相同的用户数，且 admin 用户数明显过大，说明有 Bug
            if member_users == admin_users:
                # 从 Users 页面我们知道只有 10 个 Admins
                # 如果 admin 角色显示 547 Users，这明显不对
                pytest.xfail(f"Bug 确认: member({member_users}) 和 admin({admin_users}) 显示相同用户数，数据不一致")
        
        logger.end(success=True)

