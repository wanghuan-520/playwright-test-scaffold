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

from typing import Dict, List, Tuple
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

    # 一些过于泛化的 selector 基本不适合生成到 Page Object（容易漂移、重复、不可维护）
    _GENERIC_SELECTORS_PREFIXES = (
        "button.",
        "a.",
    )
    _GENERIC_SELECTORS_EXACT = {
        "button",
        "a",
        "input",
        "select",
        "textarea",
    }

    def generate_page_object(self, page_info: PageInfo) -> str:
        """生成 Page Object 代码"""
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        url_path = extract_url_path(page_info.url)
        indicator = self._pick_page_loaded_indicator(page_info)
        
        selectors, name_map = self._gen_selectors(page_info)
        methods = self._gen_methods(page_info, name_map)
        
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
    

    def _pick_page_loaded_indicator(self, page_info: PageInfo) -> str:
        """
        选择一个“稳定且有业务意义”的页面加载指示器。

        设计原则：
        - 不能依赖“元素列表第一个”的偶然顺序（太脆弱）
        - Settings 页面优先选择 Save 按钮（语义稳定、跨主题不易漂移）
        - 否则退化到第一个可见输入框/按钮
        - 兜底用 body
        """
        # 通过可执行规则控制策略（缺失配置时使用默认值）
        try:
            from utils.rules_engine import get_rules_config

            rules_cfg = get_rules_config()
        except Exception:
            rules_cfg = None

        def _strategy_for(page_type: str) -> str:
            if rules_cfg is None:
                return "save_button" if page_type == "SETTINGS" else "first_input"
            if page_type == "SETTINGS":
                return (rules_cfg.page_loaded_indicator_settings or "").strip() or "save_button"
            return (rules_cfg.page_loaded_indicator_default or "").strip() or "first_input"

        elems = list(page_info.elements or [])

        # Settings / Profile 这类页面，Save 往往是最稳的锚点
        if (page_info.page_type or "").upper() == "SETTINGS":
            strat = _strategy_for("SETTINGS")
            if strat.startswith("css:"):
                return strat[4:].strip() or "body"
            if strat == "body":
                return "body"
            if strat not in {"save_button", "first_input"}:
                # 未知策略：退化为 save_button（最稳）
                strat = "save_button"

            if strat == "first_input":
                for e in elems:
                    if e.type in {"input", "select"} and (e.selector or "").strip():
                        return e.selector
                # fallback
                return "body"

            for e in elems:
                if e.type != "button":
                    continue
                t = (e.text or "").strip()
                if t.lower() == "save" and (e.selector or "").strip():
                    return e.selector
            # 如果分析没抓到 Save，也给一个稳定的语义 selector（比随机元素强）
            return "button:has-text('Save')"

        strat = _strategy_for((page_info.page_type or "").upper())
        if strat.startswith("css:"):
            return strat[4:].strip() or "body"
        if strat == "body":
            return "body"

        # 通用策略：优先输入框（业务字段），再按钮
        for e in elems:
            if e.type in {"input", "select"} and (e.selector or "").strip():
                return e.selector
        for e in elems:
            if e.type == "button" and (e.selector or "").strip():
                return e.selector

        return "body"

    def _is_meaningful_element(self, elem: PageElement) -> bool:
        """
        过滤掉“不可维护/无业务意义”的元素，避免生成大量噪音 selector。
        """
        sel = (elem.selector or "").strip()
        if not sel:
            return False

        # 1) 输入框/下拉框：基本都保留（业务字段核心）
        if elem.type in {"input", "select"}:
            return True

        # 2) button：必须有可识别信息（text 或 aria-label 或 id/name）
        if elem.type == "button":
            aria = (elem.attributes or {}).get("aria-label") if getattr(elem, "attributes", None) else None
            if (elem.text and elem.text.strip()) or (aria and str(aria).strip()) or elem.id or elem.name:
                return True
            # selector 过泛也丢弃
            return False

        # 3) link：必须有 text/href/id，且 selector 不能过泛
        if elem.type == "link":
            href = (elem.attributes or {}).get("href") if getattr(elem, "attributes", None) else None
            if (elem.text and elem.text.strip()) or (href and str(href).strip()) or elem.id or elem.name:
                return True
            return False

        # 其它类型默认不生成
        return False

    def _make_unique_name(self, base: str, used: Dict[str, int]) -> str:
        """
        对常量/方法名做去重：相同 base 时追加 _2/_3...（稳定且可读）。
        """
        if base not in used:
            used[base] = 1
            return base
        used[base] += 1
        return f"{base}_{used[base]}"

    def _gen_selectors(self, page_info: PageInfo) -> Tuple[str, Dict[str, str]]:
        """
        生成选择器代码，并返回 selector -> CONST 的映射（供方法生成使用）。
        """
        lines: List[str] = []
        used_consts: Dict[str, int] = {}
        selector_to_const: Dict[str, str] = {}

        for elem in page_info.elements:
            if not self._is_meaningful_element(elem):
                continue

            raw_const = get_element_constant_name(elem)
            const = self._make_unique_name(raw_const, used_consts)
            selector_to_const[(elem.selector or "").strip()] = const

            comment = get_element_comment(elem)
            lines.append(f"    # {comment}")
            lines.append(f'    {const} = "{elem.selector}"')
            lines.append("")

        return ("\n".join(lines) if lines else "    pass"), selector_to_const
    
    def _gen_methods(self, page_info: PageInfo, selector_to_const: Dict[str, str]) -> str:
        """生成操作方法代码（与 selector 去重后的 CONST 对齐）。"""
        methods: List[str] = []
        used_methods: Dict[str, int] = {}

        for elem in page_info.elements:
            if not self._is_meaningful_element(elem):
                continue

            const = selector_to_const.get((elem.selector or "").strip(), get_element_constant_name(elem))

            if elem.type == "input":
                methods.append(self._input_method(elem, const, used_methods))
            elif elem.type == "button":
                methods.append(self._button_method(elem, const, used_methods))
            elif elem.type == "select":
                methods.append(self._select_method(elem, const, used_methods))

        return "\n".join(methods) if methods else "\n    pass"
    
    def _input_method(self, elem: PageElement, const: str, used_methods: Dict[str, int]) -> str:
        name = to_snake_case(elem.name or elem.id or elem.placeholder or "input")
        name = self._make_unique_name(name, used_methods)
        desc = elem.placeholder or elem.name or "input"
        return f'''
    def fill_{name}(self, value: str) -> None:
        """填写 {desc}"""
        logger.info(f"填写 {desc}: {{value}}")
        self.fill(self.{const}, value)
    
    def get_{name}_value(self) -> str:
        """获取 {desc} 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.{const})'''
    
    def _button_method(self, elem: PageElement, const: str, used_methods: Dict[str, int]) -> str:
        aria = (elem.attributes or {}).get("aria-label") if getattr(elem, "attributes", None) else None
        text = (elem.text or aria or elem.name or elem.id or "button").strip()
        name = to_snake_case(text)
        name = self._make_unique_name(name or "button", used_methods)
        return f'''
    def click_{name}(self) -> None:
        """点击 {text} 按钮"""
        logger.info("点击 {text} 按钮")
        self.click(self.{const})'''
    
    def _select_method(self, elem: PageElement, const: str, used_methods: Dict[str, int]) -> str:
        name = to_snake_case(elem.name or elem.id or "option")
        name = self._make_unique_name(name, used_methods)
        desc = elem.name or "option"
        return f'''
    def select_{name}(self, value: str) -> None:
        """选择 {desc}"""
        logger.info(f"选择 {desc}: {{value}}")
        self.select_option(self.{const}, value)'''
    
