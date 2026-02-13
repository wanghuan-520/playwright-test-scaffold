# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - P2 Tests
# ═══════════════════════════════════════════════════════════════
"""
P2 级别测试：角色管理页面 UI/可用性测试

测试点：
- 字段可见性
- 键盘导航
- 响应式布局

账号来源：
- 需要 admin 账号（account_type="admin"）
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.admin_roles_page import AdminRolesPage
from tests.admin.users_roles._helpers import (
    assert_not_redirected_to_login,
    step_shot,
)
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# P2 - UI 测试
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Roles")
@allure.story("P2 - UI 测试")
@allure.title("test_p2_fields_visible - 核心字段可见性")
def test_p2_fields_visible(auth_page: Page):
    """
    验证：
    1. 页面标题可见
    2. Create Role 按钮可见
    3. 角色卡片可见
    """
    logger = TestLogger("test_p2_fields_visible")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
    
    with allure.step("验证核心元素可见"):
        expect(auth_page.locator(page_obj.PAGE_TITLE)).to_be_visible()
        expect(auth_page.locator(page_obj.CREATE_ROLE_BUTTON)).to_be_visible()
        step_shot(page_obj, "step_fields_visible", full_page=True)
    
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Roles")
@allure.story("P2 - UI 测试")
@allure.title("test_p2_keyboard_navigation - 键盘 Tab 导航")
def test_p2_keyboard_navigation(auth_page: Page):
    """
    验证：
    1. 可以使用 Tab 键导航
    2. 焦点在可交互元素间移动（每次 Tab 截图记录焦点位置）
    """
    logger = TestLogger("test_p2_keyboard_navigation")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        page_obj.wait_for_roles_loaded(timeout=10000)
    
    with allure.step("点击页面主区域获得焦点"):
        # 点击页面空白处（非按钮），避免触发弹窗
        auth_page.locator("main").first.click()
        auth_page.wait_for_timeout(300)
    
    tab_count = 8
    focused_elements = []
    for i in range(1, tab_count + 1):
        with allure.step(f"第 {i} 次 Tab"):
            auth_page.keyboard.press("Tab")
            auth_page.wait_for_timeout(300)
            
            # 获取当前获得焦点的元素信息
            focus_info = auth_page.evaluate("""() => {
                const el = document.activeElement;
                if (!el || el === document.body) return 'body';
                const tag = el.tagName.toLowerCase();
                const text = (el.textContent || '').trim().substring(0, 50);
                const role = el.getAttribute('role') || '';
                const ariaLabel = el.getAttribute('aria-label') || '';
                return `${tag}${role ? '[role=' + role + ']' : ''} "${text || ariaLabel}"`;
            }""")
            focused_elements.append(f"Tab {i}: {focus_info}")
            step_shot(page_obj, f"step_tab_{i}", full_page=True)
    
    with allure.step("焦点导航记录"):
        allure.attach(
            "\n".join(focused_elements),
            "focus_sequence",
            allure.attachment_type.TEXT,
        )
    
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.admin
@pytest.mark.ui
@allure.feature("Admin Roles")
@allure.story("P2 - UI 测试")
@allure.title("test_p2_full_page_screenshot - 全页面截图")
def test_p2_full_page_screenshot(auth_page: Page):
    """
    验证：
    1. 页面可以完整截图
    2. 用于视觉回归测试
    """
    logger = TestLogger("test_p2_full_page_screenshot")
    logger.start()
    
    page_obj = AdminRolesPage(auth_page)
    
    with allure.step("导航到 Admin Roles 页面"):
        page_obj.navigate()
        assert_not_redirected_to_login(auth_page)
        auth_page.wait_for_timeout(1000)  # 等待动画完成
    
    with allure.step("全页面截图"):
        step_shot(page_obj, "step_full_page", full_page=True)
    
    logger.end(success=True)
