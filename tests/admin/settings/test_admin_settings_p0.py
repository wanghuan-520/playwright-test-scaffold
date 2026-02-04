# ═══════════════════════════════════════════════════════════════
# Admin Platform Settings P0 Tests
# ═══════════════════════════════════════════════════════════════
"""
P0 级别测试：Admin Platform Settings 页面核心功能

测试点：
- 页面可访问（需要 admin 权限）
- 核心控件可见
- Tab 切换正常
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_settings_page import AdminSettingsPage
from tests.myaccount._helpers import step_shot
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.admin
@allure.feature("Admin Platform Settings")
@allure.story("P0 - 页面加载")
class TestAdminSettingsP0:
    """Admin Platform Settings 页面 P0 测试"""
    
    @allure.title("test_p0_admin_settings_page_load - 页面可打开且核心控件可见")
    def test_p0_admin_settings_page_load(self, auth_page: Page):
        """
        验证：
        1. 页面可导航到 /admin/settings
        2. 页面标题 "Platform Settings" 可见
        3. Tab 选项卡可见
        """
        logger = TestLogger("test_p0_admin_settings_page_load")
        logger.start()
        
        page_obj = AdminSettingsPage(auth_page)
        
        with allure.step("导航到 Admin Settings 页面"):
            page_obj.navigate()
            step_shot(page_obj, "step_navigate")
        
        with allure.step("验证页面标题可见"):
            assert page_obj.is_loaded(), "页面未加载完成"
        
        with allure.step("验证核心控件可见"):
            assert page_obj.is_visible(page_obj.TOOLS_MCP_TAB, timeout=5000), "Tools & MCP Tab 不可见"
            assert page_obj.is_visible(page_obj.LLM_PROVIDERS_TAB, timeout=3000), "LLM Providers Tab 不可见"
            assert page_obj.is_visible(page_obj.AGENTS_TAB, timeout=3000), "Agents Tab 不可见"
            assert page_obj.is_visible(page_obj.ADVANCED_TAB, timeout=3000), "Advanced Tab 不可见"
            step_shot(page_obj, "step_verify_controls")
        
        logger.end(success=True)
    
    @allure.title("test_p0_admin_settings_tab_switch - Tab 切换正常")
    def test_p0_admin_settings_tab_switch(self, auth_page: Page):
        """
        验证：
        1. 可以切换到各个 Tab
        2. Tab 内容正确显示
        """
        logger = TestLogger("test_p0_admin_settings_tab_switch")
        logger.start()
        
        page_obj = AdminSettingsPage(auth_page)
        
        with allure.step("导航到 Admin Settings 页面"):
            page_obj.navigate()
            step_shot(page_obj, "step_initial_tools_mcp")
        
        with allure.step("切换到 LLM Providers Tab"):
            page_obj.switch_to_llm_providers()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_llm_providers_tab")
        
        with allure.step("切换到 Agents Tab"):
            page_obj.switch_to_agents()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_agents_tab")
            # 验证 No Session Connected 消息
            assert page_obj.is_visible(page_obj.NO_SESSION_MESSAGE, timeout=3000), "No Session Connected 消息不可见"
        
        with allure.step("切换到 Advanced Tab"):
            page_obj.switch_to_advanced()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_advanced_tab")
        
        with allure.step("切换回 Tools & MCP Tab"):
            page_obj.switch_to_tools_mcp()
            auth_page.wait_for_timeout(500)
            step_shot(page_obj, "step_back_to_tools_mcp")
        
        logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Platform Settings")
@allure.story("P1 - Bug 验证")
class TestAdminSettingsBugs:
    """Admin Platform Settings 页面 Bug 验证测试"""
    
    @allure.title("test_p1_bug_ux_contradiction_disabled_button - Bug#4: UX 矛盾")
    @pytest.mark.xfail(reason="已知 Bug: Reconnect MCP 按钮禁用但提示让用户点击")
    def test_p1_bug_ux_contradiction_disabled_button(self, auth_page: Page):
        """
        Bug #4: UX 矛盾 - 禁用按钮提示
        
        现象：
        - "Reconnect MCP" 按钮是禁用状态
        - 但提示文字 "Try 'Reconnect MCP' or 'Update Skills'" 让用户点击它
        
        预期：
        - 提示文字应该根据按钮状态动态调整
        - 或者按钮应该可点击
        """
        logger = TestLogger("test_p1_bug_ux_contradiction_disabled_button")
        logger.start()
        
        page_obj = AdminSettingsPage(auth_page)
        
        with allure.step("导航到 Admin Settings 页面"):
            page_obj.navigate()
            step_shot(page_obj, "step_page_loaded")
        
        with allure.step("确保在 Tools & MCP Tab"):
            page_obj.switch_to_tools_mcp()
            auth_page.wait_for_timeout(500)
        
        with allure.step("检查 Reconnect MCP 按钮状态"):
            is_disabled = page_obj.is_reconnect_mcp_disabled()
            allure.attach(f"Reconnect MCP 按钮禁用: {is_disabled}", "按钮状态")
        
        with allure.step("检查 'No tools available' 提示"):
            has_message = page_obj.has_no_tools_message()
            allure.attach(f"显示 'No tools' 提示: {has_message}", "提示消息")
        
        with allure.step("验证 UX 矛盾"):
            is_contradiction = page_obj.is_ux_contradiction()
            step_shot(page_obj, "step_ux_check")
            
            if is_contradiction:
                pytest.xfail("Bug 确认: Reconnect MCP 按钮禁用，但提示让用户点击它，UX 矛盾")
        
        logger.end(success=True)

