# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Actions
# ═══════════════════════════════════════════════════════════════
"""
BasePage - 所有页面对象的抽象基类
提供统一的页面操作接口，子类只需关注业务逻辑
"""

from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)



def _value_len(value: Optional[str]) -> int:
    try:
        return len(value or "")
    except Exception:
        return 0


class PageActions:
    """页面操作封装"""

    def click(self, selector: str, timeout: int = 10000) -> None:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"点击元素: {selector}")
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 30000) -> None:
        """
        填写输入框
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)，默认30秒
        """
        # 安全：禁止把用户输入值打进日志（可能包含密码/Token/PII）
        logger.debug(f"填写输入框: {selector} (len={_value_len(value)})")
        # 先等待元素可见
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        # 再等待元素可交互
        self.page.wait_for_selector(selector, state="attached", timeout=5000)
        # 填写
        self.page.fill(selector, value, timeout=timeout)

    def secret_fill(self, selector: str, value: str, timeout: int = 30000) -> None:
        """
        填写敏感输入框（例如密码），日志中不打印明文。
        - 规则：只记录 selector，不记录 value
        """
        logger.debug(f"填写敏感输入框: {selector} = ***")
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        self.page.wait_for_selector(selector, state="attached", timeout=5000)
        self.page.fill(selector, value, timeout=timeout)
    
    def clear_and_fill(self, selector: str, value: str, timeout: int = 10000) -> None:
        """
        清空并填写输入框
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)
        """
        # 安全：禁止把用户输入值打进日志（可能包含密码/Token/PII）
        logger.debug(f"清空并填写: {selector} (len={_value_len(value)})")
        element = self.page.locator(selector)
        element.clear()
        element.fill(value)
    
    def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """
        逐字符输入文本（模拟真实输入）
        
        Args:
            selector: 元素选择器
            text: 要输入的文本
            delay: 字符间延迟(毫秒)
        """
        logger.debug(f"逐字符输入: {selector}")
        self.page.locator(selector).type(text, delay=delay)
    
    def select_option(self, selector: str, value: str) -> None:
        """
        选择下拉框选项
        
        Args:
            selector: 元素选择器
            value: 选项值
        """
        # 安全：避免把值打进日志（可能包含 PII）
        logger.debug(f"选择选项: {selector} (len={_value_len(value)})")
        self.page.select_option(selector, value)
    
    def check(self, selector: str) -> None:
        """勾选复选框"""
        logger.debug(f"勾选: {selector}")
        self.page.check(selector)
    
    def uncheck(self, selector: str) -> None:
        """取消勾选复选框"""
        logger.debug(f"取消勾选: {selector}")
        self.page.uncheck(selector)
    
    # NOTE:
    # - BasePage 已提供 is_visible/is_enabled/is_checked 等查询接口
    # - 这里仅保留“动作”方法，避免 mixin 间 API 重叠造成困惑
