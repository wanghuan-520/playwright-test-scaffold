# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Actions
# ═══════════════════════════════════════════════════════════════
"""
BasePage - 所有页面对象的抽象基类
提供统一的页面操作接口，子类只需关注业务逻辑
"""

from playwright.sync_api import Page, Locator, expect
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from core.page_utils import PageUtils
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)



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
        logger.debug(f"填写输入框: {selector} = {value}")
        # 先等待元素可见
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        # 再等待元素可交互
        self.page.wait_for_selector(selector, state="attached", timeout=5000)
        # 填写
        self.page.fill(selector, value, timeout=timeout)
    
    def clear_and_fill(self, selector: str, value: str, timeout: int = 10000) -> None:
        """
        清空并填写输入框
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"清空并填写: {selector} = {value}")
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
        logger.debug(f"选择选项: {selector} = {value}")
        self.page.select_option(selector, value)
    
    def check(self, selector: str) -> None:
        """勾选复选框"""
        logger.debug(f"勾选: {selector}")
        self.page.check(selector)
    
    def uncheck(self, selector: str) -> None:
        """取消勾选复选框"""
        logger.debug(f"取消勾选: {selector}")
        self.page.uncheck(selector)
    
    # ═══════════════════════════════════════════════════════════════
    # ELEMENT STATE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 元素是否可见
        """
        try:
            return self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return False
    
    def is_enabled(self, selector: str) -> bool:
        """检查元素是否启用"""
        return self.page.is_enabled(selector)
    
    def is_checked(self, selector: str) -> bool:
        """检查复选框是否被勾选"""
        return self.page.is_checked(selector)
    
