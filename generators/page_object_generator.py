# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Object Generator
# ═══════════════════════════════════════════════════════════════
"""
Page Object 生成器 - 根据页面分析结果生成可执行的测试代码

职责：生成 Page Object 代码
- Page Object 类（带 Allure 步骤截图）
- 测试用例类（带描述/步骤/预期目标）
- 测试数据文件

Allure 报告增强：
- @allure.description() - 测试描述
- with allure.step() - 关键步骤（自动前后截图）
- allure.attach() - 预期目标附件
"""

from typing import Dict
from pathlib import Path
from datetime import datetime
import json

from generators.page_types import PageInfo, PageElement
from generators.utils import (
    to_snake_case,
    to_class_name,
    get_page_name_from_url,
    get_file_name_from_url,
    get_tc_prefix_from_url,
    extract_url_path,
    get_element_constant_name,
    get_element_comment,
)
from utils.logger import get_logger

logger = get_logger(__name__)



class PageObjectGenerator:
    """Page Object 代码生成器"""

    def generate_page_object(self, page_info: PageInfo) -> str:
        """生成 Page Object 代码"""
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        url_path = extract_url_path(page_info.url)
        indicator = page_info.elements[0].selector if page_info.elements else "body"
        
        selectors = self._gen_selectors(page_info)
        methods = self._gen_methods(page_info)
        
        return f'''# ═══════════════════════════════════════════════════════════════
# {class_name} Page Object
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
"""
{class_name} 页面对象
URL: {page_info.url}
Type: {page_info.page_type}
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class {class_name}Page(BasePage):
    """
    {class_name} 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
{selectors}
    
    URL = "{url_path}"
    page_loaded_indicator = "{indicator}"
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 {class_name} 页面")
        self.goto(self.URL)
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
{methods}
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
'''
    
    # ═══════════════════════════════════════════════════════════════
    # TEST CASES GENERATOR
    # ═══════════════════════════════════════════════════════════════
    

    def _gen_selectors(self, page_info: PageInfo) -> str:
        """生成选择器代码"""
        lines = []
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            comment = get_element_comment(elem)
            lines.append(f"    # {comment}")
            lines.append(f'    {const} = "{elem.selector}"')
            lines.append("")
        return "\n".join(lines) if lines else "    pass"
    
    def _gen_methods(self, page_info: PageInfo) -> str:
        """生成操作方法代码"""
        methods = []
        
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            
            if elem.type == "input":
                methods.append(self._input_method(elem, const))
            elif elem.type == "button":
                methods.append(self._button_method(elem, const))
            elif elem.type == "select":
                methods.append(self._select_method(elem, const))
        
        return "\n".join(methods) if methods else "\n    pass"
    
    def _input_method(self, elem: PageElement, const: str) -> str:
        name = to_snake_case(elem.name or elem.id or "input")
        desc = elem.placeholder or elem.name or "input"
        return f'''
    def fill_{name}(self, value: str) -> None:
        """填写 {desc}"""
        logger.info(f"填写 {desc}: {{value}}")
        self.fill(self.{const}, value)
    
    def get_{name}_value(self) -> str:
        """获取 {desc} 的值"""
        return self.get_input_value(self.{const})'''
    
    def _button_method(self, elem: PageElement, const: str) -> str:
        text = (elem.text or "button").strip()
        name = to_snake_case(text)
        return f'''
    def click_{name}(self) -> None:
        """点击 {text} 按钮"""
        logger.info("点击 {text} 按钮")
        self.click(self.{const})'''
    
    def _select_method(self, elem: PageElement, const: str) -> str:
        name = to_snake_case(elem.name or elem.id or "option")
        desc = elem.name or "option"
        return f'''
    def select_{name}(self, value: str) -> None:
        """选择 {desc}"""
        logger.info(f"选择 {desc}: {{value}}")
        self.select_option(self.{const}, value)'''
    
