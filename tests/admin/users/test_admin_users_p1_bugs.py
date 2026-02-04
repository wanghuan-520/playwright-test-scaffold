# ═══════════════════════════════════════════════════════════════
# Admin Users P1 Bug Tests
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Users 页面已知 Bug 验证

测试点：
- Bug #1: 数据异步加载显示问题
- Bug #5: HTML DOM 嵌套错误
- Bug #6: 对话框可访问性问题
"""

import pytest
import allure
from playwright.sync_api import Page, ConsoleMessage

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Users")
@allure.story("P1 - Bug 验证")
class TestAdminUsersBugs:
    """Admin Users 页面 Bug 验证测试"""
    
    @allure.title("test_p1_bug_admins_count_shows_zero - Bug#NEW: Admins 统计始终显示 0")
    @pytest.mark.xfail(reason="已知 Bug: Admins 统计卡片始终显示 0")
    def test_p1_bug_admins_count_shows_zero(self, auth_page: Page):
        """
        Bug: Admins 统计卡片始终显示 0
        
        现象：
        - 即使表格中有多个 admin 用户
        - Admins 统计卡片始终显示 "0"
        
        预期：
        - Admins 应该显示实际的 admin 用户数量
        """
        logger = TestLogger("test_p1_bug_admins_count_shows_zero")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
            step_shot(page_obj, "step_data_loaded")
        
        with allure.step("获取 Admins 统计"):
            admins_count = page_obj.get_admins_count()
            allure.attach(f"Admins 统计: {admins_count}", "admins_count")
        
        with allure.step("按 admin 角色筛选获取实际数量"):
            page_obj.filter_by_role("admin")
            auth_page.wait_for_timeout(1500)
            actual_admin_count = page_obj.get_visible_user_count()
            allure.attach(f"实际 admin 用户数: {actual_admin_count}", "actual_admin_count")
            step_shot(page_obj, "step_filtered_admin")
        
        with allure.step("验证 Admins 统计是否正确"):
            # Bug: admins_count 显示 0，但实际有 admin 用户
            if admins_count == "0" and actual_admin_count > 0:
                pytest.xfail(f"Bug 确认: Admins 统计显示 {admins_count}，但实际有 {actual_admin_count} 个 admin 用户")
        
        logger.end(success=True)
    
    @allure.title("test_p1_bug_long_text_no_truncation - Bug#NEW: 长文本没有截断")
    @pytest.mark.xfail(reason="已知 Bug: 长邮箱/用户名没有截断，导致表格布局错乱")
    def test_p1_bug_long_text_no_truncation(self, auth_page: Page):
        """
        Bug: 长邮箱/用户名没有截断
        
        现象：
        - 超长的邮箱地址（如 256 字符）没有使用 text-overflow: ellipsis
        - 文本延伸到其他列区域，破坏表格布局
        
        预期：
        - 长文本应该截断并显示省略号
        """
        logger = TestLogger("test_p1_bug_long_text_no_truncation")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=10000)
        
        with allure.step("搜索长邮箱用户"):
            page_obj.search_user("bnd_e256")  # 256 字符邮箱测试用户
            auth_page.wait_for_timeout(2000)
            step_shot(page_obj, "step_long_email_user")
        
        with allure.step("检查邮箱单元格是否有截断样式"):
            has_truncation = auth_page.evaluate("""
                () => {
                    const emailCells = document.querySelectorAll('table td:nth-child(3), table cell:nth-child(3)');
                    for (const cell of emailCells) {
                        const style = window.getComputedStyle(cell);
                        if (style.textOverflow === 'ellipsis' || style.overflow === 'hidden') {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            allure.attach(f"是否有截断样式: {has_truncation}", "truncation_check")
            if not has_truncation:
                pytest.xfail("Bug 确认: 长文本没有截断样式")
        
        logger.end(success=True)
    
    @allure.title("test_p1_bug_data_async_loading_shows_zero - Bug#1: 数据加载时显示 0")
    @pytest.mark.xfail(reason="已知 Bug: 数据异步加载时 Total Users 显示 0")
    def test_p1_bug_data_async_loading_shows_zero(self, auth_page: Page):
        """
        Bug #1: 数据异步加载显示问题
        
        现象：
        - 页面初始加载时 Total Users 显示 "0"
        - 数据异步加载完成后才显示真实数量
        - 无 loading 状态指示
        
        预期：
        - 应该有 loading 状态
        - 或者等数据加载完成后再渲染统计
        """
        logger = TestLogger("test_p1_bug_data_async_loading_shows_zero")
        logger.start()
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
        
        with allure.step("立即检查 Total Users（预期显示 0 或 loading）"):
            # 不等待数据加载，立即检查
            total_users_immediate = page_obj.get_total_users_count()
            step_shot(page_obj, "step_immediate_check")
            allure.attach(f"立即检查 Total Users: {total_users_immediate}", "即时统计")
        
        with allure.step("等待数据加载后再检查"):
            page_obj.wait_for_data_loaded(timeout=10000)
            total_users_loaded = page_obj.get_total_users_count()
            step_shot(page_obj, "step_after_loading")
            allure.attach(f"加载后 Total Users: {total_users_loaded}", "加载后统计")
        
        with allure.step("验证加载前后数据是否一致（Bug: 应该一致或有 loading）"):
            # 如果加载前是 0，加载后不是 0，说明存在 Bug
            if total_users_immediate == "0" and total_users_loaded != "0":
                pytest.xfail("Bug 确认: 数据加载时显示 0，加载后显示真实数量")
        
        logger.end(success=True)
    
    @allure.title("test_p1_bug_html_dom_nesting_errors - Bug#5: HTML DOM 嵌套错误")
    @pytest.mark.xfail(reason="已知 Bug: React 组件 DOM 结构错误")
    def test_p1_bug_html_dom_nesting_errors(self, auth_page: Page):
        """
        Bug #5: HTML DOM 嵌套错误
        
        现象：
        - 控制台报错 "In HTML, %s cannot be a descendant of <%s>"
        - React 组件 DOM 结构问题
        
        预期：
        - 控制台不应有 DOM 嵌套错误
        """
        logger = TestLogger("test_p1_bug_html_dom_nesting_errors")
        logger.start()
        
        console_errors = []
        
        def handle_console(msg: ConsoleMessage):
            if msg.type == "error" and "cannot be a descendant" in msg.text:
                console_errors.append(msg.text)
        
        auth_page.on("console", handle_console)
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("检查控制台 DOM 嵌套错误"):
            if console_errors:
                allure.attach("\n".join(console_errors), "DOM 嵌套错误")
                pytest.xfail(f"Bug 确认: 发现 {len(console_errors)} 个 DOM 嵌套错误")
        
        logger.end(success=True)
    
    @allure.title("test_p1_bug_dialog_accessibility - Bug#6: 对话框可访问性问题")
    @pytest.mark.xfail(reason="已知 Bug: Dialog 缺少 DialogTitle 和 aria-describedby")
    def test_p1_bug_dialog_accessibility(self, auth_page: Page):
        """
        Bug #6: 对话框可访问性问题
        
        现象：
        - 控制台警告 "`DialogContent` requires a `DialogTitle`"
        - 控制台警告 "Missing `Description` or `aria-describedby`"
        
        预期：
        - Dialog 应该包含 DialogTitle
        - Dialog 应该有 aria-describedby 属性
        """
        logger = TestLogger("test_p1_bug_dialog_accessibility")
        logger.start()
        
        console_warnings = []
        
        def handle_console(msg: ConsoleMessage):
            if "DialogTitle" in msg.text or "aria-describedby" in msg.text:
                console_warnings.append(msg.text)
        
        auth_page.on("console", handle_console)
        
        page_obj = AdminUsersPage(auth_page)
        
        with allure.step("导航到 Admin Users 页面"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded(timeout=5000)
        
        with allure.step("打开 Add User 对话框"):
            page_obj.click_add_user()
            auth_page.wait_for_timeout(1000)
            step_shot(page_obj, "step_dialog_opened")
        
        with allure.step("检查控制台可访问性警告"):
            if console_warnings:
                allure.attach("\n".join(console_warnings), "可访问性警告")
                pytest.xfail(f"Bug 确认: 发现 {len(console_warnings)} 个可访问性问题")
        
        with allure.step("关闭对话框"):
            page_obj.close_dialog()
        
        logger.end(success=True)

