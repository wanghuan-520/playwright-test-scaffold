# ═══════════════════════════════════════════════════════════════
# Login Page Object - Generic Template
# ═══════════════════════════════════════════════════════════════
"""
通用登录页对象模板

使用说明：
  1. 复制此文件到你的项目
  2. 修改选择器以匹配你的登录表单
  3. 根据需要调整登录成功判定逻辑

设计原则：
  - 只做一件事：把"登录"变成可复用的稳定动作
  - 不把密码写进日志
  - 不绑定具体业务：登录成功判定交给调用方
"""

from __future__ import annotations

from typing import Optional
from playwright.sync_api import Page

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """
    通用登录页对象模板
    
    根据你的项目修改以下选择器：
    """

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS - 修改为你项目的选择器
    # ═══════════════════════════════════════════════════════════════
    
    # 输入框选择器（根据你的项目修改）
    USERNAME_INPUT = "#username"          # 或 "[name='username']", "[name='email']"
    PASSWORD_INPUT = "#password"          # 或 "[name='password']", "[type='password']"
    
    # 提交按钮选择器
    SUBMIT_BUTTON = "button[type='submit']"  # 或 "#login-btn", ".login-button"
    
    # 登录成功后的标识元素（用于判断登录是否成功）
    SUCCESS_INDICATOR = "[data-testid='user-menu']"  # 或 ".user-avatar", "#logout-btn"
    
    # 错误消息选择器
    ERROR_MESSAGE = ".error-message"  # 或 "[role='alert']", ".toast-error"

    # ═══════════════════════════════════════════════════════════════
    # PAGE CONFIG
    # ═══════════════════════════════════════════════════════════════
    
    # 登录页 URL（相对路径）
    URL = "/login"
    
    # 页面加载指示器
    page_loaded_indicator = "#username"  # 修改为你的登录表单标识元素

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到登录页"""
        logger.info(f"导航到登录页: {self.URL}")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        """检查登录页是否加载完成"""
        try:
            return self.is_visible(self.USERNAME_INPUT, timeout=10_000)
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def fill_username(self, username: str) -> None:
        """填写用户名"""
        logger.info(f"填写用户名: {username}")
        self.fill(self.USERNAME_INPUT, username)
    
    def fill_password(self, password: str) -> None:
        """填写密码（不记录到日志）"""
        logger.info("填写密码: ***")
        self.page.wait_for_selector(self.PASSWORD_INPUT, state="visible", timeout=30_000)
        self.page.fill(self.PASSWORD_INPUT, password, timeout=30_000)
    
    def click_submit(self) -> None:
        """点击登录按钮"""
        logger.info("点击登录按钮")
        self.click(self.SUBMIT_BUTTON)

    def login(self, *, username: str, password: str) -> None:
        """
        执行登录
        
        Args:
            username: 用户名或邮箱
            password: 密码
        
        注意：
            - 只负责填写并提交
            - 登录成功/失败的判定由调用方处理
        """
        logger.info(f"执行登录: {username}")
        
        # 如果不在登录页，先导航
        if not self.is_loaded():
            self.navigate()
        
        # 填写表单
        self.fill_username(username)
        self.fill_password(password)
        
        # 提交
        self.click_submit()
        
        # 等待页面响应
        self.page.wait_for_timeout(1000)

    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def is_logged_in(self, timeout: int = 10_000) -> bool:
        """
        检查是否登录成功
        
        根据你的项目修改判定逻辑，例如：
        - 检查用户菜单是否可见
        - 检查登出按钮是否存在
        - 检查 URL 是否跳转到首页
        """
        try:
            return self.is_visible(self.SUCCESS_INDICATOR, timeout=timeout)
        except Exception:
            return False
    
    def get_error_message(self) -> Optional[str]:
        """获取登录错误消息"""
        if self.is_visible(self.ERROR_MESSAGE, timeout=2000):
            return self.get_text(self.ERROR_MESSAGE)
        return None
    
    def has_error(self) -> bool:
        """检查是否显示错误消息"""
        return self.is_visible(self.ERROR_MESSAGE, timeout=2000)

    # ═══════════════════════════════════════════════════════════════
    # COMPOSITE ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def login_and_verify(self, *, username: str, password: str) -> bool:
        """
        登录并验证是否成功
        
        Returns:
            bool: 登录是否成功
        """
        self.login(username=username, password=password)
        return self.is_logged_in()
