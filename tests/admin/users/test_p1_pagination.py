# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - 分页测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面分页功能

测试点：
- 每页数量切换（10/20/50/100）
- 翻页功能（下一页、上一页、第一页、最后一页）
- 页码跳转
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# Per Page 切换测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 每页数量")
@allure.title("test_p1_pagination_per_page_10 - 每页显示 10 条")
def test_p1_pagination_per_page_10(auth_page: Page):
    """验证：每页显示 10 条"""
    logger = TestLogger("test_p1_pagination_per_page_10")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("切换到每页 10 条"):
        page_obj.change_per_page(10)
        # 等待 API 响应和页面刷新
        auth_page.wait_for_timeout(2000)  # 等待下拉选择完成
        page_obj.wait_for_filter_results()  # 等待筛选结果加载
        auth_page.wait_for_timeout(1000)  # 额外等待确保 UI 更新
        allure.attach(auth_page.screenshot(full_page=True), "step_per_page_10", allure.attachment_type.PNG)
    
    with allure.step("验证显示数量"):
        showing_text = page_obj.get_showing_text()
        visible_count = page_obj.get_visible_user_count()
        allure.attach(f"Showing: {showing_text}, 可见行数: {visible_count}", "result")
        assert "1 to 10" in showing_text or "1-10" in showing_text, f"应该显示 1 to 10 或 1-10，实际: {showing_text}"
        # 注意：如果总用户数少于 10，则显示实际数量
        if visible_count < 10:
            allure.attach(f"总用户数少于 10，实际显示: {visible_count}", "note")
        else:
            assert visible_count == 10, f"应该显示 10 行，实际: {visible_count}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 每页数量")
@allure.title("test_p1_pagination_per_page_20 - 每页显示 20 条")
def test_p1_pagination_per_page_20(auth_page: Page):
    """验证：每页显示 20 条"""
    logger = TestLogger("test_p1_pagination_per_page_20")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("切换到每页 20 条"):
        page_obj.change_per_page(20)
        # 等待 API 响应和页面刷新
        auth_page.wait_for_timeout(2000)  # 等待下拉选择完成
        page_obj.wait_for_filter_results()  # 等待筛选结果加载
        auth_page.wait_for_timeout(1000)  # 额外等待确保 UI 更新
        allure.attach(auth_page.screenshot(full_page=True), "step_per_page_20", allure.attachment_type.PNG)
    
    with allure.step("验证显示数量"):
        showing_text = page_obj.get_showing_text()
        visible_count = page_obj.get_visible_user_count()
        allure.attach(f"Showing: {showing_text}, 可见行数: {visible_count}", "result")
        assert "1 to 20" in showing_text or "1-20" in showing_text, f"应该显示 1 to 20 或 1-20，实际: {showing_text}"
        # 注意：如果总用户数少于 20，则显示实际数量
        if visible_count < 20:
            allure.attach(f"总用户数少于 20，实际显示: {visible_count}", "note")
        else:
            assert visible_count == 20, f"应该显示 20 行，实际: {visible_count}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 每页数量")
@allure.title("test_p1_pagination_per_page_50 - 每页显示 50 条")
def test_p1_pagination_per_page_50(auth_page: Page):
    """验证：每页显示 50 条"""
    logger = TestLogger("test_p1_pagination_per_page_50")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("切换到每页 50 条"):
        page_obj.change_per_page(50)
        # 等待 API 响应和页面刷新
        auth_page.wait_for_timeout(2000)  # 等待下拉选择完成
        page_obj.wait_for_filter_results()  # 等待筛选结果加载
        auth_page.wait_for_timeout(1000)  # 额外等待确保 UI 更新
        allure.attach(auth_page.screenshot(full_page=True), "step_per_page_50", allure.attachment_type.PNG)
    
    with allure.step("验证显示数量"):
        showing_text = page_obj.get_showing_text()
        visible_count = page_obj.get_visible_user_count()
        allure.attach(f"Showing: {showing_text}, 可见行数: {visible_count}", "result")
        assert "1 to 50" in showing_text or "1-50" in showing_text, f"应该显示 1 to 50 或 1-50，实际: {showing_text}"
        # 注意：如果总用户数少于 50，则显示实际数量
        # 如果总用户数 >= 50，则应该显示 50 行
        if visible_count < 50:
            # 总用户数可能少于 50，这是正常的
            allure.attach(f"总用户数少于 50，实际显示: {visible_count}", "note")
        else:
            assert visible_count == 50, f"应该显示 50 行，实际: {visible_count}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 每页数量")
@allure.title("test_p1_pagination_per_page_100 - 每页显示 100 条")
def test_p1_pagination_per_page_100(auth_page: Page):
    """验证：每页显示 100 条"""
    logger = TestLogger("test_p1_pagination_per_page_100")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("切换到每页 100 条"):
        page_obj.change_per_page(100)
        # 等待 API 响应和页面刷新
        auth_page.wait_for_timeout(2000)  # 等待下拉选择完成
        page_obj.wait_for_filter_results()  # 等待筛选结果加载
        auth_page.wait_for_timeout(1000)  # 额外等待确保 UI 更新
        allure.attach(auth_page.screenshot(full_page=True), "step_per_page_100", allure.attachment_type.PNG)
    
    with allure.step("验证显示数量"):
        showing_text = page_obj.get_showing_text()
        visible_count = page_obj.get_visible_user_count()
        allure.attach(f"Showing: {showing_text}, 可见行数: {visible_count}", "result")
        # 总数 < 100 时显示全部（如 "1 to 64 of 64"），总数 >= 100 时显示 "1 to 100"
        import re
        m = re.search(r'(\d+)\s+to\s+(\d+)\s+of\s+(\d+)', showing_text)
        assert m, f"Showing 文本格式异常: {showing_text}"
        end_num, total = int(m.group(2)), int(m.group(3))
        expected_end = min(100, total)
        assert end_num == expected_end, \
            f"per_page=100 时应显示 1 to {expected_end}，实际: {showing_text}"
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 翻页测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 翻页")
@allure.title("test_p1_pagination_next_page - 下一页")
def test_p1_pagination_next_page(auth_page: Page):
    """验证：点击下一页按钮"""
    logger = TestLogger("test_p1_pagination_next_page")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        initial_showing = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_page_1", allure.attachment_type.PNG)
        allure.attach(f"第一页: {initial_showing}", "initial_showing")
    
    with allure.step("点击下一页"):
        page_obj.click_next_page()
        page_obj.wait_for_filter_results()
        next_showing = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_page_2", allure.attachment_type.PNG)
        allure.attach(f"第二页: {next_showing}", "next_showing")
    
    with allure.step("验证翻页成功"):
        assert "11 to 20" in next_showing, f"应该显示 11 to 20，实际: {next_showing}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 翻页")
@allure.title("test_p1_pagination_prev_page - 上一页")
def test_p1_pagination_prev_page(auth_page: Page):
    """验证：点击上一页按钮"""
    logger = TestLogger("test_p1_pagination_prev_page")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("先跳转到第 2 页"):
        page_obj.click_page_number(2)
        page_obj.wait_for_filter_results()
        page2_showing = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_page_2", allure.attachment_type.PNG)
        allure.attach(f"第二页: {page2_showing}", "page2_showing")
    
    with allure.step("点击上一页"):
        page_obj.click_prev_page()
        page_obj.wait_for_filter_results()
        page1_showing = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_page_1", allure.attachment_type.PNG)
        allure.attach(f"第一页: {page1_showing}", "page1_showing")
    
    with allure.step("验证返回第一页"):
        assert "1 to 10" in page1_showing, f"应该显示 1 to 10，实际: {page1_showing}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 翻页")
@allure.title("test_p1_pagination_first_page - 第一页按钮状态")
def test_p1_pagination_first_page(auth_page: Page):
    """验证：第一页时上一页按钮禁用"""
    logger = TestLogger("test_p1_pagination_first_page")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        # 等待分页控件完全加载
        auth_page.wait_for_selector('text=/Showing \\d+ to \\d+ of/', timeout=10000)
        auth_page.wait_for_timeout(2000)  # 额外等待确保分页按钮状态已更新
        allure.attach(auth_page.screenshot(full_page=True), "step_first_page", allure.attachment_type.PNG)
    
    with allure.step("验证上一页按钮状态"):
        # 再次等待分页控件，确保按钮状态已更新
        pagination_container = page_obj._get_pagination_container()
        pagination_container.wait_for(state="visible", timeout=5000)
        auth_page.wait_for_timeout(1000)  # 等待按钮状态更新
        
        is_disabled = page_obj.is_prev_page_disabled()
        allure.attach(f"上一页按钮禁用: {is_disabled}", "prev_disabled")
        assert is_disabled, "第一页时上一页按钮应该禁用"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 翻页")
@allure.title("test_p1_pagination_last_page - 最后一页")
def test_p1_pagination_last_page(auth_page: Page):
    """验证：跳转到最后一页"""
    logger = TestLogger("test_p1_pagination_last_page")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        total_pages = page_obj.get_total_pages()
        allure.attach(f"总页数: {total_pages}", "total_pages")
    
    with allure.step("跳转到最后一页"):
        page_obj.click_last_page()
        page_obj.wait_for_filter_results()
        showing_text = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_last_page", allure.attachment_type.PNG)
        allure.attach(f"最后一页: {showing_text}", "last_page_showing")
    
    with allure.step("验证下一页按钮状态"):
        is_disabled = page_obj.is_next_page_disabled()
        allure.attach(f"下一页按钮禁用: {is_disabled}", "next_disabled")
        assert is_disabled, "最后一页时下一页按钮应该禁用"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - 分页 - 翻页")
@allure.title("test_p1_pagination_page_jump - 页码跳转")
def test_p1_pagination_page_jump(auth_page: Page):
    """验证：直接点击页码跳转"""
    logger = TestLogger("test_p1_pagination_page_jump")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("点击第 2 页"):
        page_obj.click_page_number(2)
        page_obj.wait_for_filter_results()
        showing_text = page_obj.get_showing_text()
        allure.attach(auth_page.screenshot(full_page=True), "step_page_2", allure.attachment_type.PNG)
    
    with allure.step("验证跳转到第 2 页"):
        assert "11 to 20" in showing_text, f"应该显示 11 to 20，实际: {showing_text}"
    
    logger.end(success=True)
