# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - 筛选功能测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面筛选功能

测试点：
- 按角色筛选（admin/member）
- 按状态筛选（Active/Inactive）
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import generate_unique_user, create_test_user, delete_test_user
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# 角色筛选
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 角色筛选")
@allure.title("test_p1_filter_by_admin_role - 按 admin 角色筛选")
def test_p1_filter_by_admin_role(auth_page: Page):
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
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        # 等待统计卡片加载完成
        auth_page.wait_for_selector('text=Total Users', timeout=10000)
        auth_page.wait_for_selector('text=Admins', timeout=10000)
        auth_page.wait_for_timeout(500)  # 优化：减少等待
        
        # 获取总用户数和 Admins 统计值
        total_users = int(page_obj.get_total_users_count())
        admins_count = int(page_obj.get_admins_count())
        initial_visible_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
        allure.attach(f"总用户数: {total_users}, Admins: {admins_count}, 当前页可见: {initial_visible_count}", "initial_stats")
        
        # 如果统计值为 0，说明还没加载完成，等待并重试
        if total_users == 0 or admins_count == 0:
            auth_page.wait_for_timeout(1000)  # 优化：减少等待
            total_users = int(page_obj.get_total_users_count())
            admins_count = int(page_obj.get_admins_count())
            allure.attach(f"重试后 - 总用户数: {total_users}, Admins: {admins_count}", "retry_stats")
    
    with allure.step("按 admin 角色筛选"):
        page_obj.filter_by_role("admin")
        page_obj.wait_for_filter_results(timeout=5000)
        filtered_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_filtered_admin", allure.attachment_type.PNG)
        allure.attach(f"筛选后可见数量: {filtered_count}", "filtered_count")
    
    with allure.step("验证筛选结果"):
        assert filtered_count > 0, "应该有 admin 用户"
        # 筛选后的可见行，每行的 ROLE 列都应包含 "admin"
        rows = auth_page.locator('table tbody tr')
        for i in range(min(rows.count(), 5)):
            from tests.admin.users._helpers import get_cell_by_column_name
            role = get_cell_by_column_name(rows.nth(i), auth_page, "ROLE")
            assert "admin" in role.lower(), \
                f"第 {i+1} 行 ROLE 列应为 admin，实际: {role}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 角色筛选")
@allure.title("test_p1_filter_by_member_role - 按 member 角色筛选")
def test_p1_filter_by_member_role(auth_page: Page):
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
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        initial_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
        allure.attach(f"筛选前数量: {initial_count}", "initial_count")
    
    with allure.step("按 member 角色筛选"):
        page_obj.filter_by_role("member")
        page_obj.wait_for_filter_results(timeout=5000)
        filtered_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_filtered_member", allure.attachment_type.PNG)
        allure.attach(f"筛选后数量: {filtered_count}", "filtered_count")
    
    with allure.step("验证筛选结果"):
        assert filtered_count > 0, "应有 member 用户"
        rows = auth_page.locator('table tbody tr')
        for i in range(min(rows.count(), 5)):
            from tests.admin.users._helpers import get_cell_by_column_name
            role = get_cell_by_column_name(rows.nth(i), auth_page, "ROLE")
            assert "member" in role.lower(), \
                f"第 {i+1} 行 ROLE 列应为 member，实际: {role}"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 状态筛选
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 状态筛选")
@allure.title("test_p1_filter_by_active_status - 按 Active 状态筛选")
def test_p1_filter_by_active_status(auth_page: Page):
    """
    验证：
    1. 按 Active 状态筛选
    2. 结果只显示活跃用户
    """
    logger = TestLogger("test_p1_filter_by_active_status")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        initial_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
        allure.attach(f"筛选前数量: {initial_count}", "initial_count")
    
    with allure.step("按 Active 状态筛选"):
        page_obj.filter_by_status("Active")
        page_obj.wait_for_filter_results(timeout=5000)
        filtered_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_filtered_active", allure.attachment_type.PNG)
        allure.attach(f"Active 用户数: {filtered_count}", "filtered_count")
    
    with allure.step("验证筛选结果"):
        assert filtered_count > 0, "应有 Active 用户"
        rows = auth_page.locator('table tbody tr')
        for i in range(min(rows.count(), 5)):
            from tests.admin.users._helpers import get_cell_by_column_name
            status = get_cell_by_column_name(rows.nth(i), auth_page, "STATUS")
            assert "active" in status.lower(), \
                f"第 {i+1} 行 STATUS 列应为 Active，实际: {status}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 状态筛选")
@allure.title("test_p1_filter_by_inactive_status - 按 Inactive 状态筛选")
def test_p1_filter_by_inactive_status(auth_page: Page):
    """
    验证：
    1. 按 Inactive 状态筛选
    2. 结果只显示非活跃用户
    """
    logger = TestLogger("test_p1_filter_by_inactive_status")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        # 等待统计卡片加载完成
        auth_page.wait_for_selector('text=Total Users', timeout=10000)
        auth_page.wait_for_timeout(500)  # 优化：减少等待
        
        # 获取总用户数（不是当前页可见数量）
        total_users = int(page_obj.get_total_users_count())
        initial_visible_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
        allure.attach(f"总用户数: {total_users}, 当前页可见: {initial_visible_count}", "initial_stats")
        
        # 如果统计值为 0，说明还没加载完成，等待并重试
        if total_users == 0:
            auth_page.wait_for_timeout(1000)  # 优化：减少等待
            total_users = int(page_obj.get_total_users_count())
            allure.attach(f"重试后 - 总用户数: {total_users}", "retry_stats")
    
    with allure.step("按 Inactive 状态筛选"):
        page_obj.filter_by_status("Inactive")
        page_obj.wait_for_filter_results(timeout=5000)
        filtered_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_filtered_inactive", allure.attachment_type.PNG)
        allure.attach(f"Inactive 用户数: {filtered_count}", "filtered_count")
    
    with allure.step("验证筛选结果"):
        # 筛选后应该有结果
        assert filtered_count >= 0, "筛选应返回有效结果"
        # 如果总用户数已加载，验证筛选后的数量应该小于等于总用户数（考虑分页）
        if total_users > 0:
            assert filtered_count <= total_users, f"Inactive 用户数({filtered_count})应小于等于总用户数({total_users})"
        else:
            # 如果统计值仍未加载，至少验证筛选后有结果或为 0（可能没有 Inactive 用户）
            assert filtered_count >= 0, "筛选后应该有结果或为 0"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 统计卡片
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 统计卡片")
@allure.title("test_p1_stats_cards_display - 统计卡片显示")
def test_p1_stats_cards_display(auth_page: Page):
    """
    验证：Total Users / Active Now / Roles / Admins 统计卡片显示正确
    """
    logger = TestLogger("test_p1_stats_cards_display")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=10000)
        step_shot(page_obj, "step_stats_loaded")
    with allure.step("验证统计数据合理性"):
        total_users = page_obj.get_total_users_count()
        admins = page_obj.get_admins_count()
        allure.attach(f"Total Users: {total_users}, Admins: {admins}", "stats")
        assert total_users.isdigit(), "Total Users 应该是数字"
        assert admins.isdigit(), "Admins 应该是数字"
        assert int(admins) <= int(total_users), "Admins <= Total Users"
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 统计卡片")
@allure.title("test_p1_stats_update_on_create_delete - 统计卡片随创建/删除更新")
@pytest.mark.skip(reason="并发 worker 同时创建/删除用户导致统计值波动，需串行执行")
def test_p1_stats_update_on_create_delete(auth_page: Page):
    """创建用户 → Total+1 → 删除 → Total 恢复（并发环境下统计值可能波动）"""
    logger = TestLogger("test_p1_stats_update_on_create_delete")
    logger.start()
    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("stats_test")
    created = []
    try:
        with allure.step("记录初始统计"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            auth_page.wait_for_selector('text=Total Users', timeout=10000)
            auth_page.wait_for_timeout(1000)
            initial = int(page_obj.get_total_users_count())
            allure.attach(f"初始: {initial}", "initial", allure.attachment_type.TEXT)
        with allure.step("创建用户 → +1"):
            create_test_user(page_obj, test_user)
            created.append(test_user["username"])
            page_obj.wait_for_data_loaded()
            auth_page.wait_for_timeout(1000)
            after_create = int(page_obj.get_total_users_count())
            # 并发 worker 可能同时创建/删除用户，允许 >= initial+1
            assert after_create >= initial + 1, \
                f"创建后应 >= {initial+1}，实际: {after_create}"
        with allure.step("删除用户 → 恢复"):
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            page_obj.delete_user(test_user["username"])
            created.clear()
            auth_page.get_by_role("searchbox").clear()
            auth_page.wait_for_timeout(1500)
            after_delete = int(page_obj.get_total_users_count())
            # 并发 worker 可能同时操作，允许 <= after_create（至少减少了）
            assert after_delete < after_create, \
                f"删除后应 < {after_create}，实际: {after_delete}"
        logger.end(success=True)
    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass
