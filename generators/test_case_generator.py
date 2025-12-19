# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Case Generator
# ═══════════════════════════════════════════════════════════════
"""
测试用例生成器 - 根据页面分析结果生成可执行的测试代码

职责：生成测试用例代码
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

from generators.page_analyzer import PageInfo, PageElement
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



from generators.test_case_templates import TestCaseTemplates


class TestCaseGenerator:
    """测试用例代码生成器"""
    
    def __init__(self):
        self.templates = TestCaseTemplates()
    """测试用例代码生成器"""

    def generate_test_cases(self, page_info: PageInfo) -> str:
        """生成测试用例代码 - 集成 Allure 报告增强"""
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        file_name = get_file_name_from_url(page_info.url)
        tc = get_tc_prefix_from_url(page_info.url)
        
        # 类型特定测试
        type_tests = self.templates._gen_type_tests(page_info, tc, file_name)
        
        return f'''# ═══════════════════════════════════════════════════════════════
# {class_name} Test Cases
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
"""
{class_name} 页面测试用例

Allure 报告增强:
- 测试描述: @allure.description()
- 步骤追踪: with allure.step() + 关键步骤前后截图
- 预期目标: allure.attach() 附件

运行命令:
    pytest tests/test_{file_name}.py -v
    pytest tests/test_{file_name}.py -v -m P0
    pytest tests/test_{file_name}.py --alluredir=allure-results && allure serve allure-results
"""

import pytest
import allure
from playwright.sync_api import Page
from pages.{file_name}_page import {class_name}Page
from utils.logger import TestLogger

logger = TestLogger("test_{file_name}")


# ═══════════════════════════════════════════════════════════════
# ALLURE REPORT HELPERS
# ═══════════════════════════════════════════════════════════════

def attach_expected(expectations: list[str]) -> None:
    \"\"\"附加预期目标到 Allure 报告\"\"\"
    content = "\\n".join(f"✓ {{exp}}" for exp in expectations)
    allure.attach(content, name="预期目标", attachment_type=allure.attachment_type.TEXT)


@allure.feature("{class_name}")
class Test{class_name}:
    \"\"\"
    {class_name} 页面测试类
    
    测试覆盖:
    - P0: 核心功能 (页面加载、主流程)
    - P1: 输入验证 (边界值、特殊字符)
    - P2: UI验证 (样式、布局)
    \"\"\"
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        \"\"\"测试 setup\"\"\"
        self.page = page
        self.{file_name}_page = {class_name}Page(page)
    
    # ═══════════════════════════════════════════════════════════════
    # P0 TESTS - 核心功能
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("页面加载")
    @allure.title("TC-{tc}-001: 页面加载验证")
    @allure.description(\"\"\"
    **测试目的**: 验证页面能正常加载，核心元素正确显示
    
    **前置条件**: 
    - 系统正常运行
    - 网络连接正常
    
    **测试步骤**:
    1. 导航到 {class_name} 页面
    2. 等待页面加载完成
    3. 验证页面标题和核心元素
    \"\"\")
    def test_p0_page_load(self):
        \"\"\"TC-{tc}-001: 页面加载验证\"\"\"
        logger.start()
        
        # 附加预期目标
        attach_expected([
            "页面在 3 秒内加载完成",
            "页面标题正确显示",
            "核心元素可见"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_before_navigate")
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_after_navigate")
        
        with allure.step("Step 2: 验证页面加载状态"):
            is_loaded = self.{file_name}_page.is_loaded()
            logger.checkpoint("页面加载完成", is_loaded)
            assert is_loaded, "页面未能正常加载"
        
        with allure.step("Step 3: 验证页面标题"):
            title = self.{file_name}_page.get_title()
            logger.checkpoint(f"页面标题: {{title}}", bool(title))
            assert title, "页面标题为空"
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_loaded")
        
        logger.end(success=True)
{type_tests}
    # ═══════════════════════════════════════════════════════════════
    # P1 TESTS - 输入验证
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-{tc}-101: 边界值测试")
    @allure.description(\"\"\"
    **测试目的**: 验证输入字段的边界值处理
    
    **测试数据**:
    - 最小长度值
    - 最大长度值
    - 空值
    \"\"\")
    def test_p1_boundary_values(self):
        \"\"\"TC-{tc}-101: 边界值测试\"\"\"
        logger.start()
        
        attach_expected([
            "最小长度输入被接受",
            "最大长度输入被接受",
            "空值显示验证错误"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_101_initial")
        
        with allure.step("Step 2: 测试边界值"):
            # TODO: 实现边界值测试
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_101_boundary")
        
        logger.end(success=True)
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-{tc}-102: 特殊字符测试")
    @allure.description(\"\"\"
    **测试目的**: 验证输入字段对特殊字符的处理
    
    **测试数据**:
    - SQL 注入字符: ' OR 1=1 --
    - XSS 字符: <script>alert(1)</script>
    - Unicode 字符: 中文、emoji
    \"\"\")
    def test_p1_special_characters(self):
        \"\"\"TC-{tc}-102: 特殊字符测试\"\"\"
        logger.start()
        
        attach_expected([
            "特殊字符被正确转义",
            "不触发 XSS/SQL 注入",
            "Unicode 字符正常显示"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_102_initial")
        
        with allure.step("Step 2: 测试特殊字符"):
            # TODO: 实现特殊字符测试
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_102_special")
        
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P2 TESTS - UI验证
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P2
    @pytest.mark.ui
    @allure.story("UI验证")
    @allure.title("TC-{tc}-201: UI样式验证")
    @allure.description(\"\"\"
    **测试目的**: 验证页面 UI 样式和布局
    
    **检查项**:
    - 元素对齐和间距
    - 颜色和字体
    - 响应式布局
    \"\"\")
    def test_p2_ui_styling(self):
        \"\"\"TC-{tc}-201: UI样式验证\"\"\"
        logger.start()
        
        attach_expected([
            "布局正确，元素对齐",
            "样式符合设计规范",
            "响应式适配正常"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
        
        with allure.step("Step 2: 截取全页截图"):
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_201_fullpage", full_page=True)
        
        logger.end(success=True)
'''
    
    # ═══════════════════════════════════════════════════════════════
    # TEST DATA GENERATOR
    # ═══════════════════════════════════════════════════════════════
    

