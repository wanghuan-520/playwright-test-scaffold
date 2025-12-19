# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Generator Interfaces
# ═══════════════════════════════════════════════════════════════
"""
生成器接口定义 - 使用 Protocol 定义接口契约

优势:
- 提高类型安全性
- 明确接口契约
- 便于测试和扩展
- 支持鸭子类型（Duck Typing）
"""

from typing import Protocol, Dict, List
from generators.page_types import PageInfo


# ═══════════════════════════════════════════════════════════════
# CODE GENERATOR INTERFACES
# ═══════════════════════════════════════════════════════════════

class PageObjectGeneratorProtocol(Protocol):
    """Page Object 生成器接口"""
    
    def generate_page_object(self, page_info: PageInfo) -> str:
        """生成 Page Object 代码"""
        ...


class TestCaseGeneratorProtocol(Protocol):
    """测试用例生成器接口"""
    
    def generate_test_cases(self, page_info: PageInfo) -> str:
        """生成测试用例代码"""
        ...


class TestDataGeneratorProtocol(Protocol):
    """测试数据生成器接口"""
    
    def generate_test_data(self, page_info: PageInfo) -> Dict:
        """生成测试数据"""
        ...


class CodeGeneratorProtocol(Protocol):
    """代码生成器协调器接口"""
    
    def generate_all(self, page_info: PageInfo, output_dir: str = ".") -> Dict[str, str]:
        """生成所有文件（Page Object + 测试用例 + 测试数据）"""
        ...


# ═══════════════════════════════════════════════════════════════
# PLAN GENERATOR INTERFACES
# ═══════════════════════════════════════════════════════════════

class TestPlanFormatterProtocol(Protocol):
    """测试计划格式化器接口"""
    
    def _header(self, page_info: PageInfo) -> str:
        """生成标题和概述"""
        ...
    
    def _overview(self, page_info: PageInfo) -> str:
        """生成页面概述"""
        ...
    
    def _element_mapping(self, page_info: PageInfo) -> str:
        """生成元素映射"""
        ...


class TestPlanScenariosProtocol(Protocol):
    """测试计划场景生成器接口"""
    
    def _p0_tests(self, page_info: PageInfo) -> List[str]:
        """生成 P0 测试场景"""
        ...
    
    def _p1_tests(self, page_info: PageInfo) -> List[str]:
        """生成 P1 测试场景"""
        ...
    
    def _p2_tests(self, page_info: PageInfo) -> List[str]:
        """生成 P2 测试场景"""
        ...


class TestPlanGeneratorProtocol(Protocol):
    """测试计划生成器协调器接口"""
    
    def generate(self, page_info: PageInfo) -> str:
        """生成测试计划"""
        ...
    
    def save(self, content: str, file_path: str) -> None:
        """保存测试计划"""
        ...


# ═══════════════════════════════════════════════════════════════
# PAGE ANALYZER INTERFACES
# ═══════════════════════════════════════════════════════════════

class ElementExtractorProtocol(Protocol):
    """元素提取器接口"""
    
    def _get_elements(self, page) -> List:
        """提取所有元素"""
        ...
    
    def _get_inputs(self, page) -> List:
        """提取输入框"""
        ...
    
    def _get_buttons(self, page) -> List:
        """提取按钮"""
        ...
    
    def _get_links(self, page) -> List:
        """提取链接"""
        ...
    
    def _get_selects(self, page) -> List:
        """提取下拉框"""
        ...


class PageAnalyzerProtocol(Protocol):
    """页面分析器协调器接口"""
    
    def analyze(self, url: str, auth_callback=None) -> PageInfo:
        """分析页面"""
        ...
    
    def to_dict(self, page_info: PageInfo) -> Dict:
        """转换为字典"""
        ...
    
    def to_json(self, page_info: PageInfo, file_path: str = None) -> str:
        """转换为 JSON"""
        ...

