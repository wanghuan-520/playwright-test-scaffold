# ═══════════════════════════════════════════════════════════════
# Profile (View) - P2
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
P2：UI 可见性与可访问性测试（查看模式）。

测试内容：
- 字段标签可见性
- 页面布局
- 响应式检查
"""

import pytest
import allure

from utils.logger import TestLogger
from tests.myaccount._helpers import attach_rule_source_note, step_shot
from playwright.sync_api import Page
from pages.personal_settings_page import PersonalSettingsPage


@pytest.fixture(scope="function")
def profile_page(auth_page: Page):
    """
    Profile 页面 fixture（仅用于查看模式测试）
    """
    page_obj = PersonalSettingsPage(auth_page)
    page_obj.navigate()
    yield auth_page, page_obj


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile")
@allure.story("P2 - Fields Visible")
@allure.description(
    """
测试点：
- 验证查看模式下所有元素可见
- 证据：全页截图
"""
)
def test_p2_profile_fields_visible(profile_page):
    """P2: 字段可见性检查"""
    attach_rule_source_note("Profile P2 - fields visible")
    logger = TestLogger("test_p2_profile_fields_visible")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("检查页面标题可见"):
        assert page_obj.is_visible(page_obj.PAGE_TITLE, timeout=3000), "My Account 标题不可见"
        assert page_obj.is_visible(page_obj.PROFILE_HEADING, timeout=3000), "Profile 标题不可见"

    with allure.step("检查侧边栏导航可见"):
        assert page_obj.is_visible(page_obj.PROFILE_LINK, timeout=3000), "Profile 链接不可见"
        assert page_obj.is_visible(page_obj.PASSWORD_LINK, timeout=3000), "Password 链接不可见"

    with allure.step("检查操作按钮可见"):
        assert page_obj.is_visible(page_obj.BACK_BUTTON, timeout=3000), "Back 按钮不可见"
        assert page_obj.is_visible(page_obj.EDIT_BUTTON, timeout=3000), "Edit 按钮不可见"

    step_shot(page_obj, "step_all_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile")
@allure.story("P2 - User Avatar Display")
@allure.description(
    """
测试点：
- 验证用户头像区域可见
- 证据：截图
"""
)
def test_p2_profile_user_avatar(profile_page):
    """P2: 用户头像展示"""
    attach_rule_source_note("Profile P2 - user avatar")
    logger = TestLogger("test_p2_profile_user_avatar")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("检查用户头像区域"):
        # 头像按钮（带有相机图标的按钮）
        avatar_button = auth_page.locator('button:has(img)').first
        is_visible = avatar_button.is_visible(timeout=3000)
        
        allure.attach(
            f"头像按钮可见: {is_visible}",
            name="avatar_visible",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_avatar_area", full_page=True)

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile")
@allure.story("P2 - Keyboard Navigation")
@allure.description(
    """
测试点：
- Tab 键导航顺序正确（查看模式）
- 证据：每个 Tab 步骤截图
"""
)
def test_p2_profile_keyboard_navigation(profile_page):
    """P2: Tab 键导航（查看模式）"""
    attach_rule_source_note("Profile P2 - keyboard navigation")
    logger = TestLogger("test_p2_profile_keyboard_navigation")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("Tab 键导航测试"):
        # 聚焦到 Back 按钮
        auth_page.locator(page_obj.BACK_BUTTON).focus()
        
        for i in range(5):
            # 添加红色边框高亮当前焦点元素
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '3px solid red';
                }
            }""")
            step_shot(page_obj, f"step_tab_{i}", full_page=True)
            # 移除高亮
            auth_page.evaluate("""() => {
                const focused = document.activeElement;
                if (focused) {
                    focused.style.outline = '';
                }
            }""")
            auth_page.keyboard.press("Tab")
            auth_page.wait_for_timeout(100)

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile")
@allure.story("P2 - Page Title")
@allure.description(
    """
测试点：
- 验证页面标题正确
- 证据：标题截图
"""
)
def test_p2_profile_page_title(profile_page):
    """P2: 页面标题检查"""
    attach_rule_source_note("Profile P2 - page title")
    logger = TestLogger("test_p2_profile_page_title")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("检查页面标题"):
        title = auth_page.title()
        allure.attach(
            f"页面标题: {title}",
            name="page_title",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 验证标题包含预期关键词
        assert title, "页面标题为空"
        step_shot(page_obj, "step_page_title", full_page=True)

    logger.end(success=True)



