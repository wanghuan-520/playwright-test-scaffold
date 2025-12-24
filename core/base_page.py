# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Base Page (Core)
# ═══════════════════════════════════════════════════════════════
"""
BasePage - 页面对象基类核心
"""

from playwright.sync_api import Page
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
import os
from core.page_actions import PageActions
from core.page_waits import PageWaits
from core.page_utils import PageUtils
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class BasePage(ABC, PageActions, PageWaits):
    """页面对象基类 - 继承操作和等待能力"""
    
    URL: str = "/"
    page_loaded_indicator: str = "body"
    
    def __init__(self, page: Page):
        """初始化页面对象"""
        self.page = page
        self.utils = PageUtils(page)
        self.config = ConfigManager()
        self.base_url = self.config.get_service_url("frontend") or ""
    
    # ═══════════════════════════════════════════════════════════════
    # ABSTRACT METHODS
    # ═══════════════════════════════════════════════════════════════
    
    @abstractmethod
    def navigate(self) -> None:
        """导航到页面"""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def goto(self, path: str = "", wait_for_load: bool = True) -> None:
        """
        导航到指定路径
        
        Args:
            path: 相对路径或完整URL
            wait_for_load: 是否等待页面加载完成
        """
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        logger.info(f"导航到: {url}")
        
        # SPA / 长轮询场景下，等待 "load" 容易卡死（资源持续加载/连接不断开）
        # 默认用 domcontentloaded，更符合“页面可交互”的定义。
        wait_until = os.getenv("PAGE_GOTO_WAIT_UNTIL", "domcontentloaded").strip() or "domcontentloaded"
        timeout_ms = int(os.getenv("PAGE_GOTO_TIMEOUT_MS", "60000"))
        self.page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        
        if wait_for_load:
            self.wait_for_page_load()
    
    def wait_for_page_load(self, timeout: int = 30000) -> None:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待页面加载: {self.__class__.__name__}")
        # 可配置的 load_state（默认 networkidle；需要提速可用 domcontentloaded）
        load_state = os.getenv("WAIT_FOR_LOAD_STATE", "networkidle").strip() or "networkidle"
        self.page.wait_for_load_state(load_state, timeout=timeout)
        
        # 等待页面标识元素
        if self.page_loaded_indicator:
            try:
                self.page.wait_for_selector(
                    self.page_loaded_indicator, 
                    state="visible", 
                    timeout=timeout
                )
            except Exception as e:
                logger.warning(f"页面加载指示器未找到: {self.page_loaded_indicator}")
    
    def refresh(self) -> None:
        """刷新页面"""
        logger.info("刷新页面")
        self.page.reload(wait_until='networkidle')
        self.wait_for_page_load()
    
    def go_back(self) -> None:
        """返回上一页"""
        logger.info("返回上一页")
        self.page.go_back()
        self.wait_for_page_load()
    
    def go_forward(self) -> None:
        """前进到下一页"""
        logger.info("前进到下一页")
        self.page.go_forward()
        self.wait_for_page_load()
    
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # QUERY METHODS
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
    
    def get_text(self, selector: str, timeout: int = 10000) -> Optional[str]:
        """
        获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            str: 元素文本
        """
        try:
            return self.page.text_content(selector, timeout=timeout)
        except Exception:
            return None
    
    def get_input_value(self, selector: str) -> str:
        """
        获取输入框的值
        
        Args:
            selector: 元素选择器
            
        Returns:
            str: 输入框的值
        """
        return self.page.input_value(selector)
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            
        Returns:
            str: 属性值
        """
        return self.page.get_attribute(selector, attribute)
    
    # ══════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════
    # SCREENSHOT METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def take_screenshot(self, name: str = "screenshot", full_page: bool = True) -> str:
        """
        截取页面截图
        
        Args:
            name: 截图名称（用于保存文件）
            
        Returns:
            str: 截图文件路径
        """
        from pathlib import Path
        import allure
        
        # 创建截图目录
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        
        # 生成截图文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = screenshot_dir / filename
        
        # 截取截图
        screenshot_bytes = self.page.screenshot(full_page=full_page)
        
        # 保存文件
        with open(filepath, "wb") as f:
            f.write(screenshot_bytes)
        
        # 附加到 Allure 报告
        allure.attach(
            screenshot_bytes,
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
        
        logger.info(f"截图已保存: {filepath}")
        return str(filepath)
    

    
    def get_title(self) -> str:
        """
        获取页面标题
        
        Returns:
            str: 页面标题
        """
        return self.page.title()
    
    # ═══════════════════════════════════════════════════════════════
    # WAIT METHODS
    # ═══════════════════════════════════════════════════════════════


class BaseDialog(BasePage):
    """
    对话框基类
    
    使用方式:
        class ConfirmDialog(BaseDialog):
            DIALOG_SELECTOR = ".modal-dialog"
            CONFIRM_BUTTON = "button.confirm"
            CANCEL_BUTTON = "button.cancel"
            
            def confirm(self):
                self.click(self.CONFIRM_BUTTON)
            
            def cancel(self):
                self.click(self.CANCEL_BUTTON)
    """
    
    DIALOG_SELECTOR: str = ".dialog"
    
    def navigate(self) -> None:
        """对话框不需要导航"""
        pass
    
    def is_loaded(self) -> bool:
        """检查对话框是否显示"""
        return self.is_visible(self.DIALOG_SELECTOR)
    
    def close(self) -> None:
        """关闭对话框"""
        # 尝试点击关闭按钮
        close_selectors = [
            f"{self.DIALOG_SELECTOR} .close",
            f"{self.DIALOG_SELECTOR} [aria-label='close']",
            f"{self.DIALOG_SELECTOR} button:has-text('Close')",
            f"{self.DIALOG_SELECTOR} button:has-text('Cancel')",
        ]
        
        for selector in close_selectors:
            if self.is_visible(selector, timeout=1000):
                self.click(selector)
                return
        
        # 按ESC键关闭
        self.page.keyboard.press("Escape")

