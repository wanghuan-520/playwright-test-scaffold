# ═══════════════════════════════════════════════════════════════
# AccountRegister Page Object
# Updated: 2026-01-30
# ═══════════════════════════════════════════════════════════════
"""
AccountRegister 页面对象
URL: http://localhost:5173/register

字段说明（根据 docs/requirements/account-register-field-requirements.md）：
- UserName: 用户名，直接传递给后端（最大256字符，必须唯一）
- Email: 邮箱地址，直接传递给后端（最大256字符，必须唯一，邮箱格式）
- Password: 密码，直接传递给后端（最小6字符，大小写+数字+特殊字符）
"""

import re
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
    # SELECTORS（实际页面元素 ID）
    # ═══════════════════════════════════════════════════════════════
    
    # userName | 用户名输入框（独立字段，不再从 email 生成）
    USERNAME_INPUT = '#userName'

    # email | 邮箱输入框
    EMAIL_INPUT = '#email'

    # password | 密码输入框
    PASSWORD_INPUT = '#password'

    # register | 注册按钮
    REGISTER_BUTTON = 'button[type="submit"]'

    # terms | 条款复选框
    TERMS_CHECKBOX = 'button[role="checkbox"]'

    # login | 登录链接
    LOGIN_LINK = 'a[href="/login"]'

    # 兼容性别名（为了保持与旧测试用例的兼容性）
    FULL_NAME_INPUT = '#userName'  # 旧测试用例可能使用 FULL_NAME_INPUT
    EMAIL_ADDRESS_INPUT = '#email'  # 旧测试用例可能使用 EMAIL_ADDRESS_INPUT

    URL = 'http://localhost:5173/register'
    page_loaded_indicator = '#userName'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AccountRegister 页面")
        # BasePage.goto 默认会 wait_for_page_load；这里避免重复等待（降低超时/flake 概率）
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
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def fill_username(self, value: str) -> None:
        """填写 UserName（用户名）"""
        logger.info(f"填写 UserName (len={len(value)})")
        self.fill(self.USERNAME_INPUT, value)
    
    def get_username_value(self) -> str:
        """获取 UserName 的值"""
        return super().get_input_value(self.USERNAME_INPUT)

    def fill_email(self, value: str) -> None:
        """填写 Email（邮箱）"""
        logger.info(f"填写 Email (len={len(value)})")
        self.fill(self.EMAIL_INPUT, value)
    
    def get_email_value(self) -> str:
        """获取 Email 的值"""
        return super().get_input_value(self.EMAIL_INPUT)
    
    def fill_password(self, value: str) -> None:
        """填写 Password（密码）"""
        logger.info("填写 Password: ***")
        self.secret_fill(self.PASSWORD_INPUT, value)
    
    def get_password_value(self) -> str:
        """获取 Password 的值"""
        return super().get_input_value(self.PASSWORD_INPUT)
    
    def check_terms(self) -> None:
        """勾选 Terms of Service and Privacy Policy 复选框"""
        logger.info("勾选 Terms of Service and Privacy Policy")
        # 首选：使用 role selector（最可靠）
        checkbox = self.page.get_by_role("checkbox", name=re.compile(r"agree.*terms", re.IGNORECASE)).first
        if checkbox.count() > 0:
            if not checkbox.is_checked():
                checkbox.click()  # 使用 click() 而不是 check()，因为这是 button[role="checkbox"]
                return
        # 备选：使用 CSS selector
        checkbox_btn = self.page.locator(self.TERMS_CHECKBOX)
        if checkbox_btn.count() > 0:
            if checkbox_btn.get_attribute("aria-checked") != "true":
                checkbox_btn.click()
    
    def is_terms_checked(self) -> bool:
        """检查 Terms 复选框是否已勾选"""
        try:
            # 首选：使用 role selector
            checkbox = self.page.get_by_role("checkbox", name=re.compile(r"agree.*terms", re.IGNORECASE)).first
            if checkbox.count() > 0:
                return checkbox.get_attribute("aria-checked") == "true"
            # 备选：使用 CSS selector
            checkbox_btn = self.page.locator(self.TERMS_CHECKBOX)
            if checkbox_btn.count() > 0:
                return checkbox_btn.get_attribute("aria-checked") == "true"
            return False
        except Exception:
            return False

    def click_register(self) -> None:
        """点击 Create Account 按钮"""
        logger.info("点击 Create Account 按钮")
        self.click(self.REGISTER_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # 兼容性方法（为旧测试用例保留）
    # ═══════════════════════════════════════════════════════════════
    
    def fill_full_name(self, value: str) -> None:
        """兼容旧代码：填写 Full Name（实际是 UserName）"""
        self.fill_username(value)
    
    def get_full_name_value(self) -> str:
        """兼容旧代码：获取 Full Name（实际是 UserName）"""
        return self.get_username_value()
    
    def fill_email_address(self, value: str) -> None:
        """兼容旧代码：填写 Email Address（实际是 Email）"""
        self.fill_email(value)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
