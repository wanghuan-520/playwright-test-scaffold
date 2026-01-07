# ═══════════════════════════════════════════════════════════════
# AdminProfile Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AdminProfile 页面对象
URL: https://localhost:3000/admin/profile
Type: SETTINGS
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminProfilePage(BasePage):
    """
    AdminProfile 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # personal_settings | placeholder: personal_settings
    PERSONAL_SETTINGS_BUTTON = 'role=tab[name="Personal Settings"]'

    # change_password | placeholder: change_password
    CHANGE_PASSWORD_BUTTON = 'role=tab[name="Change Password"]'

    # user_name | placeholder: user_name
    USER_NAME_INPUT = 'role=textbox[name="User name *"]'

    # name | placeholder: name
    NAME_INPUT = 'role=textbox[name="Name"]'

    # surname | placeholder: surname
    SURNAME_INPUT = 'role=textbox[name="Surname"]'

    # email_address | placeholder: email_address
    EMAIL_ADDRESS_INPUT = 'role=textbox[name="Email address *"]'

    # phone_number | placeholder: phone_number
    PHONE_NUMBER_INPUT = 'role=textbox[name="Phone number"]'

    # toggle_user_menu | placeholder: toggle_user_menu
    TOGGLE_USER_MENU_BUTTON = 'role=button[name="Toggle user menu"]'

    # save | placeholder: save
    SAVE_BUTTON = 'role=button[name="Save"]'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # home | placeholder: home
    HOME_LINK = 'role=link[name="Home"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    
    URL = 'https://localhost:3000/admin/profile'
    page_loaded_indicator = 'role=button[name="Save"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AdminProfile 页面")
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

    def click_personal_settings(self) -> None:
        """点击 personal_settings 按钮"""
        logger.info("点击 personal_settings 按钮")
        self.click(self.PERSONAL_SETTINGS_BUTTON)

    def click_change_password(self) -> None:
        """点击 change_password 按钮"""
        logger.info("点击 change_password 按钮")
        self.click(self.CHANGE_PASSWORD_BUTTON)

    def fill_user_name(self, value: str) -> None:
        """填写 user_name"""
        logger.info("填写 user_name (len={len(value)})")
        self.fill(self.USER_NAME_INPUT, value)
    
    def get_user_name_value(self) -> str:
        """获取 user_name 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.USER_NAME_INPUT)

    def fill_name(self, value: str) -> None:
        """填写 name"""
        logger.info("填写 name (len={len(value)})")
        self.fill(self.NAME_INPUT, value)
    
    def get_name_value(self) -> str:
        """获取 name 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.NAME_INPUT)

    def fill_surname(self, value: str) -> None:
        """填写 surname"""
        logger.info("填写 surname (len={len(value)})")
        self.fill(self.SURNAME_INPUT, value)
    
    def get_surname_value(self) -> str:
        """获取 surname 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.SURNAME_INPUT)

    def fill_email_address(self, value: str) -> None:
        """填写 email_address"""
        logger.info("填写 email_address (len={len(value)})")
        self.fill(self.EMAIL_ADDRESS_INPUT, value)
    
    def get_email_address_value(self) -> str:
        """获取 email_address 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.EMAIL_ADDRESS_INPUT)

    def fill_phone_number(self, value: str) -> None:
        """填写 phone_number"""
        logger.info("填写 phone_number (len={len(value)})")
        self.fill(self.PHONE_NUMBER_INPUT, value)
    
    def get_phone_number_value(self) -> str:
        """获取 phone_number 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.PHONE_NUMBER_INPUT)

    def click_toggle_user_menu(self) -> None:
        """点击 toggle_user_menu 按钮"""
        logger.info("点击 toggle_user_menu 按钮")
        self.click(self.TOGGLE_USER_MENU_BUTTON)

    def click_save(self) -> None:
        """点击 save 按钮"""
        logger.info("点击 save 按钮")
        self.click(self.SAVE_BUTTON)

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
