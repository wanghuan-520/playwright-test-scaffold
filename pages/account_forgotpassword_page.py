# ═══════════════════════════════════════════════════════════════
# AccountForgotpassword Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AccountForgotpassword 页面对象
URL: https://localhost:44320/Account/ForgotPassword
Type: FORM
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountForgotpasswordPage(BasePage):
    """
    AccountForgotpassword 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # email | placeholder: email
    EMAIL_INPUT = 'role=textbox[name="Email *"]'

    # english | placeholder: english
    ENGLISH_BUTTON = 'role=button[name="\uf658 English"]'

    # submit | placeholder: submit
    SUBMIT_BUTTON = 'role=button[name="Submit"]'

    # login | placeholder: login
    LOGIN_LINK = 'role=link[name="Login"]'

    
    URL = 'https://localhost:44320/Account/ForgotPassword'
    page_loaded_indicator = 'role=textbox[name="Email *"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AccountForgotpassword 页面")
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

    def fill_email(self, value: str) -> None:
        """填写 email"""
        logger.info("填写 email (len={len(value)})")
        self.fill(self.EMAIL_INPUT, value)
    
    def get_email_value(self) -> str:
        """获取 email 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.EMAIL_INPUT)

    def click_english(self) -> None:
        """点击 english 按钮"""
        logger.info("点击 english 按钮")
        self.click(self.ENGLISH_BUTTON)

    def click_submit(self) -> None:
        """点击 submit 按钮"""
        logger.info("点击 submit 按钮")
        self.click(self.SUBMIT_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
