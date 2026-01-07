# ═══════════════════════════════════════════════════════════════
# AdminSettings Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AdminSettings 页面对象
URL: https://localhost:3000/admin/settings
Type: SETTINGS
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminSettingsPage(BasePage):
    """
    AdminSettings 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # emailing | placeholder: emailing
    EMAILING_BUTTON = 'role=tab[name="Emailing"]'

    # feature_management | placeholder: feature_management
    FEATURE_MANAGEMENT_BUTTON = 'role=tab[name="Feature management"]'

    # default_from_display_name | placeholder: default_from_display_name
    DEFAULT_FROM_DISPLAY_NAME_INPUT = 'role=textbox[name="Default from display name"]'

    # default_from_address | placeholder: default_from_address
    DEFAULT_FROM_ADDRESS_INPUT = 'role=textbox[name="Default from address"]'

    # host | placeholder: host
    HOST_INPUT = 'role=textbox[name="Host"]'

    # domain | placeholder: domain
    DOMAIN_INPUT = 'role=textbox[name="Domain"]'

    # user_name | placeholder: user_name
    USER_NAME_INPUT = 'role=textbox[name="User name"]'

    # password | placeholder: password
    PASSWORD_INPUT = 'role=textbox[name="Password"]'

    # toggle_user_menu | placeholder: toggle_user_menu
    TOGGLE_USER_MENU_BUTTON = 'role=button[name="Toggle user menu"]'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # home | placeholder: home
    HOME_LINK = 'role=link[name="Home"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    
    URL = 'https://localhost:3000/admin/settings'
    # Save 按钮在“无权限/Feature 禁用”时可能不存在；用更稳定的 tab 作为加载指示器
    page_loaded_indicator = 'role=tab[name="Emailing"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AdminSettings 页面")
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

    def click_emailing(self) -> None:
        """点击 emailing 按钮"""
        logger.info("点击 emailing 按钮")
        self.click(self.EMAILING_BUTTON)

    def click_feature_management(self) -> None:
        """点击 feature_management 按钮"""
        logger.info("点击 feature_management 按钮")
        self.click(self.FEATURE_MANAGEMENT_BUTTON)

    def fill_default_from_display_name(self, value: str) -> None:
        """填写 default_from_display_name"""
        logger.info("填写 default_from_display_name (len={len(value)})")
        self.fill(self.DEFAULT_FROM_DISPLAY_NAME_INPUT, value)
    
    def get_default_from_display_name_value(self) -> str:
        """获取 default_from_display_name 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.DEFAULT_FROM_DISPLAY_NAME_INPUT)

    def fill_default_from_address(self, value: str) -> None:
        """填写 default_from_address"""
        logger.info("填写 default_from_address (len={len(value)})")
        self.fill(self.DEFAULT_FROM_ADDRESS_INPUT, value)
    
    def get_default_from_address_value(self) -> str:
        """获取 default_from_address 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.DEFAULT_FROM_ADDRESS_INPUT)

    def fill_host(self, value: str) -> None:
        """填写 host"""
        logger.info("填写 host (len={len(value)})")
        self.fill(self.HOST_INPUT, value)
    
    def get_host_value(self) -> str:
        """获取 host 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.HOST_INPUT)

    def fill_domain(self, value: str) -> None:
        """填写 domain"""
        logger.info("填写 domain (len={len(value)})")
        self.fill(self.DOMAIN_INPUT, value)
    
    def get_domain_value(self) -> str:
        """获取 domain 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.DOMAIN_INPUT)

    def fill_user_name(self, value: str) -> None:
        """填写 user_name"""
        logger.info("填写 user_name (len={len(value)})")
        self.fill(self.USER_NAME_INPUT, value)
    
    def get_user_name_value(self) -> str:
        """获取 user_name 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.USER_NAME_INPUT)

    def fill_password(self, value: str) -> None:
        """填写 password"""
        logger.info("填写 password: ***")
        self.secret_fill(self.PASSWORD_INPUT, value)
    
    def get_password_value(self) -> str:
        """获取 password 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.PASSWORD_INPUT)

    def click_toggle_user_menu(self) -> None:
        """点击 toggle_user_menu 按钮"""
        logger.info("点击 toggle_user_menu 按钮")
        self.click(self.TOGGLE_USER_MENU_BUTTON)

    def click_open_next_js_dev_tools(self) -> None:
        """点击 open_next_js_dev_tools 按钮"""
        logger.info("点击 open_next_js_dev_tools 按钮")
        self.click(self.OPEN_NEXT_JS_DEV_TOOLS_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
