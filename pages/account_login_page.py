# ═══════════════════════════════════════════════════════════════
# AccountLogin Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AccountLogin 页面对象
URL: https://localhost:44320/Account/Login
Type: LOGIN
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountLoginPage(BasePage):
    """
    AccountLogin 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # username_or_email_address | placeholder: username_or_email_address
    USERNAME_OR_EMAIL_ADDRESS_INPUT = 'role=textbox[name="Username or email address"]'

    # password | placeholder: password
    PASSWORD_INPUT = 'role=textbox[name="Password"]'

    # english | placeholder: english
    ENGLISH_BUTTON = 'role=button[name="\uf658 English"]'

    # login | placeholder: login
    LOGIN_BUTTON = 'role=button[name="Login"]'

    # register | placeholder: register
    REGISTER_LINK = 'role=link[name="Register"]'

    # forgot_password | placeholder: forgot_password
    FORGOT_PASSWORD_LINK = 'role=link[name="Forgot password?"]'

    
    URL = 'https://localhost:44320/Account/Login'
    page_loaded_indicator = 'role=textbox[name="Username or email address"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AccountLogin 页面")
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

    def fill_username_or_email_address(self, value: str) -> None:
        """填写 username_or_email_address"""
        logger.info("填写 username_or_email_address (len={len(value)})")
        self.fill(self.USERNAME_OR_EMAIL_ADDRESS_INPUT, value)
    
    def get_username_or_email_address_value(self) -> str:
        """获取 username_or_email_address 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.USERNAME_OR_EMAIL_ADDRESS_INPUT)

    def fill_password(self, value: str) -> None:
        """填写 password"""
        logger.info("填写 password: ***")
        self.secret_fill(self.PASSWORD_INPUT, value)
    
    def get_password_value(self) -> str:
        """获取 password 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.PASSWORD_INPUT)

    def click_english(self) -> None:
        """点击 english 按钮"""
        logger.info("点击 english 按钮")
        self.click(self.ENGLISH_BUTTON)

    def click_login(self) -> None:
        """点击 login 按钮"""
        logger.info("点击 login 按钮")
        self.click(self.LOGIN_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
