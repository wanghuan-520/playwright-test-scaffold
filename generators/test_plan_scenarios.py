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

from typing import Dict, List
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



class TestPlanScenarios:
    """测试计划场景生成器"""

    def _p0_tests(self, page_info: PageInfo) -> List[str]:
        """P0 核心测试用例 - 增强版"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        
        # 通用：页面加载测试
        tests.append(f"""
#### TC-{tc}-001: 页面加载验证

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 页面加载 |

**测试描述**:
> 验证页面能正常加载，核心元素正确显示

**前置条件**:
- 系统正常运行
- 网络连接正常

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面: `{page_info.url}` | 📸 before_navigate |
| 2 | 等待页面加载完成 | 📸 after_navigate |
| 3 | 验证页面标题和核心元素 | 📸 loaded |

**预期目标**:
- [ ] ✓ 页面在 3 秒内加载完成
- [ ] ✓ 页面标题正确: "{page_info.title}"
- [ ] ✓ 核心元素可见""")
        
        # 页面类型特定测试
        type_tests = {
            "LOGIN": self._login_p0,
            "FORM": self._form_p0,
            "LIST": self._list_p0,
        }
        
        if page_info.page_type in type_tests:
            tests.append(type_tests[page_info.page_type](tc))
        
        return tests
    
    def _p1_tests(self, page_info: PageInfo) -> List[str]:
        """P1 重要测试用例 - 增强版"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        inputs = [e for e in page_info.elements if e.type == "input"]
        
        for i, elem in enumerate(inputs, 1):
            name = get_element_name(elem)
            tests.append(f"""
#### TC-{tc}-1{i:02d}: {name} 输入验证

| 属性 | 值 |
|------|-----|
| **优先级** | P1 |
| **类型** | validation |
| **Allure Story** | 输入验证 |
| **元素选择器** | `{elem.selector}` |

**测试描述**:
> 验证 {name} 字段的输入验证逻辑

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 测试空值输入 | 📸 empty_input |
| 3 | 测试边界值输入 | 📸 boundary |
| 4 | 测试特殊字符输入 | 📸 special_chars |

**测试数据**:
- 空值: `""`
- 正常值: 有效数据
- 边界值: 最小/最大长度
- 特殊字符: `<script>`, `' OR 1=1`

**预期目标**:
- [ ] ✓ 空值显示必填验证
- [ ] ✓ 正常值可接受
- [ ] ✓ 边界值正确处理
- [ ] ✓ 特殊字符被正确转义""")
        
        return tests
    
    def _p2_tests(self, page_info: PageInfo) -> List[str]:
        """P2 一般测试用例 - 增强版"""
        tc = get_tc_prefix_from_url(page_info.url)
        
        return [f"""
#### TC-{tc}-201: UI样式验证

| 属性 | 值 |
|------|-----|
| **优先级** | P2 |
| **类型** | ui |
| **Allure Story** | UI验证 |

**测试描述**:
> 验证页面 UI 样式和布局符合设计规范

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 截取全页截图 | 📸 fullpage (full_page=True) |

**预期目标**:
- [ ] ✓ 布局正确，元素对齐
- [ ] ✓ 响应式适配正常
- [ ] ✓ 样式符合设计规范

#### TC-{tc}-202: 键盘导航测试

| 属性 | 值 |
|------|-----|
| **优先级** | P2 |
| **类型** | accessibility |
| **Allure Story** | 可访问性 |

**测试描述**:
> 验证页面支持键盘导航，符合可访问性标准

**测试步骤**:

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 按 Tab 键遍历元素 | 📸 focus_visible |

**预期目标**:
- [ ] ✓ Tab 顺序正确
- [ ] ✓ 焦点指示器可见
- [ ] ✓ 可通过 Enter 激活按钮"""]
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE TYPE SPECIFIC TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def _login_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 正常登录流程

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 登录功能 |

**测试描述**:
> 验证使用有效凭证能成功登录系统

**前置条件**:
- 有效的测试账号
- 账号状态正常

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到登录页面 | 📸 initial |
| 2 | 填写用户名和密码 | 📸 filled |
| 3 | 点击登录按钮 | 📸 after_click |
| 4 | 验证登录结果 | 📸 result |

**预期目标**:
- [ ] ✓ 登录表单正确显示
- [ ] ✓ 输入凭证后无验证错误
- [ ] ✓ 成功跳转到目标页面
- [ ] ✓ Session 正确建立

#### TC-{tc}-003: 错误登录处理

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | exception |
| **Allure Story** | 登录功能 |

**测试描述**:
> 验证使用无效凭证登录时的错误处理

**测试场景**:
- 错误密码
- 不存在的用户名

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到登录页面 | 📸 initial |
| 2 | 输入无效凭证 | 📸 invalid_input |
| 3 | 点击登录并验证 | 📸 error_shown |

**预期目标**:
- [ ] ✓ 显示错误提示信息
- [ ] ✓ 不跳转到登录后页面
- [ ] ✓ 允许重新输入"""
    
    def _form_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 表单提交成功

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 表单提交 |

**测试描述**:
> 验证填写有效数据后表单能成功提交

**前置条件**:
- 页面正常加载
- 有效的测试数据

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到表单页面 | 📸 initial |
| 2 | 填写所有必填字段 | 📸 filled |
| 3 | 点击提交按钮 | 📸 before_submit |
| 4 | 验证提交结果 | 📸 result |

**预期目标**:
- [ ] ✓ 表单正确显示所有字段
- [ ] ✓ 填写数据后无验证错误
- [ ] ✓ 提交成功，数据保存
- [ ] ✓ 显示成功提示或跳转

#### TC-{tc}-003: 必填字段验证

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | validation |
| **Allure Story** | 表单验证 |

**测试描述**:
> 验证未填必填字段时的验证提示

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到表单页面 | 📸 initial |
| 2 | 直接点击提交 | 📸 before_submit |
| 3 | 验证错误提示 | 📸 error_shown |

**预期目标**:
- [ ] ✓ 必填字段显示验证错误
- [ ] ✓ 阻止表单提交
- [ ] ✓ 错误提示清晰可读"""
    
    def _list_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 列表数据加载

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 列表功能 |

**测试描述**:
> 验证列表页面数据正确加载和显示

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到列表页面 | 📸 initial |
| 2 | 等待数据加载 | 📸 data_loaded |

**预期目标**:
- [ ] ✓ 数据正确显示
- [ ] ✓ 分页信息正确
- [ ] ✓ 无空数据异常

#### TC-{tc}-003: 分页功能

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 列表功能 |

**测试描述**:
> 验证分页功能正常工作

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到列表页面 | 📸 page1 |
| 2 | 点击下一页 | 📸 page2 |
| 3 | 验证 URL 参数 | 📸 url_params |

**预期目标**:
- [ ] ✓ 分页切换正确
- [ ] ✓ URL 参数同步
- [ ] ✓ 数据内容正确更新"""
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _page_methods(self, page_info: PageInfo) -> str:
        """生成 Page Object 方法"""
        methods = []
        
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            
            if elem.type == "input":
                name = to_snake_case(elem.name or elem.id or "input")
                methods.append(f"""
    def fill_{name}(self, value: str) -> None:
        self.fill(self.{const}, value)""")
            
            elif elem.type == "button":
                text = to_snake_case(elem.text.strip() if elem.text else "button")
                methods.append(f"""
    def click_{text}(self) -> None:
        self.click(self.{const})""")
        
        return "\n".join(methods) if methods else "    pass"
    
