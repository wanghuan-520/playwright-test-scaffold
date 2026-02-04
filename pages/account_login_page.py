# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AccountLogin Page Object
# Generated: 2026-01-29 18:43:45
# ═══════════════════════════════════════════════════════════════
"""
AccountLogin 页面对象
URL: http://localhost:5173/account/login
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
    
    # username_or_email_address | 实际页面ID选择器
    USERNAME_OR_EMAIL_ADDRESS_INPUT = '#email'
    
    # 兼容性：为了保持与旧测试用例的兼容性
    USERNAME_OR_EMAIL_ADDRESS_INPUT_OLD = '#email'  # 旧测试用例可能使用这个名称

    # password | 实际页面ID选择器
    PASSWORD_INPUT = '#password'

    # login | 实际页面按钮选择器
    LOGIN_BUTTON = 'button[type="submit"]'

    # register | 实际页面链接
    REGISTER_LINK = 'a[href="/register"]'

    # forgot_password | 实际页面链接
    FORGOT_PASSWORD_LINK = 'a[href="/forgot-password"]'

    
    URL = 'http://localhost:5173/login'
    page_loaded_indicator = '#email'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AccountLogin 页面")
        self.goto(self.URL, wait_for_load=False)
        # 等待React应用加载
        try:
            self.page.wait_for_function(
                "() => { const root = document.getElementById('root'); return root && root.children.length > 0; }",
                timeout=30000
            )
        except Exception:
            pass
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            # 先检查React root是否有内容
            root_has_content = self.page.evaluate("""() => {
                const root = document.getElementById('root');
                return root && root.children.length > 0;
            }""")
            if not root_has_content:
                # 等待React应用加载
                try:
                    self.page.wait_for_function(
                        "() => { const root = document.getElementById('root'); return root && root.children.length > 0; }",
                        timeout=30000
                    )
                except Exception:
                    pass
            
            # 再检查目标元素（使用更宽松的等待）
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def fill_username_or_email_address(self, value: str) -> None:
        """填写 username_or_email_address"""
        logger.info(f"填写 username_or_email_address (len={len(value)})")
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
