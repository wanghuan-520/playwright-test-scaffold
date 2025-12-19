# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Data Generator
# ═══════════════════════════════════════════════════════════════
"""
测试数据生成器 - 根据页面分析结果生成可执行的测试代码

职责：生成测试数据
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



class TestDataGenerator:
    """测试数据生成器"""

    def generate_test_data(self, page_info: PageInfo) -> Dict:
        """生成测试数据"""
        data = {
            "page_info": {"url": page_info.url, "type": page_info.page_type},
            "valid_data": {},
            "invalid_data": {},
            "boundary_data": {},
        }
        
        for elem in page_info.elements:
            if elem.type != "input":
                continue
            
            field = elem.name or elem.id or "field"
            input_type = elem.attributes.get("type", "text")
            
            type_data = {
                "email": {
                    "valid": "test@example.com",
                    "invalid": "invalid-email",
                    "boundary": {"min": "a@b.c", "max": "a" * 50 + "@example.com"},
                },
                "password": {
                    "valid": "ValidPass123!",
                    "invalid": "123",
                    "boundary": {"min": "a", "max": "a" * 100},
                },
                "tel": {
                    "valid": "13800138000",
                    "invalid": "abc",
                    "boundary": {"min": "1", "max": "1" * 20},
                },
                "number": {
                    "valid": "100",
                    "invalid": "abc",
                    "boundary": {"min": "0", "max": "999999999", "negative": "-1"},
                },
            }
            
            default = {
                "valid": "test_value",
                "invalid": "",
                "boundary": {"empty": "", "min": "a", "max": "x" * 256, "special": "@#$%^&*()"},
            }
            
            field_data = type_data.get(input_type, default)
            data["valid_data"][field] = field_data["valid"]
            data["invalid_data"][field] = field_data["invalid"]
            data["boundary_data"][field] = field_data["boundary"]
        
        return data
    
    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════
    
