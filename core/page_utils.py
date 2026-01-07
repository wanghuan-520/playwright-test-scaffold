# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Utilities
# ═══════════════════════════════════════════════════════════════
"""
PageUtils - 页面操作工具类
提供通用的页面操作方法，与框架无关
"""

from playwright.sync_api import Page, Locator
from typing import Optional, List, Any
import allure
from utils.logger import get_logger

logger = get_logger(__name__)


class PageUtils:
    """页面操作工具类"""
    
    def __init__(self, page: Page):
        """
        初始化工具类
        
        Args:
            page: Playwright Page对象
        """
        self.page = page
    
    # ═══════════════════════════════════════════════════════════════
    # SAFE OPERATIONS - 带错误处理的操作
    # ═══════════════════════════════════════════════════════════════
    
    def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """
        安全点击（带错误处理）
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 是否点击成功
        """
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            self.page.click(selector, timeout=timeout)
            logger.debug(f"✓ 点击成功: {selector}")
            return True
        except Exception as e:
            logger.error(f"✗ 点击失败: {selector} - {e}")
            return False
    
    def safe_fill(self, selector: str, value: str, timeout: int = 10000) -> bool:
        """
        安全填写（带错误处理）
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 是否填写成功
        """
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            self.page.fill(selector, value, timeout=timeout)
            # 安全：禁止把输入值写进日志（可能包含密码/Token/PII）
            logger.debug(f"✓ 填写成功: {selector} (len={len(value or '')})")
            return True
        except Exception as e:
            logger.error(f"✗ 填写失败: {selector} - {e}")
            return False
    
    def safe_get_text(self, selector: str, timeout: int = 10000) -> Optional[str]:
        """
        安全获取文本（带错误处理）
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            str: 元素文本，失败返回None
        """
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            text = self.page.text_content(selector, timeout=timeout)
            # 安全：避免把页面文本直接落日志（可能包含 PII）；仅记录长度
            logger.debug(f"获取文本: {selector} (len={len(text or '')})")
            return text
        except Exception as e:
            logger.error(f"✗ 获取文本失败: {selector} - {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # ELEMENT QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    def count_elements(self, selector: str) -> int:
        """
        计算匹配元素数量
        
        Args:
            selector: 元素选择器
            
        Returns:
            int: 元素数量
        """
        return self.page.locator(selector).count()
    
    def get_all_texts(self, selector: str) -> List[str]:
        """
        获取所有匹配元素的文本
        
        Args:
            selector: 元素选择器
            
        Returns:
            List[str]: 文本列表
        """
        return self.page.locator(selector).all_text_contents()
    
    def get_all_attributes(self, selector: str, attribute: str) -> List[str]:
        """
        获取所有匹配元素的指定属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            
        Returns:
            List[str]: 属性值列表
        """
        elements = self.page.locator(selector).all()
        return [el.get_attribute(attribute) for el in elements]
    
    # ═══════════════════════════════════════════════════════════════
    # SCROLL OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def scroll_to_top(self) -> None:
        """滚动到页面顶部"""
        self.page.evaluate("window.scrollTo(0, 0)")
        logger.debug("滚动到页面顶部")
    
    def scroll_to_bottom(self) -> None:
        """滚动到页面底部"""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        logger.debug("滚动到页面底部")
    
    def scroll_to_element(self, selector: str) -> None:
        """
        滚动到元素位置
        
        Args:
            selector: 元素选择器
        """
        try:
            self.page.locator(selector).scroll_into_view_if_needed()
            logger.debug(f"滚动到元素: {selector}")
        except Exception as e:
            logger.error(f"✗ 滚动失败: {selector} - {e}")
    
    def scroll_by(self, x: int = 0, y: int = 0) -> None:
        """
        滚动指定距离
        
        Args:
            x: 水平滚动距离（像素）
            y: 垂直滚动距离（像素）
        """
        self.page.evaluate(f"window.scrollBy({x}, {y})")
    
    # ═══════════════════════════════════════════════════════════════
    # SCREENSHOT
    # ═══════════════════════════════════════════════════════════════
    
    def take_screenshot(
        self, 
        file_path: str = None, 
        full_page: bool = False,
        attach_to_allure: bool = True,
        step_name: str = "Screenshot"
    ) -> bytes:
        """
        截取屏幕截图
        
        Args:
            file_path: 保存路径（可选）
            full_page: 是否截取整页
            attach_to_allure: 是否附加到Allure报告
            step_name: Allure步骤名称
            
        Returns:
            bytes: 截图数据
        """
        try:
            screenshot_bytes = self.page.screenshot(full_page=full_page)
            
            # 保存到文件
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(screenshot_bytes)
                logger.debug(f"截图已保存: {file_path}")
            
            # 附加到Allure报告
            if attach_to_allure:
                allure.attach(
                    screenshot_bytes,
                    name=step_name,
                    attachment_type=allure.attachment_type.PNG
                )
                logger.debug(f"截图已附加到Allure: {step_name}")
            
            return screenshot_bytes
        except Exception as e:
            logger.error(f"✗ 截图失败: {e}")
            return b""
    
    # ═══════════════════════════════════════════════════════════════
    # JAVASCRIPT EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    def execute_script(self, script: str) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            
        Returns:
            Any: 脚本执行结果
        """
        try:
            result = self.page.evaluate(script)
            logger.debug(f"执行脚本成功")
            return result
        except Exception as e:
            logger.error(f"✗ 执行脚本失败: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # FORM HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def fill_form(self, form_data: dict) -> None:
        """
        批量填写表单
        
        Args:
            form_data: 字段选择器与值的映射 {"#username": "testuser", "#password": "123456"}
        """
        for selector, value in form_data.items():
            self.safe_fill(selector, value)
    
    def get_form_values(self, selectors: List[str]) -> dict:
        """
        批量获取表单值
        
        Args:
            selectors: 输入框选择器列表
            
        Returns:
            dict: 选择器与值的映射
        """
        return {selector: self.page.input_value(selector) for selector in selectors}
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDATION HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def has_validation_error(self, error_selectors: List[str] = None) -> bool:
        """
        检查是否有验证错误
        
        Args:
            error_selectors: 错误信息选择器列表（可选，使用默认值）
            
        Returns:
            bool: 是否有错误
        """
        if error_selectors is None:
            error_selectors = [
                ".invalid-feedback",
                ".text-danger",
                "[role='alert']",
                ".error-message",
                ".field-error",
                ".toast-error",
                ".Toastify__toast--error",
            ]
        
        for selector in error_selectors:
            if self.page.is_visible(selector, timeout=1000):
                return True
        return False
    
    def get_validation_errors(self, error_selectors: List[str] = None) -> List[str]:
        """
        获取所有验证错误信息
        
        Args:
            error_selectors: 错误信息选择器列表（可选，使用默认值）
            
        Returns:
            List[str]: 错误信息列表
        """
        if error_selectors is None:
            error_selectors = [
                ".invalid-feedback",
                ".text-danger",
                "[role='alert']",
                ".error-message",
            ]
        
        errors = []
        for selector in error_selectors:
            if self.page.is_visible(selector, timeout=500):
                texts = self.page.locator(selector).all_text_contents()
                errors.extend([t.strip() for t in texts if t.strip()])
        
        return errors
    
    # ═══════════════════════════════════════════════════════════════
    # DRAG & DROP
    # ═══════════════════════════════════════════════════════════════
    
    def drag_and_drop(self, source: str, target: str) -> None:
        """
        拖拽操作
        
        Args:
            source: 源元素选择器
            target: 目标元素选择器
        """
        try:
            self.page.locator(source).drag_to(self.page.locator(target))
            logger.debug(f"拖拽: {source} -> {target}")
        except Exception as e:
            logger.error(f"✗ 拖拽失败: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # KEYBOARD
    # ═══════════════════════════════════════════════════════════════
    
    def press_key(self, key: str) -> None:
        """
        按下键盘键
        
        Args:
            key: 键名（如 "Enter", "Escape", "Tab"）
        """
        self.page.keyboard.press(key)
        logger.debug(f"按键: {key}")
    
    def press_keys(self, keys: str) -> None:
        """
        按下组合键
        
        Args:
            keys: 组合键（如 "Control+A", "Shift+Tab"）
        """
        self.page.keyboard.press(keys)
        logger.debug(f"组合键: {keys}")

