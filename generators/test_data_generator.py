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

from typing import Dict, Optional
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



def _safe_int(v: object) -> Optional[int]:
    try:
        if v is None:
            return None
        n = int(str(v).strip())
        return n if n > 0 else None
    except Exception:
        return None


def _infer_max_len(elem: PageElement) -> Optional[int]:
    """从 DOM attributes 推测 maxlength（若存在）。"""
    attrs = elem.attributes or {}
    return _safe_int(attrs.get("maxlength") or attrs.get("maxLength") or attrs.get("data-maxlength"))


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
            max_len = _infer_max_len(elem)
            
            type_data = {
                "email": {
                    "valid": "test@example.com",
                    "invalid": "invalid-email",
                    # 默认不制造“超长”，仅贴合 maxlength（或给一个合理上限）
                    "boundary": {"min": "a@b.c", "max": None},
                },
                "password": {
                    "valid": "ValidPass123!",
                    "invalid": "123",
                    "boundary": {"min": "a", "max": None},
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
                # 正常 case 用正常长度；边界也默认只到“合理 max”
                "boundary": {"empty": "", "min": "a", "max": None, "special": "@#$%^&*()"},
            }
            
            field_data = type_data.get(input_type, default)
            boundary = field_data.get("boundary")
            if isinstance(boundary, dict) and boundary.get("max") is None:
                cap = max_len or 64
                if input_type == "email":
                    suffix = "@t.com"
                    local_len = max(1, cap - len(suffix))
                    if max_len is None:
                        local_len = min(local_len, 48)
                    boundary["max"] = ("a" * local_len) + suffix
                else:
                    boundary["max"] = "x" * cap
            data["valid_data"][field] = field_data["valid"]
            data["invalid_data"][field] = field_data["invalid"]
            data["boundary_data"][field] = field_data["boundary"]
        
        return data
    
    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════
    
