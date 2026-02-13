# ═══════════════════════════════════════════════════════════════
# Admin Users P1 - View Details 页面 Bug 测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：View Details 对话框已知问题

Bug 清单：
1. 用户名未显示
2. 头像/Avatar 显示为空
3. Account Information 缺少 Username 字段
4. 缺少 First Name / Last Name 显示
5. View Details 与 Edit User 信息不一致
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_users_page import AdminUsersPage
from tests.myaccount._helpers import step_shot
from tests.admin.users._helpers import generate_unique_user, create_test_user, delete_test_user
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# Bug #1: 用户名未显示
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_details_username_displayed - 用户名显示验证")
def test_p1_view_details_username_displayed(auth_page: Page):
    """
    验证：View Details 对话框应显示用户名
    
    期望：对话框显示用户名和邮箱
    """
    logger = TestLogger("test_p1_bug_username_not_displayed")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("获取第一行用户的用户名"):
        rows = auth_page.locator('table tbody tr')
        first_row = rows.first
        # 获取用户名（通常在第二列）
        username_cell = first_row.locator('td').nth(1)
        expected_username = username_cell.text_content() or ""
        expected_username = expected_username.strip()
        allure.attach(f"期望用户名: {expected_username}", "expected_username")
    
    with allure.step("打开 View Details 对话框"):
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(1000)
        allure.attach(auth_page.screenshot(full_page=True), "step_view_details_dialog", allure.attachment_type.PNG)
    
    with allure.step("验证用户名是否显示"):
        dialog = auth_page.locator('[role="dialog"]')
        dialog_text = dialog.text_content() or ""
        
        # 检查用户名是否在对话框中显示
        # 用户名应该单独显示，不仅仅是邮箱的一部分
        has_username_displayed = expected_username in dialog_text
        
        allure.attach(f"对话框文本: {dialog_text[:500]}", "dialog_text")
        allure.attach(f"用户名显示: {has_username_displayed}", "username_check")
        
        # 期望：用户名应该单独显示在对话框中
        assert has_username_displayed, f"Bug: 用户名 '{expected_username}' 未在 View Details 中显示"
    
    with allure.step("关闭对话框"):
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# 头像/Avatar 显示验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_bug_avatar_empty - 头像显示验证")
def test_p1_bug_avatar_empty(auth_page: Page):
    """
    验证：View Details 对话框头像区域正常显示
    
    期望：应显示用户头像或默认的用户名首字母（如 "T"）
    注意：Bug 已修复，现在作为正常功能验证
    """
    logger = TestLogger("test_p1_bug_avatar_empty")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("搜索有头像的用户 haylee@test.com"):
        page_obj.search_user("haylee@test.com")
        page_obj.wait_for_filter_results(timeout=5000)
        auth_page.wait_for_timeout(1000)

        user_row = page_obj.get_user_by_username("haylee")
        if user_row.count() == 0:
            # fallback: 按邮箱在表格行中查找
            rows = auth_page.locator('table tbody tr')
            for i in range(rows.count()):
                if "haylee" in (rows.nth(i).text_content() or "").lower():
                    user_row = rows.nth(i)
                    break
        if not hasattr(user_row, 'count') or (hasattr(user_row, 'count') and user_row.count() == 0):
            pytest.skip("未找到 haylee@test.com 用户")

        step_shot(page_obj, "step_user_found")
    
    with allure.step("打开 View Details 对话框"):
        # 直接点击行内 Actions 按钮（避免用户名匹配问题）
        if hasattr(user_row, 'locator'):
            user_row.locator('button').last.click()
        else:
            user_row.first.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(1500)
        step_shot(page_obj, "step_view_details_dialog", full_page=True)
    
    with allure.step("验证头像区域存在"):
        dialog = auth_page.locator('[role="dialog"]')
        dialog_html = dialog.inner_html() or ""
        dialog_text = dialog.text_content() or ""

        # 头像可能是：img 标签、首字母圆形（class 含 avatar）、或 svg 图标
        has_img = '<img' in dialog_html.lower()
        has_avatar_class = 'avatar' in dialog_html.lower()
        # 首字母头像：显示 "T"（TestAdmin1 的首字母）
        has_initial = bool(dialog.locator('text=/^[A-Z]$/').count() > 0)

        allure.attach(
            f"有 img 标签: {has_img}\n"
            f"有 avatar class: {has_avatar_class}\n"
            f"有首字母: {has_initial}",
            "avatar_check", allure.attachment_type.TEXT,
        )
        assert has_img or has_avatar_class or has_initial, \
            "头像区域应显示头像图片或首字母"
    
    with allure.step("关闭对话框"):
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Bug #3: Account Information 缺少 Username 字段
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_details_account_info_fields - Account Information 字段验证")
def test_p1_view_details_account_info_fields(auth_page: Page):
    """
    验证：Account Information 包含完整字段
    
    期望字段：Phone Number、Created At、Last Login、Two-Factor Auth
    """
    logger = TestLogger("test_p1_bug_missing_username_field")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("打开 View Details 对话框"):
        rows = auth_page.locator('table tbody tr')
        first_row = rows.first
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(1000)
        allure.attach(auth_page.screenshot(full_page=True), "step_view_details_dialog", allure.attachment_type.PNG)
    
    with allure.step("验证 Account Information 字段"):
        dialog = auth_page.locator('[role="dialog"]')
        dialog_text = dialog.text_content() or ""
        
        # 检查现有字段
        has_phone = "Phone Number" in dialog_text
        has_created = "Created At" in dialog_text
        has_login = "Last Login" in dialog_text
        has_2fa = "Two-Factor Auth" in dialog_text
        
        # 检查是否有 Username 字段
        has_username_field = "Username" in dialog_text
        
        allure.attach(f"Phone Number: {has_phone}", "field_check")
        allure.attach(f"Created At: {has_created}", "field_check")
        allure.attach(f"Last Login: {has_login}", "field_check")
        allure.attach(f"Two-Factor Auth: {has_2fa}", "field_check")
        allure.attach(f"Username: {has_username_field}", "field_check")
        
        # 期望：应该有 Username 字段
        assert has_username_field, "Bug: Account Information 缺少 Username 字段"
    
    with allure.step("关闭对话框"):
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Bug #4: 缺少 First Name / Last Name 显示
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P2
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_details_name_fields - 姓名字段验证")
def test_p1_view_details_name_fields(auth_page: Page):
    """
    验证：View Details 显示姓名相关字段
    
    期望：如果用户有设置姓名，应该在详情中显示
    """
    logger = TestLogger("test_p1_bug_missing_name_fields")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("打开 View Details 对话框"):
        rows = auth_page.locator('table tbody tr')
        first_row = rows.first
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(1000)
        allure.attach(auth_page.screenshot(full_page=True), "step_view_details_dialog", allure.attachment_type.PNG)
    
    with allure.step("验证姓名字段是否显示"):
        dialog = auth_page.locator('[role="dialog"]')
        dialog_text = dialog.text_content() or ""
        
        # 检查是否有 First Name / Last Name 或 Name 字段
        has_first_name = "First Name" in dialog_text
        has_last_name = "Last Name" in dialog_text
        has_name = "Name" in dialog_text and "Username" not in dialog_text
        
        allure.attach(f"First Name: {has_first_name}", "field_check")
        allure.attach(f"Last Name: {has_last_name}", "field_check")
        allure.attach(f"Name: {has_name}", "field_check")
        
        # 期望：应该有姓名相关字段
        assert has_first_name or has_last_name or has_name, \
            "Bug: View Details 缺少 First Name / Last Name 字段"
    
    with allure.step("关闭对话框"):
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Bug #5: View Details 与 Edit User 信息不一致
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_edit_consistency - View Details 与 Edit User 一致性验证")
def test_p1_view_edit_consistency(auth_page: Page):
    """
    验证：View Details 与 Edit User 显示的信息一致
    
    期望：两个对话框应该显示一致的用户信息
    """
    logger = TestLogger("test_p1_bug_view_edit_inconsistency")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    # 收集 View Details 字段
    with allure.step("打开 View Details 对话框并收集字段"):
        rows = auth_page.locator('table tbody tr')
        first_row = rows.first
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(1000)
        
        dialog = auth_page.locator('[role="dialog"]')
        view_details_text = dialog.text_content() or ""
        
        allure.attach(auth_page.screenshot(full_page=True), "step_view_details", allure.attachment_type.PNG)
        
        view_has_first_name = "First Name" in view_details_text
        view_has_last_name = "Last Name" in view_details_text
        view_has_username = "Username" in view_details_text
        
        allure.attach(f"View - First Name: {view_has_first_name}", "view_fields")
        allure.attach(f"View - Last Name: {view_has_last_name}", "view_fields")
        allure.attach(f"View - Username: {view_has_username}", "view_fields")
        
        # 关闭 View Details
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    # 收集 Edit User 字段
    with allure.step("打开 Edit User 对话框并收集字段"):
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="Edit User").click()
        auth_page.wait_for_timeout(1000)
        
        dialog = auth_page.locator('[role="dialog"]')
        edit_user_text = dialog.text_content() or ""
        
        allure.attach(auth_page.screenshot(full_page=True), "step_edit_user", allure.attachment_type.PNG)
        
        edit_has_first_name = "First Name" in edit_user_text
        edit_has_last_name = "Last Name" in edit_user_text
        
        allure.attach(f"Edit - First Name: {edit_has_first_name}", "edit_fields")
        allure.attach(f"Edit - Last Name: {edit_has_last_name}", "edit_fields")
        
        # 关闭 Edit User
        dialog.get_by_role("button", name="Cancel", exact=True).click()
        auth_page.wait_for_timeout(500)
    
    with allure.step("验证字段一致性"):
        # Edit User 有的字段，View Details 也应该有
        inconsistencies = []
        
        if edit_has_first_name and not view_has_first_name:
            inconsistencies.append("First Name 在 Edit User 中有，但 View Details 中没有")
        
        if edit_has_last_name and not view_has_last_name:
            inconsistencies.append("Last Name 在 Edit User 中有，但 View Details 中没有")
        
        allure.attach("\n".join(inconsistencies) if inconsistencies else "无不一致", "inconsistencies")
        
        assert len(inconsistencies) == 0, \
            f"Bug: View Details 与 Edit User 信息不一致:\n" + "\n".join(inconsistencies)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# Bug #6: Two-Factor-Auth API 403 错误
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_details_2fa_api_no_errors - 2FA API 无错误")
def test_p1_view_details_2fa_api_no_errors(auth_page: Page):
    """
    验证：获取用户 Two-Factor-Auth 状态时 API 正常
    
    期望：admin 用户有权限查看其他用户的 2FA 状态，无 403 错误
    """
    logger = TestLogger("test_p1_bug_2fa_api_403")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    
    # 收集 API 响应
    api_responses = []
    
    def capture_response(response):
        if "two-factor" in response.url.lower() or "2fa" in response.url.lower():
            api_responses.append({
                "url": response.url,
                "status": response.status
            })
    
    auth_page.on("response", capture_response)
    
    with allure.step("导航到 Admin Users 页面"):
        page_obj.navigate()
        page_obj.wait_for_data_loaded(timeout=3000)  # 优化：减少超时
    
    with allure.step("打开 View Details 对话框"):
        rows = auth_page.locator('table tbody tr')
        first_row = rows.first
        first_row.locator('button').last.click()
        auth_page.wait_for_timeout(500)
        auth_page.get_by_role("menuitem", name="View Details").click()
        auth_page.wait_for_timeout(2000)  # 等待 API 调用
        
        allure.attach(auth_page.screenshot(full_page=True), "step_view_details", allure.attachment_type.PNG)
    
    with allure.step("检查 2FA API 响应"):
        # 检查是否有 403 响应
        error_responses = [r for r in api_responses if r["status"] == 403]
        
        allure.attach(f"总 2FA API 调用: {len(api_responses)}", "api_stats")
        allure.attach(f"403 错误数: {len(error_responses)}", "api_stats")
        
        if error_responses:
            for r in error_responses:
                allure.attach(f"URL: {r['url']}, Status: {r['status']}", "403_response")
        
        # 期望：不应该有 403 错误
        assert len(error_responses) == 0, \
            f"Bug: 获取 2FA 状态时返回 {len(error_responses)} 个 403 错误"
    
    with allure.step("关闭对话框"):
        auth_page.get_by_role("button", name="Close").click()
        auth_page.wait_for_timeout(500)
    
    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 - 完整字段用户 View Details 验证
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.admin
@allure.feature("Admin Users")
@allure.story("P1 - View Details 验证")
@allure.title("test_p1_view_details_full_fields_user - 完整字段用户 View Details")
def test_p1_view_details_full_fields_user(auth_page: Page):
    """
    创建所有字段完整的用户 → View Details 验证各字段展示
    字段：First Name / Last Name / Email / Username / Phone / Role / Status
    """
    logger = TestLogger("test_p1_view_details_full_fields_user")
    logger.start()

    page_obj = AdminUsersPage(auth_page)
    test_user = generate_unique_user("full_detail_test")
    first_name = "TestFirst"
    last_name = "TestLast"
    phone = "13912345678"
    created = []

    try:
        with allure.step("创建完整字段用户"):
            page_obj.navigate()
            page_obj.wait_for_data_loaded()
            page_obj.click_add_user()
            auth_page.wait_for_timeout(500)
            page_obj.fill_create_user_form(
                first_name=first_name, last_name=last_name,
                email=test_user["email"], username=test_user["username"],
                password=test_user["password"], phone=phone,
                role="admin", active=True,
            )
            step_shot(page_obj, "step_form_filled")
            page_obj.click_create_user()
            auth_page.wait_for_timeout(2000)
            created.append(test_user["username"])

        with allure.step("搜索并打开 View Details"):
            page_obj.wait_for_data_loaded()
            page_obj.search_user(test_user["username"])
            page_obj.wait_for_filter_results()
            assert page_obj.get_visible_user_count() > 0
            page_obj.click_actions_menu_for_user(test_user["username"])
            page_obj.click_view_details()
            auth_page.wait_for_timeout(1500)
            step_shot(page_obj, "step_view_details", full_page=True)

        with allure.step("验证各字段展示"):
            dialog = auth_page.locator('[role="dialog"]')
            text = dialog.text_content() or ""
            allure.attach(f"Dialog 文本:\n{text[:600]}", "dialog_text",
                          allure.attachment_type.TEXT)

            checks = {
                "Username": test_user["username"] in text,
                "Email": test_user["email"] in text,
                "First Name": first_name in text,
                "Last Name": last_name in text,
                "Role (admin)": "admin" in text.lower(),
            }
            for field, found in checks.items():
                allure.attach(f"{field}: {'✅' if found else '❌'}", f"check_{field}",
                              allure.attachment_type.TEXT)
            step_shot(page_obj, "step_fields_verified")

            # 必须显示 Username 和 Email
            assert checks["Username"], f"应显示 Username: {test_user['username']}"
            assert checks["Email"], f"应显示 Email: {test_user['email']}"

        with allure.step("关闭"):
            auth_page.get_by_role("button", name="Close").click()
            auth_page.wait_for_timeout(500)

        logger.end(success=True)

    finally:
        for u in created:
            try:
                delete_test_user(page_obj, u)
            except Exception:
                pass

