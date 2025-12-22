# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword Page Object
# Generated: 2025-12-22 13:06:47
# ═══════════════════════════════════════════════════════════════
"""
AdminProfileChangePassword 页面对象
URL: https://localhost:3000/admin/profile/change-password
Type: SETTINGS
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminProfileChangePasswordPage(BasePage):
    """
    AdminProfileChangePassword 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # currentPassword | placeholder: Current password | required
    CURRENTPASSWORD_INPUT = "[name='currentPassword']"

    # newPassword | placeholder: New password
    NEWPASSWORD_INPUT = "[name='newPassword']"

    # confirmNewPassword | placeholder: Confirm new password
    CONFIRMNEWPASSWORD_INPUT = "[name='confirmNewPassword']"

    # button
    TOGGLE_NAVIGATION_MENU_BUTTON = "button[type='button']"

    # button
    RADIXRDJEL7_BUTTON = "#radix-«Rdjel7»"

    # button
    SAVE_BUTTON = "button[type='submit']"

    # link
    AEVATAR_AI_LINK = "a[href='/']"

    # link
    HOME_LINK = "a[href='/admin']"

    # link
    WORKFLOW_LINK = "a[href='/workflow']"

    # link
    RADIXR7NEJEL7TRIGGERPERSONAL_S_LINK = "#radix-«R7nejel7»-trigger-Personal Settings"

    # link
    RADIXR7NEJEL7TRIGGERCHANGE_PAS_LINK = "#radix-«R7nejel7»-trigger-Change Password"

    
    URL = "/admin/profile/change-password"
    page_loaded_indicator = "button[type='submit']"
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AdminProfileChangePassword 页面")
        self.goto(self.URL)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def fill_currentpassword(self, value: str) -> None:
        """填写 Current password"""
        logger.info(f"填写 Current password: {value}")
        self.fill(self.CURRENTPASSWORD_INPUT, value)
    
    def get_currentpassword_value(self) -> str:
        """获取 Current password 的值"""
        return super().get_input_value(self.CURRENTPASSWORD_INPUT)

    def fill_newpassword(self, value: str) -> None:
        """填写 New password"""
        logger.info(f"填写 New password: {value}")
        self.fill(self.NEWPASSWORD_INPUT, value)
    
    def get_newpassword_value(self) -> str:
        """获取 New password 的值"""
        return super().get_input_value(self.NEWPASSWORD_INPUT)

    def fill_confirmnewpassword(self, value: str) -> None:
        """填写 Confirm new password"""
        logger.info(f"填写 Confirm new password: {value}")
        self.fill(self.CONFIRMNEWPASSWORD_INPUT, value)
    
    def get_confirmnewpassword_value(self) -> str:
        """获取 Confirm new password 的值"""
        return super().get_input_value(self.CONFIRMNEWPASSWORD_INPUT)

    def click_toggle_navigation_menu(self) -> None:
        """点击 Toggle navigation menu 按钮"""
        logger.info("点击 Toggle navigation menu 按钮")
        self.click(self.TOGGLE_NAVIGATION_MENU_BUTTON)

    def click_toggle_user_menu(self) -> None:
        """点击 Toggle user menu 按钮"""
        logger.info("点击 Toggle user menu 按钮")
        self.click(self.RADIXRDJEL7_BUTTON)

    def click_save(self) -> None:
        """点击 Save 按钮"""
        logger.info("点击 Save 按钮")
        self.click(self.SAVE_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
