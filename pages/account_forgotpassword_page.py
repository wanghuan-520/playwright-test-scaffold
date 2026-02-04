# ═══════════════════════════════════════════════════════════════
# AccountForgotPassword Page Object
# ═══════════════════════════════════════════════════════════════
"""
AccountForgotPassword 页面对象
URL: http://localhost:5173/forgot-password
Type: PUBLIC (匿名页)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountForgotpasswordPage(BasePage):
    """
    AccountForgotPassword 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS (使用 Playwright MCP 定位)
    # ═══════════════════════════════════════════════════════════════
    
    # email 输入框 - textbox "Email Address", placeholder="Enter your email"
    EMAIL_INPUT = 'input[placeholder="Enter your email"]'
    EMAIL_INPUT_ROLE = 'role=textbox[name="Email Address"]'
    
    # 提交按钮 - "Send Reset Link"
    SUBMIT_BUTTON = 'button:has-text("Send Reset Link")'
    SUBMIT_BUTTON_ROLE = 'role=button[name="Send Reset Link"]'
    
    # 返回登录链接 - "Back to sign in"
    BACK_TO_LOGIN_LINK = 'a[href="/login"]'
    BACK_TO_LOGIN_LINK_ROLE = 'role=link[name="Back to sign in"]'
    
    # 页面 URL
    URL = 'http://localhost:5173/forgot-password'
    URL_PATH = '/forgot-password'
    
    # 页面加载标识
    page_loaded_indicator = 'input[placeholder="Enter your email"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info("导航到 AccountForgotPassword 页面")
        self.goto(self.URL, wait_for_load=False)
        # 等待 React 应用加载
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
            # 先检查 React root 是否有内容
            root_has_content = self.page.evaluate("""() => {
                const root = document.getElementById('root');
                return root && root.children.length > 0;
            }""")
            if not root_has_content:
                try:
                    self.page.wait_for_function(
                        "() => { const root = document.getElementById('root'); return root && root.children.length > 0; }",
                        timeout=30000
                    )
                except Exception:
                    pass
            
            # 检查目标元素
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def fill_email(self, value: str) -> None:
        """填写 email"""
        logger.info(f"填写 email (len={len(value)})")
        self.fill(self.EMAIL_INPUT, value)
    
    def get_email_value(self) -> str:
        """获取 email 的值"""
        return super().get_input_value(self.EMAIL_INPUT)
    
    def click_submit(self) -> None:
        """点击提交按钮"""
        logger.info("点击 Send Reset Link 按钮")
        self.click(self.SUBMIT_BUTTON)
    
    def click_back_to_login(self) -> None:
        """点击返回登录链接"""
        logger.info("点击 Back to sign in 链接")
        self.click(self.BACK_TO_LOGIN_LINK)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
    
    def has_error_message(self) -> bool:
        """检查是否有错误提示"""
        error_selectors = [
            ".text-red-500",
            ".text-danger",
            ".error-message",
            ".invalid-feedback",
            "[role='alert']",
        ]
        for sel in error_selectors:
            try:
                if self.page.locator(sel).count() > 0 and self.page.is_visible(sel, timeout=500):
                    return True
            except Exception:
                continue
        return False
    
    def get_error_message(self) -> str:
        """获取错误提示文本"""
        error_selectors = [
            ".text-red-500",
            ".text-danger",
            ".error-message",
            ".invalid-feedback",
            "[role='alert']",
        ]
        for sel in error_selectors:
            try:
                if self.page.locator(sel).count() > 0:
                    return self.page.locator(sel).first.inner_text(timeout=500) or ""
            except Exception:
                continue
        return ""

