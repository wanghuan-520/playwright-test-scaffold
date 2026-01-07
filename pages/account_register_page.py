# ═══════════════════════════════════════════════════════════════
# AccountRegister Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AccountRegister 页面对象
URL: https://localhost:44320/Account/Register
Type: REGISTER
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountRegisterPage(BasePage):
    """
    AccountRegister 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # username | placeholder: username
    USERNAME_INPUT = 'role=textbox[name="Username *"]'

    # email_address | placeholder: email_address
    EMAIL_ADDRESS_INPUT = 'role=textbox[name="Email address *"]'

    # password | placeholder: password
    PASSWORD_INPUT = 'role=textbox[name="Password *"]'

    # english | placeholder: english
    ENGLISH_BUTTON = 'role=button[name="\uf658 English"]'

    # register | placeholder: register
    REGISTER_BUTTON = 'role=button[name="Register"]'

    # login | placeholder: login
    LOGIN_LINK = 'role=link[name="Login"]'

    
    URL = 'https://localhost:44320/Account/Register'
    page_loaded_indicator = 'role=textbox[name="Username *"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AccountRegister 页面")
        # BasePage.goto 默认会 wait_for_page_load；这里避免重复等待（降低超时/flake 概率）
        self.goto(self.URL, wait_for_load=False)
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

    def fill_username(self, value: str) -> None:
        """填写 username"""
        logger.info("填写 username (len={len(value)})")
        self.fill(self.USERNAME_INPUT, value)
    
    def get_username_value(self) -> str:
        """获取 username 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.USERNAME_INPUT)

    def fill_email_address(self, value: str) -> None:
        """填写 email_address"""
        logger.info("填写 email_address (len={len(value)})")
        self.fill(self.EMAIL_ADDRESS_INPUT, value)
    
    def get_email_address_value(self) -> str:
        """获取 email_address 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.EMAIL_ADDRESS_INPUT)

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

    def click_register(self) -> None:
        """点击 register 按钮"""
        logger.info("点击 register 按钮")
        self.click(self.REGISTER_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
