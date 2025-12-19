# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Element Extractor
# ═══════════════════════════════════════════════════════════════
"""
元素提取器 - 从页面中提取各种类型的元素
"""

from playwright.sync_api import Page
from typing import List, Optional, Dict
from generators.page_types import PageElement
from utils.logger import get_logger

logger = get_logger(__name__)


class ElementExtractor:
    """元素提取器"""

    def _get_elements(self, page: Page) -> List[PageElement]:
        """
        获取页面元素
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[PageElement]: 元素列表
        """
        elements = []
        
        # 获取输入框
        inputs = self._get_inputs(page)
        elements.extend(inputs)
        
        # 获取按钮
        buttons = self._get_buttons(page)
        elements.extend(buttons)
        
        # 获取链接
        links = self._get_links(page)
        elements.extend(links)
        
        # 获取下拉框
        selects = self._get_selects(page)
        elements.extend(selects)
        
        return elements
    
    def _get_inputs(self, page: Page) -> List[PageElement]:
        """获取输入框元素"""
        elements = []
        
        # 各种输入类型
        input_types = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='number']",
            "input[type='tel']",
            "input[type='url']",
            "input[type='search']",
            "input:not([type])",
            "textarea",
        ]
        
        for selector in input_types:
            try:
                locators = page.locator(selector).all()
                for i, loc in enumerate(locators):
                    try:
                        element = self._extract_element_info(loc, "input")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_buttons(self, page: Page) -> List[PageElement]:
        """获取按钮元素"""
        elements = []
        
        button_selectors = [
            "button",
            "input[type='submit']",
            "input[type='button']",
            "[role='button']",
        ]
        
        for selector in button_selectors:
            try:
                locators = page.locator(selector).all()
                for loc in locators:
                    try:
                        element = self._extract_element_info(loc, "button")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_links(self, page: Page) -> List[PageElement]:
        """获取链接元素"""
        elements = []
        
        try:
            locators = page.locator("a[href]").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "link")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _get_selects(self, page: Page) -> List[PageElement]:
        """获取下拉框元素"""
        elements = []
        
        try:
            locators = page.locator("select").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "select")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _extract_element_info(self, locator, element_type: str) -> Optional[PageElement]:
        """
        提取元素信息
        
        Args:
            locator: Playwright定位器
            element_type: 元素类型
            
        Returns:
            PageElement: 元素信息
        """
        try:
            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            selector = self._build_selector(locator, tag)
            attributes = self._extract_attributes(locator)
            
            return PageElement(
                selector=selector,
                tag=tag,
                type=element_type,
                text=locator.text_content() or "",
                placeholder=locator.get_attribute("placeholder") or "",
                name=locator.get_attribute("name") or "",
                id=locator.get_attribute("id") or "",
                role=locator.get_attribute("role") or "",
                required=locator.get_attribute("required") is not None,
                disabled=locator.get_attribute("disabled") is not None,
                attributes=attributes
            )
        except Exception as e:
            logger.debug(f"提取元素信息失败: {e}")
            return None
    
    def _build_selector(self, locator, tag: str) -> str:
        """构建元素选择器"""
        element_id = locator.get_attribute("id") or ""
        element_name = locator.get_attribute("name") or ""
        element_class = locator.get_attribute("class") or ""
        
        if element_id:
            return f"#{element_id}"
        elif element_name:
            return f"[name='{element_name}']"
        elif element_class:
            first_class = element_class.split()[0] if element_class else ""
            return f"{tag}.{first_class}" if first_class else tag
        else:
            return tag
    
    def _extract_attributes(self, locator) -> Dict[str, str]:
        """提取元素属性"""
        return {
            "type": locator.get_attribute("type") or "",
            "maxlength": locator.get_attribute("maxlength") or "",
            "pattern": locator.get_attribute("pattern") or "",
        }
    def _get_forms(self, page: Page) -> List[Dict]:
        """获取表单信息"""
        forms = []
        
        try:
            form_locators = page.locator("form").all()
            for form_loc in form_locators:
                try:
                    form_info = {
                        "id": form_loc.get_attribute("id") or "",
                        "action": form_loc.get_attribute("action") or "",
                        "method": form_loc.get_attribute("method") or "GET",
                        "inputs": [],
                    }
                    
                    # 获取表单内的输入框
                    inputs = form_loc.locator("input, textarea, select").all()
                    for inp in inputs:
                        form_info["inputs"].append({
                            "name": inp.get_attribute("name") or "",
                            "type": inp.get_attribute("type") or "text",
                            "required": inp.get_attribute("required") is not None,
                        })
                    
                    forms.append(form_info)
                except:
                    pass
        except:
            pass
        
        return forms
    
    def _get_navigation(self, page: Page) -> List[Dict]:
        """获取导航信息"""
        navigation = []
        
        nav_selectors = ["nav a", "header a", ".navbar a", ".menu a", ".nav a"]
        
        for selector in nav_selectors:
            try:
                links = page.locator(selector).all()
                for link in links:
                    try:
                        nav_item = {
                            "text": link.text_content() or "",
                            "href": link.get_attribute("href") or "",
                        }
                        if nav_item["text"] and nav_item["href"]:
                            navigation.append(nav_item)
                    except:
                        pass
            except:
                pass
        
        return navigation
    
