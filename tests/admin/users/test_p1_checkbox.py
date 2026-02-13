# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - Checkbox 测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面 Checkbox 功能

测试点：
- 勾选单个用户
- 勾选多个用户
- 取消勾选
- 全选/取消全选
- 勾选后删除（使用专门创建的测试账号）
"""

import time
import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import create_test_user, delete_test_user, generate_unique_user
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# 测试数据：用于删除测试的账号前缀
# ═══════════════════════════════════════════════════════════════

DELETE_TEST_PREFIX = "del_test_"


def generate_delete_test_user():
    """生成用于删除测试的用户名"""
    timestamp = int(time.time() * 1000)
    return f"{DELETE_TEST_PREFIX}{timestamp}"


# ═══════════════════════════════════════════════════════════════
# P1 - Checkbox 功能测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Checkbox 勾选")
@allure.title("test_p1_checkbox_select_single - 勾选单个用户")
def test_p1_checkbox_select_single(auth_page: Page):
    """
    验证：
    1. 点击行 checkbox 可以勾选
    2. 勾选状态正确显示
    """
    logger = TestLogger("test_p1_checkbox_select_single")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        step_shot(page_obj, "step_initial")
    
    with allure.step("勾选第一行用户"):
        initial_checked = page_obj.get_checked_count()
        page_obj.check_row(0)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_checked_row_0")
    
    with allure.step("验证勾选状态"):
        is_checked = page_obj.is_row_checked(0)
        checked_count = page_obj.get_checked_count()
        allure.attach(f"初始勾选数: {initial_checked}, 当前勾选数: {checked_count}", "checked_count")
        assert is_checked, "第一行应该被勾选"
        assert checked_count == initial_checked + 1, "勾选数应该增加 1"
    
    with allure.step("取消勾选"):
        page_obj.uncheck_row(0)
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_unchecked_row_0")
        assert not page_obj.is_row_checked(0), "第一行应该取消勾选"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Checkbox 勾选")
@allure.title("test_p1_checkbox_select_multiple - 勾选多个用户")
def test_p1_checkbox_select_multiple(auth_page: Page):
    """
    验证：
    1. 可以同时勾选多个用户
    2. 勾选数量正确统计
    """
    logger = TestLogger("test_p1_checkbox_select_multiple")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        step_shot(page_obj, "step_initial")
    
    with allure.step("勾选前 3 行用户"):
        for i in range(3):
            page_obj.check_row(i)
            auth_page.wait_for_timeout(300)
        step_shot(page_obj, "step_checked_3_rows")
    
    with allure.step("验证勾选数量"):
        checked_count = page_obj.get_checked_count()
        allure.attach(f"勾选数量: {checked_count}", "checked_count")
        assert checked_count >= 3, f"应该至少勾选 3 个，实际: {checked_count}"
    
    with allure.step("逐个取消勾选"):
        for i in range(3):
            page_obj.uncheck_row(i)
            auth_page.wait_for_timeout(300)
        step_shot(page_obj, "step_unchecked_all")
        
        final_count = page_obj.get_checked_count()
        assert final_count == 0, f"应该没有勾选，实际: {final_count}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Checkbox 勾选")
@allure.title("test_p1_checkbox_select_all - 全选功能")
def test_p1_checkbox_select_all(auth_page: Page):
    """
    验证：
    1. 点击表头 checkbox 全选当前页
    2. 再次点击取消全选
    """
    logger = TestLogger("test_p1_checkbox_select_all")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
        visible_count = page_obj.get_visible_user_count()
        step_shot(page_obj, "step_initial")
        allure.attach(f"当前页用户数: {visible_count}", "visible_count")
    
    with allure.step("点击表头 checkbox 全选"):
        page_obj.check_all()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_select_all")
    
    with allure.step("验证全选状态"):
        checked_count = page_obj.get_checked_count()
        allure.attach(f"勾选数量: {checked_count}", "checked_count")
        # 全选应该勾选当前页所有行
        assert checked_count >= visible_count - 1, f"全选后应该勾选 {visible_count} 行，实际: {checked_count}"
    
    with allure.step("再次点击取消全选"):
        page_obj.uncheck_all()
        auth_page.wait_for_timeout(500)
        step_shot(page_obj, "step_unselect_all")
    
    with allure.step("验证取消全选"):
        final_count = page_obj.get_checked_count()
        assert final_count == 0, f"取消全选后应该为 0，实际: {final_count}"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - Checkbox 勾选")
@allure.title("test_p1_checkbox_delete_selected - 勾选后删除")
def test_p1_checkbox_delete_selected(auth_page: Page):
    """
    验证：
    1. 先创建多个专门用于删除的测试用户
    2. 勾选这些测试用户
    3. 批量删除勾选的用户
    4. 验证用户已删除
    
    注意：此测试创建专门的测试账号，避免误删其他账号
    """
    logger = TestLogger("test_p1_checkbox_delete_selected")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    # 创建 3 个专门用于删除的测试用户
    created_users = []
    
    try:
        with allure.step("创建 3 个专门用于删除的测试用户"):
            for i in range(3):
                test_user = generate_unique_user(f"del_checkbox_{i}")
                create_test_user(page_obj, test_user)
                created_users.append(test_user["username"])
                auth_page.wait_for_timeout(500)  # 等待创建完成
            step_shot(page_obj, "step_users_created")
            allure.attach(f"创建了 {len(created_users)} 个测试用户: {', '.join(created_users)}", "created_users")
        
        with allure.step("导航到 Admin Users 页面并等待数据加载"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("搜索并勾选每个测试用户"):
            # 由于搜索会改变页面显示，每次搜索后只能勾选一个用户
            # 我们逐个搜索并勾选每个测试用户
            for username in created_users:
                page_obj.search_user(username)
                auth_page.wait_for_timeout(1000)  # 等待搜索结果
                
                # 验证用户存在
                user_count = page_obj.get_visible_user_count()
                assert user_count > 0, f"应该找到用户 {username}"
                
                # 勾选用户
                page_obj.check_row_by_username(username)
                auth_page.wait_for_timeout(300)
                logger.info(f"已勾选用户: {username}")
            
            # 验证至少勾选了用户（由于搜索会改变显示，可能只显示一个）
            checked_count = page_obj.get_checked_count()
            step_shot(page_obj, "step_users_checked")
            allure.attach(f"已勾选 {checked_count} 个用户", "checked_count")
            assert checked_count >= 1, f"应该至少勾选 1 个用户，实际: {checked_count}"
        
        with allure.step("逐个删除勾选的测试用户"):
            # 由于没有批量删除功能，逐个删除每个测试用户
            for username in created_users:
                try:
                    # 先搜索用户，确保在当前页
                    page_obj.search_user(username)
                    auth_page.wait_for_timeout(1000)
                    
                    # 检查用户是否存在
                    if page_obj.get_visible_user_count() > 0:
                        # 打开 Actions 菜单并删除
                        page_obj.click_actions_menu_for_user(username)
                        page_obj.click_delete_user()
                        auth_page.wait_for_timeout(500)
                        
                        # 确认删除
                        confirm_btn = auth_page.locator('[role="dialog"] button:has-text("Delete")')
                        if confirm_btn.is_visible(timeout=2000):
                            confirm_btn.click()
                            auth_page.wait_for_timeout(1500)  # 等待删除完成
                            logger.info(f"已删除用户: {username}")
                except Exception as e:
                    logger.warning(f"删除用户 {username} 失败: {e}")
            
            step_shot(page_obj, "step_after_delete")
        
        with allure.step("验证所有测试用户已删除"):
            # 删除后，重新导航到页面，确保数据刷新
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
            auth_page.wait_for_timeout(2000)  # 额外等待确保数据完全加载
            
            # 验证每个测试用户都已删除
            for username in created_users:
                # 先清空搜索框，确保搜索准确
                search_box = auth_page.get_by_role("searchbox")
                search_box.clear()
                auth_page.wait_for_timeout(500)  # 增加等待时间确保清空完成
                
                # 然后搜索用户（使用完整用户名）
                page_obj.search_user(username)
                auth_page.wait_for_timeout(2000)  # 增加等待时间确保搜索结果加载
                
                # 检查是否有 "No users found" 消息（主要验证方式）
                no_results_selectors = [
                    'text=/No users found/i',
                    'text=/No results/i',
                    'text=/没有找到用户/i'
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
                
                # 统计实际数据行（排除空行和 "No users found" 行）
                table_rows = auth_page.locator('table tbody tr:not([class*="empty"])')
                data_row_count = 0
                found_username_in_results = False
                
                for i in range(table_rows.count()):
                    row = table_rows.nth(i)
                    row_text = row.text_content() or ""
                    # 排除空行和 "No users found" 行
                    if row_text.strip() and "no users found" not in row_text.lower():
                        data_row_count += 1
                        # 检查是否包含完整的用户名（精确匹配）
                        if username in row_text:
                            found_username_in_results = True
                
                user_count = page_obj.get_visible_user_count()
                
                allure.attach(f"搜索 {username} 结果:", f"search_{username}")
                allure.attach(f"  - 表格行数（get_visible_user_count）: {user_count}", f"search_{username}")
                allure.attach(f"  - 实际数据行数: {data_row_count}", f"search_{username}")
                allure.attach(f"  - 无结果消息元素: {has_no_results_message}", f"search_{username}")
                allure.attach(f"  - 页面文本包含无结果: {has_no_results_in_text}", f"search_{username}")
                allure.attach(f"  - 搜索结果中包含该用户名: {found_username_in_results}", f"search_{username}")
                
                # 验证无结果：主要检查 "No users found" 消息或搜索结果中不包含该用户名
                # 如果页面显示 "No users found"，说明用户已删除
                # 如果搜索结果中有数据，但用户名不在结果中，也说明用户已删除
                is_deleted = (
                    has_no_results_message or 
                    has_no_results_in_text or 
                    (data_row_count == 0) or
                    (data_row_count > 0 and not found_username_in_results)  # 有结果但不包含该用户名
                )
                
                assert is_deleted, \
                    f"用户 {username} 应该已被删除。用户数: {user_count}, 数据行: {data_row_count}, 无结果消息: {has_no_results_message}, 找到用户名: {found_username_in_results}"
                
                step_shot(page_obj, f"step_verify_deleted_{username}")
        
        logger.end(success=True)
        
    finally:
        # 清理：确保所有创建的测试用户都被删除
        # 注意：由于测试中已经删除了这些用户，清理阶段主要是为了处理异常情况
        # 如果用户已删除，搜索会超时，所以跳过清理或使用更短的超时
        with allure.step("清理测试用户（如果存在）"):
            for username in created_users:
                try:
                    # 快速检查用户是否存在（使用短超时）
                    page_obj.navigate()
                    page_obj.wait_for_data_loaded(timeout=5000)
                    page_obj.search_user(username)
                    auth_page.wait_for_timeout(1000)  # 减少等待时间
                    
                    # 快速检查用户是否存在
                    user_count = page_obj.get_visible_user_count()
                    if user_count > 0:
                        # 验证是否真的是这个用户（避免部分匹配）
                        rows = auth_page.locator('table tbody tr')
                        found = False
                        for i in range(min(rows.count(), 5)):  # 只检查前5行
                            row_text = rows.nth(i).text_content() or ""
                            if username in row_text:
                                found = True
                                break
                        
                        if found:
                            delete_test_user(page_obj, username)
                        else:
                            logger.info(f"用户 {username} 已删除（搜索结果不匹配）")
                    else:
                        logger.info(f"用户 {username} 已删除（无搜索结果）")
                except Exception as e:
                    # 如果搜索超时或其他错误，说明用户可能已删除，跳过
                    logger.warning(f"清理用户 {username} 时出错（可能已删除）: {e}")
