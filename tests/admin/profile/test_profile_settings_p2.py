# ═══════════════════════════════════════════════════════════════
# Profile Settings (Personal Settings) - P2
# ═══════════════════════════════════════════════════════════════
"""
P2：UI/可用性/交互（推荐最小集合）。

覆盖：
- Tabs 可用性：Personal Settings / Change Password 切换
- 键盘 Tab 导航基本可用（不做脆弱的“精确顺序”断言）

注意：
- 本目录使用 profile_settings fixture 做 baseline 修正与 teardown 回滚。
"""

import pytest
import allure

from utils.logger import TestLogger
from ._helpers import attach_rule_source_note, step_shot


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Tabs/Keyboard")
@allure.description(
    """
测试点：
- Tabs 切换可用：Personal Settings <-> Change Password
- 切换后页面仍可交互（无异常卡死/空白）
- 证据：切换前后各 1 张关键截图
"""
)
def test_p2_profile_settings_tabs_switch(profile_settings):
    """P2: Tabs 切换（Personal Settings <-> Change Password）"""
    attach_rule_source_note()
    logger = TestLogger("test_p2_profile_settings_tabs_switch")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("打开 /admin/profile（fixture 已完成导航）"):
        step_shot(page_obj, "step_open_profile")

    with allure.step("点击 Change Password tab"):
        auth_page.get_by_role("tab", name="Change Password").click()
        auth_page.wait_for_timeout(300)
        step_shot(page_obj, "step_after_click_change_password")

    with allure.step("点击 Personal Settings tab"):
        auth_page.get_by_role("tab", name="Personal Settings").click()
        auth_page.wait_for_timeout(300)
        step_shot(page_obj, "step_after_click_personal_settings")

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("Profile Settings")
@allure.story("P2 - Tabs/Keyboard")
@allure.description(
    """
测试点：
- 键盘 Tab 导航基本可用：焦点能推进、不丢失
- 不做脆弱的“精确顺序”断言，关注可用性（能 Tab 走下去）
- 证据：初始聚焦 + 每次 Tab 后截图
"""
)
def test_p2_profile_settings_keyboard_tab(profile_settings):
    """P2: 键盘 Tab 基本可用（焦点可推进且不丢失）"""
    attach_rule_source_note()
    logger = TestLogger("test_p2_profile_settings_keyboard_tab")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings

    with allure.step("点击第一个输入框并开始 Tab 导航"):
        auth_page.locator(page_obj.USERNAME_INPUT).click()
        step_shot(page_obj, "step_focus_username")

    with allure.step("连续按 Tab 4 次，观察焦点推进"):
        for i in range(4):
            auth_page.keyboard.press("Tab")
            auth_page.wait_for_timeout(150)
            step_shot(page_obj, f"step_tab_{i+1}")

    logger.end(success=True)
