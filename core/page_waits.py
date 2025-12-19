# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Waits
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



class PageWaits:
    pass
    """页面等待策略"""

    def wait_for_element(self, selector: str, state: str = "visible", timeout: int = 10000) -> None:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            state: 状态（visible, attached, detached, hidden）
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待元素: {selector} ({state})")
        self.page.wait_for_selector(selector, state=state, timeout=timeout)
    
    def wait_for_url(self, url_pattern: str, timeout: int = 10000) -> None:
        """
        等待URL匹配
        
        Args:
            url_pattern: URL模式（支持正则）
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待URL匹配: {url_pattern}")
        self.page.wait_for_url(url_pattern, timeout=timeout)
    
    def wait(self, milliseconds: int) -> None:
        """等待指定毫秒数"""
        self.page.wait_for_timeout(milliseconds)
