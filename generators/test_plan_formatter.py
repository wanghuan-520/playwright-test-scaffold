# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Code Generator
# ═══════════════════════════════════════════════════════════════
"""
测试代码生成器 - 根据页面分析结果生成可执行的测试代码

生成物：
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



class TestPlanFormatter:
    """测试计划格式化器"""

    def _infer_max_len(self, elem: PageElement):
        # DOM attributes 可能来自不同风格：maxlength / maxLength
        try:
            v = elem.attributes.get("maxlength") or elem.attributes.get("maxLength") or elem.attributes.get("data-maxlength")
            if v is None:
                return None
            n = int(str(v).strip())
            return n if n > 0 else None
        except Exception:
            return None

    def _header(self, page_info: PageInfo) -> str:
        """文档头部"""
        page_name = get_page_name_from_url(page_info.url)
        return f"""# {page_name} Test Plan

> 自动生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 页面类型: {page_info.page_type}
> 生成工具: Playwright Test Scaffold"""
    
    def _overview(self, page_info: PageInfo) -> str:
        """页面概述"""
        page_name = get_page_name_from_url(page_info.url)
        dimensions = self.TEST_DIMENSIONS.get(page_info.page_type, ["functional"])
        
        return f"""## 1. Page Overview

| Attribute | Value |
|-----------|-------|
| **Page Name** | {page_name} |
| **URL** | `{page_info.url}` |
| **Title** | {page_info.title} |
| **Type** | {page_info.page_type} |
| **Test Dimensions** | {', '.join(dimensions)} |

### 1.1 Page Description

{get_page_description(page_info.page_type)}"""
    
    def _element_mapping(self, page_info: PageInfo) -> str:
        """元素映射表"""
        rows = []
        for element in page_info.elements:
            name = get_element_name(element)
            desc = get_element_description(element)
            rows.append(f"| {name} | {desc} | `{element.selector}` | {element.type} |")
        
        table = "\n".join(rows) if rows else "| (No elements found) | - | - | - |"
        
        return f"""## 2. Element Mapping

| Element Name | Description | Selector | Type |
|--------------|-------------|----------|------|
{table}"""
    
    def _test_cases(self, page_info: PageInfo) -> str:
        """测试用例"""
        cases = []
        
        cases.append("### 3.1 P0 - Critical Tests (核心功能)")
        cases.extend(self._p0_tests(page_info))
        
        cases.append("\n### 3.2 P1 - High Priority Tests (重要功能)")
        cases.extend(self._p1_tests(page_info))
        
        cases.append("\n### 3.3 P2 - Medium Priority Tests (一般功能)")
        cases.extend(self._p2_tests(page_info))
        
        return f"""## 3. Test Cases

{chr(10).join(cases)}"""
    
    def _test_data(self, page_info: PageInfo) -> str:
        """测试数据设计"""
        inputs = [e for e in page_info.elements if e.type == "input"]
        
        valid, invalid, boundary = {}, {}, {}
        
        for elem in inputs:
            field = elem.name or elem.id or "field"
            attr_type = elem.attributes.get("type", "text")
            max_len = self._infer_max_len(elem)
            
            if attr_type == "email":
                valid[field] = "test@example.com"
                invalid[field] = "invalid-email"
                # 边界示例：尽量贴合 maxlength；未推导时给一个“正常偏长”的样例即可
                cap = max_len or 64
                suffix = "@t.com"
                local_len = max(1, cap - len(suffix))
                if max_len is None:
                    local_len = min(local_len, 48)
                boundary[field] = ("a" * local_len) + suffix
            elif attr_type == "password":
                valid[field] = "ValidPass123!"
                invalid[field] = "123"
                boundary[field] = "a" * (max_len or 64)
            elif attr_type == "tel":
                valid[field] = "13800138000"
                invalid[field] = "abc"
                boundary[field] = "1" * 20
            else:
                valid[field] = "test_value"
                invalid[field] = ""
                # 不默认写超长；优先用 maxlength，否则 64
                boundary[field] = "x" * (max_len or 64)
        
        return f"""## 4. Test Data Design

### 4.1 Valid Data
```json
{json.dumps(valid, indent=2, ensure_ascii=False)}
```

### 4.2 Invalid Data
```json
{json.dumps(invalid, indent=2, ensure_ascii=False)}
```

### 4.3 Boundary Data
```json
{json.dumps(boundary, indent=2, ensure_ascii=False)}
```"""
    
    def _page_object_skeleton(self, page_info: PageInfo) -> str:
        """Page Object 骨架代码 - 带 Allure 集成"""
        page_name = get_page_name_from_url(page_info.url)
        class_name = to_class_name(page_name)
        
        # 选择器代码
        selectors = []
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            selectors.append(f'    {const} = "{elem.selector}"')
        selectors_code = "\n".join(selectors) if selectors else "    # No elements found"
        
        # 方法代码
        methods = self._page_methods(page_info)
        
        indicator = page_info.elements[0].selector if page_info.elements else "body"
        
        return f"""## 5. Page Object Skeleton

> **注意**: 此骨架已集成 Allure 报告支持，截图会自动附加到报告

```python
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class {class_name}Page(BasePage):
    \"\"\"
    {page_name} 页面对象
    URL: {page_info.url}
    Type: {page_info.page_type}
    
    Allure 集成:
    - take_screenshot() 自动附加截图到报告
    - 所有操作方法记录日志
    \"\"\"
    
    # SELECTORS
{selectors_code}
    
    page_loaded_indicator = "{indicator}"
    
    # NAVIGATION
    def navigate(self) -> None:
        \"\"\"导航到页面\"\"\"
        logger.info(f"导航到 {class_name} 页面")
        self.goto("{page_info.url}")
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        \"\"\"检查页面是否加载完成\"\"\"
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ACTIONS
{methods}
    
    # SCREENSHOT HELPERS (继承自 BasePage)
    # take_screenshot(name, full_page=False) - 截图并附加到 Allure 报告
```

### 5.1 Allure 步骤使用示例

```python
import allure

def test_example(self):
    # 附加预期目标
    attach_expected([
        "预期目标 1",
        "预期目标 2"
    ])
    
    # 使用 allure.step 包装关键步骤
    with allure.step("Step 1: 操作描述"):
        self.page.take_screenshot("step1_before")
        # 执行操作
        self.page.take_screenshot("step1_after")
    
    with allure.step("Step 2: 验证结果"):
        assert condition, "断言失败信息"
        self.page.take_screenshot("step2_result")
```"""
    
    def _notes(self, page_info: PageInfo) -> str:
        """实施说明 - 包含 Allure 报告指南"""
        file_name = to_snake_case(get_page_name_from_url(page_info.url))
        auth = "No" if not requires_auth(page_info.page_type) else "Yes (likely)"
        
        return f"""## 6. Implementation Notes

### 6.1 File Locations
| 文件类型 | 路径 |
|----------|------|
| Page Object | `pages/{file_name}_page.py` |
| Test File | `tests/test_{file_name}.py` |
| Test Data | `test-data/{file_name}_data.json` |
| Screenshots | `screenshots/tc_*` |

### 6.2 Execution Commands

```bash
# 运行测试
pytest tests/test_{file_name}.py -v

# 运行 P0 用例
pytest tests/test_{file_name}.py -v -m P0

# 生成 Allure 报告
pytest tests/test_{file_name}.py --alluredir=allure-results
allure open allure-report
```

### 6.3 Allure 报告增强

生成的测试代码包含以下 Allure 特性:

| 特性 | 用途 |
|------|------|
| `@allure.description()` | 测试描述 (目的、前置条件) |
| `with allure.step()` | 步骤追踪 (支持嵌套) |
| `take_screenshot()` | 关键步骤截图 |
| `attach_expected()` | 预期目标附件 |

### 6.4 截图命名规范

```
tc_{{tc_prefix}}_{{case_number}}_{{timing}}.png

示例:
- tc_{file_name.lower()}_001_initial.png    # 初始状态
- tc_{file_name.lower()}_001_after_click.png # 点击后
- tc_{file_name.lower()}_001_result.png     # 最终结果
```

### 6.5 Dependencies
- Requires authentication: {auth}

---
*Generated by Playwright Test Scaffold - Enhanced Allure Report*"""
    
    # ═══════════════════════════════════════════════════════════════
    # TEST CASE GENERATORS
    # ═══════════════════════════════════════════════════════════════
