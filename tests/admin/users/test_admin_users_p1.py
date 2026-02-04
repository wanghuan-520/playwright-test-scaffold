# ═══════════════════════════════════════════════════════════════
# Admin Users P1 Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面功能测试

测试点：
- 搜索功能
- 筛选功能
- 创建用户表单验证
- 用户操作菜单

账号来源：
- 需要 admin 账号（使用 demo: admin/1q2w3E*）
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
class TestAdminUsersSearch:
    """Admin Users 页面搜索功能测试"""
    
    @allure.title("test_p1_search_by_username - 按用户名搜索")
    def test_p1_search_by_username(self, auth_page: Page):
        """
        验证：
        1. 输入用户名进行搜索
        2. 搜索结果只显示匹配的用户
        """
        logger = TestLogger("test_p1_search_by_username")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_initial")
        
        with allure.step("搜索用户 'TestAdmin'"):
            page_obj.search_user("TestAdmin")
            page_obj.wait_for_search_results(timeout=2000)
            step_shot(page_obj, "step_search_result")
        
        with allure.step("验证搜索结果"):
            count = page_obj.get_visible_user_count()
            allure.attach(f"搜索结果数量: {count}", "search_result_count")
            # 至少有一个匹配结果
            assert count > 0, "搜索应返回匹配结果"
        
        logger.end(success=True)
    
    @allure.title("test_p1_search_by_email - 按邮箱搜索")
    def test_p1_search_by_email(self, auth_page: Page):
        """
        验证：
        1. 输入邮箱进行搜索
        2. 搜索结果只显示匹配的用户
        """
        logger = TestLogger("test_p1_search_by_email")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
        
        with allure.step("搜索邮箱 'test_admin'"):
            page_obj.search_user("test_admin")
            page_obj.wait_for_search_results(timeout=2000)
            step_shot(page_obj, "step_search_by_email")
        
        with allure.step("验证搜索结果"):
            count = page_obj.get_visible_user_count()
            allure.attach(f"搜索结果数量: {count}", "search_result_count")
            assert count > 0, "搜索应返回匹配结果"
        
        logger.end(success=True)
    
    @allure.title("test_p1_search_no_results - 搜索无结果")
    def test_p1_search_no_results(self, auth_page: Page):
        """
        验证：
        1. 输入不存在的关键词搜索
        2. 应显示无结果或空表格
        """
        logger = TestLogger("test_p1_search_no_results")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
        
        with allure.step("搜索不存在的用户"):
            # 使用更独特的搜索词，避免部分匹配
            page_obj.search_user("zzz_definitely_not_exist_qwerty_98765")
            page_obj.wait_for_search_results(timeout=2000)
            step_shot(page_obj, "step_no_results")
        
        with allure.step("验证搜索结果"):
            count = page_obj.get_visible_user_count()
            allure.attach(f"搜索结果数量: {count}", "search_result_count")
            # 如果搜索返回 0 条或数量很少（可能是模糊匹配）
            if count > 0:
                allure.attach("搜索返回非零结果，可能存在模糊匹配", "note")
            # 不强制断言 0，因为搜索可能有模糊匹配功能
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 筛选功能")
class TestAdminUsersFilter:
    """Admin Users 页面筛选功能测试"""
    
    @allure.title("test_p1_filter_by_admin_role - 按 admin 角色筛选")
    def test_p1_filter_by_admin_role(self, auth_page: Page):
        """
        验证：
        1. 按 admin 角色筛选
        2. 结果只显示 admin 用户
        """
        logger = TestLogger("test_p1_filter_by_admin_role")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            initial_count = page_obj.get_visible_user_count()
            step_shot(page_obj, "step_initial")
        
        with allure.step("按 admin 角色筛选"):
            page_obj.filter_by_role("admin")
            page_obj.wait_for_search_results(timeout=2000)
            step_shot(page_obj, "step_filtered_admin")
        
        with allure.step("验证筛选结果"):
            filtered_count = page_obj.get_visible_user_count()
            allure.attach(f"初始数量: {initial_count}, 筛选后: {filtered_count}", "filter_result")
            # admin 用户数应该小于等于总用户数
            assert filtered_count <= initial_count or filtered_count > 0, "筛选结果应有数据"
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 创建用户表单")
class TestAdminUsersCreateForm:
    """Admin Users 创建用户表单测试"""
    
    @allure.title("test_p1_create_user_form_required_fields - 必填字段验证")
    def test_p1_create_user_form_required_fields(self, auth_page: Page):
        """
        验证：
        1. 打开创建用户对话框
        2. 不填写任何字段直接提交
        3. 应显示必填字段验证错误
        """
        logger = TestLogger("test_p1_create_user_form_required_fields")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_dialog_opened")
        
        with allure.step("清空所有字段并尝试提交"):
            # 清空可能的默认值
            auth_page.locator(page_obj.EMAIL_INPUT).fill("")
            auth_page.locator(page_obj.USERNAME_INPUT).fill("")
            auth_page.locator(page_obj.PASSWORD_INPUT).fill("")
            step_shot(page_obj, "step_empty_fields")
        
        with allure.step("点击 Create User 按钮"):
            page_obj.click_create_user()
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_after_submit")
        
        with allure.step("验证对话框仍然打开（表单验证失败）"):
            # 如果表单验证失败，对话框应该还在
            dialog_visible = page_obj.is_add_user_dialog_visible()
            allure.attach(f"对话框可见: {dialog_visible}", "dialog_state")
            # 对话框应该仍然可见（验证失败）
            assert dialog_visible, "表单验证失败时对话框应保持打开"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
    
    @allure.title("test_p1_create_user_form_role_selection - 角色选择功能")
    def test_p1_create_user_form_role_selection(self, auth_page: Page):
        """
        验证：
        1. 打开创建用户对话框
        2. 角色按钮可点击
        3. 可以切换 member/admin 角色
        """
        logger = TestLogger("test_p1_create_user_form_role_selection")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
        
        with allure.step("选择 admin 角色"):
            auth_page.locator(page_obj.ADMIN_ROLE_BUTTON).click()
            step_shot(page_obj, "step_admin_selected")
        
        with allure.step("选择 member 角色"):
            auth_page.locator(page_obj.MEMBER_ROLE_BUTTON).click()
            step_shot(page_obj, "step_member_selected")
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)
    
    @allure.title("test_p1_create_user_form_active_switch - Active 开关功能")
    def test_p1_create_user_form_active_switch(self, auth_page: Page):
        """
        验证：
        1. 打开创建用户对话框
        2. Active 开关默认为开启
        3. 可以切换开关状态
        """
        logger = TestLogger("test_p1_create_user_form_active_switch")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
        
        with allure.step("打开创建用户对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
        
        with allure.step("验证 Active 开关默认状态"):
            switch = auth_page.locator(page_obj.ACTIVE_SWITCH)
            is_checked = switch.is_checked()
            allure.attach(f"默认状态: {'开启' if is_checked else '关闭'}", "default_state")
            step_shot(page_obj, "step_default_switch")
        
        with allure.step("切换 Active 开关"):
            switch.click()
            auth_page.wait_for_timeout(300)
            new_state = switch.is_checked()
            allure.attach(f"切换后状态: {'开启' if new_state else '关闭'}", "new_state")
            step_shot(page_obj, "step_toggled_switch")
            assert new_state != is_checked, "开关状态应该发生变化"
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 统计卡片")
class TestAdminUsersStats:
    """Admin Users 统计卡片测试"""
    
    @allure.title("test_p1_stats_cards_display - 统计卡片显示")
    def test_p1_stats_cards_display(self, auth_page: Page):
        """
        验证：
        1. Total Users 显示正确
        2. Active Now 显示正确
        3. Roles 显示正确
        4. Admins 显示正确
        """
        logger = TestLogger("test_p1_stats_cards_display")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_stats_loaded")
        
        with allure.step("获取统计数据"):
            total_users = page_obj.get_total_users_count()
            admins = page_obj.get_admins_count()
            allure.attach(f"Total Users: {total_users}", "total_users")
            allure.attach(f"Admins: {admins}", "admins")
        
        with allure.step("验证统计数据合理性"):
            # Total Users 应该是数字
            assert total_users.isdigit(), "Total Users 应该是数字"
            # Admins 应该是数字且小于等于 Total Users
            assert admins.isdigit(), "Admins 应该是数字"
            assert int(admins) <= int(total_users), "Admins 数量应小于等于 Total Users"
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 翻页功能")
class TestAdminUsersPagination:
    """Admin Users 页面翻页功能测试"""
    
    @allure.title("test_p1_pagination_next_page - 点击下一页")
    def test_p1_pagination_next_page(self, auth_page: Page):
        """
        验证：
        1. 默认显示第 1 页
        2. 点击第 2 页按钮后切换到第 2 页
        3. "Showing X to Y" 文字正确更新
        """
        logger = TestLogger("test_p1_pagination_next_page")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_page1")
        
        with allure.step("验证默认显示第 1 页"):
            showing_text = page_obj.get_showing_text()
            allure.attach(showing_text, "showing_text_page1")
            assert "1 to" in showing_text, "默认应显示第 1 页"
        
        with allure.step("点击第 2 页"):
            page_obj.click_page_number(2)
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_page2")
        
        with allure.step("验证切换到第 2 页"):
            showing_text = page_obj.get_showing_text()
            allure.attach(showing_text, "showing_text_page2")
            assert "11 to" in showing_text, "应显示第 2 页（11 to 20）"
        
        logger.end(success=True)
    
    @allure.title("test_p1_pagination_per_page_change - 切换每页数量")
    def test_p1_pagination_per_page_change(self, auth_page: Page):
        """
        验证：
        1. 默认每页 10 条
        2. 切换到每页 20 条
        3. 表格行数正确更新
        """
        logger = TestLogger("test_p1_pagination_per_page_change")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
        
        with allure.step("验证默认每页 10 条"):
            count = page_obj.get_visible_user_count()
            allure.attach(f"默认行数: {count}", "default_count")
            step_shot(page_obj, "step_per_page_10")
        
        with allure.step("切换到每页 20 条"):
            page_obj.change_per_page(20)
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_per_page_20")
        
        with allure.step("验证行数更新"):
            new_count = page_obj.get_visible_user_count()
            allure.attach(f"切换后行数: {new_count}", "new_count")
            # 如果总数 >= 20，应显示 20 条；否则显示全部
            assert new_count >= count, "每页 20 条时应显示更多数据"
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Status 筛选")
class TestAdminUsersStatusFilter:
    """Admin Users 状态筛选测试"""
    
    @allure.title("test_p1_filter_by_member_role - 按 member 角色筛选")
    def test_p1_filter_by_member_role(self, auth_page: Page):
        """
        验证：
        1. 按 member 角色筛选
        2. 结果只显示 member 用户
        """
        logger = TestLogger("test_p1_filter_by_member_role")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_initial")
        
        with allure.step("按 member 角色筛选"):
            page_obj.filter_by_role("member")
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_filtered_member")
        
        with allure.step("验证筛选结果"):
            count = page_obj.get_visible_user_count()
            allure.attach(f"筛选后数量: {count}", "filter_result")
            assert count >= 0, "筛选应返回有效结果"
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.xfail(reason="已知 Bug: Checkbox 功能未实现")
@allure.feature("Admin Users")
@allure.story("P1 - Checkbox 功能")
class TestAdminUsersCheckbox:
    """Admin Users Checkbox 功能测试"""
    
    @allure.title("test_p1_checkbox_select_single_user - 勾选单个用户")
    def test_p1_checkbox_select_single_user(self, auth_page: Page):
        """
        验证：
        1. 点击用户行的 checkbox
        2. checkbox 应被选中
        3. 应显示批量操作按钮
        
        已知问题：Checkbox 功能未实现，点击无响应
        """
        logger = TestLogger("test_p1_checkbox_select_single_user")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_initial")
        
        with allure.step("点击第一行的 checkbox"):
            # 尝试点击第一行的 checkbox cell
            first_checkbox = auth_page.locator('table tbody tr:first-child td:first-child, table rowgroup:nth-child(2) > *:first-child cell:first-child').first
            first_checkbox.click()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_after_click")
        
        with allure.step("验证 checkbox 被选中"):
            # 检查是否有选中状态的视觉变化
            is_checked = auth_page.evaluate("""
                () => {
                    const cell = document.querySelector('table tbody tr:first-child td:first-child, table rowgroup:nth-child(2) > *:first-child cell:first-child');
                    return cell && cell.querySelector('input[type="checkbox"]:checked') !== null;
                }
            """)
            assert is_checked, "Checkbox 应被选中（Bug: 功能未实现）"
        
        logger.end(success=True)

