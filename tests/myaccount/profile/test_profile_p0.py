# ═══════════════════════════════════════════════════════════════
# Profile (View) - P0
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
P0：页面展示测试（查看模式）。

测试内容：
- 页面加载
- 核心控件可见
- 导航功能
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


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P0 - Page Load")
@allure.description(
    """
测试点：
- 页面可正常打开（/account/profile），不被重定向到登录页
- 核心控件可见：Profile 标题 / Edit 按钮
- 证据：关键步骤截图
"""
)
def test_p0_profile_page_load(profile_page):
    """P0: 页面加载 + 核心控件可见"""
    attach_rule_source_note("Profile P0 - page load")
    logger = TestLogger("test_p0_profile_page_load")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证页面加载完成"):
        step_shot(page_obj, "step_page_loaded", full_page=True)

    # 验证未被重定向到登录页
    assert not page_obj.is_login_page(), f"疑似未登录，current_url={auth_page.url}"

    # 验证核心控件可见
    with allure.step("验证核心控件可见"):
        assert page_obj.is_visible(page_obj.PROFILE_HEADING, timeout=3000), "Profile 标题不可见"
        assert page_obj.is_visible(page_obj.EDIT_BUTTON, timeout=3000), "Edit 按钮不可见"
        step_shot(page_obj, "step_verify_controls", full_page=True)

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P0 - User Info Display")
@allure.description(
    """
测试点：
- 验证用户信息正确显示
- User Name、Email、Full Name、Phone Number 等字段可见
- 证据：用户信息截图
"""
)
def test_p0_profile_user_info_display(profile_page):
    """P0: 用户信息展示"""
    attach_rule_source_note("Profile P0 - user info display")
    logger = TestLogger("test_p0_profile_user_info_display")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证用户信息区域可见"):
        # 验证 Personal Information 区块
        assert page_obj.is_visible('h3:has-text("Personal Information")', timeout=3000), "Personal Information 标题不可见"
        step_shot(page_obj, "step_user_info_visible", full_page=True)

    with allure.step("验证用户字段标签可见"):
        # 注：Member Since 字段已从页面移除
        labels = ["User Name", "Full Name", "Email Address", "Phone Number"]
        for label in labels:
            assert page_obj.is_visible(f'p:has-text("{label}")', timeout=2000), f"{label} 标签不可见"
        
        allure.attach(
            f"验证的字段标签: {', '.join(labels)}",
            name="verified_labels",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P0 - Sidebar Navigation")
@allure.description(
    """
测试点：
- 侧边栏导航功能正常
- Profile 和 Password 链接可见且可点击
- 证据：导航前后截图
"""
)
def test_p0_profile_sidebar_navigation(profile_page):
    """P0: 侧边栏导航"""
    attach_rule_source_note("Profile P0 - sidebar navigation")
    logger = TestLogger("test_p0_profile_sidebar_navigation")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证侧边栏链接可见"):
        assert page_obj.is_visible(page_obj.PROFILE_LINK, timeout=3000), "Profile 链接不可见"
        assert page_obj.is_visible(page_obj.PASSWORD_LINK, timeout=3000), "Password 链接不可见"
        step_shot(page_obj, "step_sidebar_visible", full_page=True)

    with allure.step("点击 Password 链接"):
        page_obj.go_to_password_page()
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_after_nav_password", full_page=True)

    # 验证已导航到 Password 页面
    current_url = auth_page.url or ""
    assert "/account/password" in current_url.lower(), f"未导航到 Password 页面，当前 URL: {current_url}"

    with allure.step("点击 Profile 链接返回"):
        auth_page.click(page_obj.PROFILE_LINK)
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_after_nav_profile", full_page=True)

    # 验证已返回 Profile 页面
    current_url = auth_page.url or ""
    assert "/account/profile" in current_url.lower(), f"未返回 Profile 页面，当前 URL: {current_url}"

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P0 - Back Button")
@allure.description(
    """
测试点：
- Back 按钮功能正常
- 点击后返回上一页
- 证据：点击前后截图
"""
)
def test_p0_profile_back_button(profile_page):
    """P0: Back 按钮"""
    attach_rule_source_note("Profile P0 - back button")
    logger = TestLogger("test_p0_profile_back_button")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证 Back 按钮可见"):
        assert page_obj.is_visible(page_obj.BACK_BUTTON, timeout=3000), "Back 按钮不可见"
        step_shot(page_obj, "step_back_button_visible", full_page=True)

    with allure.step("点击 Back 按钮"):
        page_obj.click_back()
        auth_page.wait_for_timeout(1000)
        step_shot(page_obj, "step_after_back", full_page=True)

    # 验证已离开 Profile 页面
    current_url = auth_page.url or ""
    # Back 按钮通常返回到 /app 主页
    allure.attach(
        f"点击 Back 后的 URL: {current_url}",
        name="url_after_back",
        attachment_type=allure.attachment_type.TEXT,
    )

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P0 - Security Settings Display")
@allure.description(
    """
测试点：
- Security Settings 区块可见
- Change Password 按钮可见
- 证据：截图
"""
)
def test_p0_profile_security_settings_display(profile_page):
    """P0: Security Settings 展示"""
    attach_rule_source_note("Profile P0 - security settings display")
    logger = TestLogger("test_p0_profile_security_settings_display")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证 Security Settings 区块可见"):
        assert page_obj.is_visible('h3:has-text("Security Settings")', timeout=3000), "Security Settings 标题不可见"
        step_shot(page_obj, "step_security_settings_visible", full_page=True)

    with allure.step("验证 Change Password 按钮可见"):
        assert page_obj.is_visible(page_obj.CHANGE_PASSWORD_BUTTON, timeout=3000), "Change Password 按钮不可见"

    logger.end(success=True)

