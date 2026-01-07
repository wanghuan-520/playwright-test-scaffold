# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Waits
# ═══════════════════════════════════════════════════════════════
"""
页面等待策略（Waits）。

说明：
- 该类作为 mixin 被 `BasePage` 组合使用，只提供等待相关方法。
"""

from utils.logger import get_logger

logger = get_logger(__name__)


class PageWaits:
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
