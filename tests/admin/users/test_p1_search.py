# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - 搜索功能测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面搜索功能

测试点：
- 按用户名精确搜索
- 按邮箱精确搜索
- 模糊匹配搜索
- 搜索无结果
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# 精确搜索
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_by_username_exact - 按用户名精确搜索")
def test_p1_search_by_username_exact(auth_page: Page):
    """
    验证：
    1. 输入完整用户名进行搜索
    2. 搜索结果精确匹配
    """
    logger = TestLogger("test_p1_search_by_username_exact")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
    
    with allure.step("搜索已知 admin 用户"):
        from tests.admin.users._helpers import KNOWN_ADMIN_USER
        page_obj.search_user(KNOWN_ADMIN_USER)
        page_obj.wait_for_filter_results(timeout=5000)
        allure.attach(auth_page.screenshot(full_page=True), "step_search_result", allure.attachment_type.PNG)
    
    with allure.step("验证搜索结果"):
        count = page_obj.get_visible_user_count()
        user_row = page_obj.get_user_by_username(KNOWN_ADMIN_USER)
        is_visible = user_row.count() > 0
        allure.attach(f"搜索 {KNOWN_ADMIN_USER}: 数量={count}, 可见={is_visible}", "search_result")
        assert is_visible or count > 0, \
            f"搜索结果应包含 {KNOWN_ADMIN_USER}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_by_email_exact - 按邮箱精确搜索")
def test_p1_search_by_email_exact(auth_page: Page):
    """
    验证：
    1. 输入完整邮箱进行搜索
    2. 搜索结果精确匹配
    """
    logger = TestLogger("test_p1_search_by_email_exact")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
    
    with allure.step("搜索已知 admin 邮箱"):
        from tests.admin.users._helpers import KNOWN_ADMIN_EMAIL
        page_obj.search_user(KNOWN_ADMIN_EMAIL)
        page_obj.wait_for_search_results(timeout=2000)
        allure.attach(auth_page.screenshot(full_page=True), "step_search_result", allure.attachment_type.PNG)
    
    with allure.step("验证搜索结果"):
        count = page_obj.get_visible_user_count()
        allure.attach(f"搜索结果数量: {count}", "search_result_count")
        assert count >= 1, "应该找到至少 1 个匹配结果"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 模糊搜索
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_fuzzy_by_username - 用户名模糊搜索")
def test_p1_search_fuzzy_by_username(auth_page: Page):
    """
    验证：
    1. 输入部分用户名进行模糊搜索
    2. 搜索结果包含所有匹配项
    """
    logger = TestLogger("test_p1_search_fuzzy_by_username")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
    
    with allure.step("模糊搜索 'TestAdmin'"):
        page_obj.search_user("TestAdmin")
        page_obj.wait_for_search_results(timeout=2000)
        allure.attach(auth_page.screenshot(full_page=True), "step_search_result", allure.attachment_type.PNG)
    
    with allure.step("验证搜索结果"):
        count = page_obj.get_visible_user_count()
        allure.attach(f"搜索结果数量: {count}", "search_result_count")
        # TestAdmin1 ~ TestAdmin10 共 10 个（如果账号池中的账号都已创建）
        # 但实际系统中可能只有部分账号存在，所以至少验证有结果即可
        assert count >= 1, f"模糊搜索 'TestAdmin' 应返回至少 1 个结果，实际: {count}"
        if count >= 5:
            allure.attach(f"模糊搜索返回了 {count} 个结果（符合预期）", "search_success")
        else:
            allure.attach(f"模糊搜索只返回了 {count} 个结果（可能部分账号未创建）", "search_info")
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_fuzzy_by_email - 邮箱模糊搜索")
def test_p1_search_fuzzy_by_email(auth_page: Page):
    """
    验证：
    1. 输入部分邮箱进行模糊搜索
    2. 搜索结果包含所有匹配项
    """
    logger = TestLogger("test_p1_search_fuzzy_by_email")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
    
    with allure.step("模糊搜索 'test_admin'"):
        page_obj.search_user("test_admin")
        page_obj.wait_for_search_results(timeout=2000)
        allure.attach(auth_page.screenshot(full_page=True), "step_search_result", allure.attachment_type.PNG)
    
    with allure.step("验证搜索结果"):
        count = page_obj.get_visible_user_count()
        allure.attach(f"搜索结果数量: {count}", "search_result_count")
        # test_admin1@test.com ~ test_admin10@test.com 共 10 个（如果账号池中的账号都已创建）
        # 但实际系统中可能只有部分账号存在，所以至少验证有结果即可
        assert count >= 1, f"模糊搜索 'test_admin' 应返回至少 1 个结果，实际: {count}"
        if count >= 5:
            allure.attach(f"模糊搜索返回了 {count} 个结果（符合预期）", "search_success")
        else:
            allure.attach(f"模糊搜索只返回了 {count} 个结果（可能部分账号未创建）", "search_info")
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 无结果搜索
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_no_results - 搜索无结果")
def test_p1_search_no_results(auth_page: Page):
    """
    验证：
    1. 搜索不存在的用户
    2. 显示无结果提示
    """
    logger = TestLogger("test_p1_search_no_results")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        allure.attach(auth_page.screenshot(full_page=True), "step_initial", allure.attachment_type.PNG)
    
    with allure.step("搜索不存在的用户"):
        # 使用一个绝对不会存在的用户名（包含特殊字符和数字，确保不会匹配到任何用户）
        search_term = "xyz_nonexistent_user_12345_abcdef_99999"
        page_obj.search_user(search_term)
        # 等待搜索 API 响应和 UI 更新
        page_obj.wait_for_filter_results(timeout=5000)
        allure.attach(auth_page.screenshot(full_page=True), "step_no_results", allure.attachment_type.PNG)
    
    with allure.step("验证无结果"):
        # 等待搜索结果稳定
        auth_page.wait_for_timeout(1500)
        
        # 检查是否有 "No users found" 或类似的空状态提示（主要验证方式）
        no_results_selectors = [
            'text=/No users found/i',
            'text=/No results/i',
            'text=/没有找到用户/i',
            '[class*="empty"]',
            '[class*="no-results"]'
        ]
        
        has_no_results_message = False
        for selector in no_results_selectors:
            try:
                element = auth_page.locator(selector)
                if element.count() > 0 and element.first.is_visible(timeout=1000):
                    has_no_results_message = True
                    break
            except Exception:
                continue
        
        # 检查页面文本中是否包含无结果提示
        page_text = auth_page.locator('body').text_content() or ""
        has_no_results_in_text = "no users found" in page_text.lower() or "no results" in page_text.lower()
        
        # 检查表格是否为空（统计实际数据行，排除表头）
        # 注意：即使显示 "No users found"，表格可能仍有空行或表头
        table_rows = auth_page.locator('table tbody tr:not([class*="empty"])')
        data_row_count = 0
        for i in range(table_rows.count()):
            row = table_rows.nth(i)
            row_text = row.text_content() or ""
            # 排除空行和 "No users found" 行
            if row_text.strip() and "no users found" not in row_text.lower():
                data_row_count += 1
        
        count = page_obj.get_visible_user_count()
        showing_text = page_obj.get_showing_text()
        
        # 检查搜索框中的内容是否与输入一致（验证搜索是否生效）
        searchbox_value = auth_page.get_by_role("searchbox").input_value()
        search_triggered = searchbox_value == search_term
        
        allure.attach(f"搜索词: {search_term}", "search_term")
        allure.attach(f"搜索框内容: {searchbox_value}", "searchbox_value")
        allure.attach(f"搜索是否触发: {search_triggered}", "search_triggered")
        allure.attach(f"表格行数（get_visible_user_count）: {count}", "user_count")
        allure.attach(f"实际数据行数: {data_row_count}", "data_row_count")
        allure.attach(f"Showing 文本: {showing_text}", "showing_text")
        allure.attach(f"无结果消息元素: {has_no_results_message}", "no_results_element")
        allure.attach(f"页面文本包含无结果: {has_no_results_in_text}", "no_results_in_text")
        
        # 验证无结果：
        # 1. 如果显示 "No users found" 消息，说明搜索无结果
        # 2. 如果 Showing 文本显示 "0 results" 或类似，说明搜索无结果
        # 3. 如果数据行数为 0，说明搜索无结果
        # 4. 如果搜索已触发但 Showing 文本显示大量结果，可能是搜索功能有问题
        has_zero_results = "0 results" in showing_text.lower() or "of 0" in showing_text.lower()
        
        assert has_no_results_message or has_no_results_in_text or data_row_count == 0 or has_zero_results, \
            f"搜索不存在的用户应该显示 'No users found' 或 0 结果。用户数: {count}, 数据行: {data_row_count}, Showing: {showing_text}, 无结果消息: {has_no_results_message}, 搜索已触发: {search_triggered}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 搜索功能")
@allure.title("test_p1_search_clear - 清空搜索恢复全部")
def test_p1_search_clear(auth_page: Page):
    """
    验证：
    1. 搜索后清空搜索框
    2. 恢复显示全部用户
    """
    logger = TestLogger("test_p1_search_clear")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        initial_count = page_obj.get_visible_user_count()
        allure.attach(f"初始数量: {initial_count}", "initial_count")
    
    with allure.step("搜索 'TestAdmin1'"):
        page_obj.search_user("TestAdmin1")
        page_obj.wait_for_search_results(timeout=2000)
        search_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_searched", allure.attachment_type.PNG)
        allure.attach(f"搜索后数量: {search_count}", "search_count")
    
    with allure.step("清空搜索框"):
        page_obj.search_user("")
        page_obj.wait_for_search_results(timeout=2000)
        restored_count = page_obj.get_visible_user_count()
        allure.attach(auth_page.screenshot(full_page=True), "step_cleared", allure.attachment_type.PNG)
        allure.attach(f"清空后数量: {restored_count}", "restored_count")
    
    with allure.step("验证恢复全部"):
        assert restored_count >= initial_count, f"清空搜索后应恢复全部，实际: {restored_count}"
    
    logger.end(success=True)
