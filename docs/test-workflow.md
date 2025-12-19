# 🎯 完整测试流程详解

本文档详细说明 Playwright Test Scaffold 的完整测试流程，从用户输入到报告生成的每一个步骤。

---

## 📋 目录

- [流程概览](#流程概览)
- [阶段 1: 页面分析与代码生成](#阶段-1-页面分析与代码生成)
- [阶段 2: 自动测试执行](#阶段-2-自动测试执行)
- [阶段 3: 报告查看与分析](#阶段-3-报告查看与分析)
- [核心框架支撑](#核心框架支撑)
- [数据流转](#数据流转)

---

## 流程概览

```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║                          用户输入："帮我测试修改密码页面"                                      ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
                                          │
                                          ▼
                              读取 AI 规则系统（.cursor/rules/）
                              ├─ core/project-overview.md
                              ├─ project-specific/aevatar-station.md
                              ├─ workflow/analysis-and-generation.md
                              └─ workflow/test-execution.md
                                          │
                                          ▼
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                        阶段 1: 页面分析与代码生成（2-3 分钟）                                 ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
                                          │
                                          ▼
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                        阶段 2: 自动测试执行（1-2 分钟）                                       ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
                                          │
                                          ▼
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                        阶段 3: 报告查看与分析（自动打开）                                     ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 阶段 1: 页面分析与代码生成

### Step 1: 读取项目配置

```
读取 config/project.yaml
├─ project_name: "Aevatar Agent Station"
├─ repositories:
│   ├─ frontend: https://github.com/xxx/frontend
│   └─ backend: https://github.com/xxx/backend
├─ services:
│   ├─ frontend: https://localhost:3000
│   └─ backend: https://localhost:44320
└─ tech_stack:
    ├─ frontend: Next.js 15 + React 19 + TypeScript
    └─ backend: ABP Framework 8.3 + .NET Aspire
```

### Step 2: 根据页面 URL 推断代码位置

```
输入: "/admin/profile/change-password"
  ↓
推断代码位置:
  ├─ src/pages/admin/profile/ChangePassword.tsx
  ├─ src/pages/admin/profile/change-password/page.tsx
  └─ src/views/admin/profile/ChangePassword/index.tsx
```

### Step 3A: GitHub 代码分析（静态分析）

```
查询 GitHub 仓库
  ↓
找到 src/pages/admin/profile/ChangePassword.tsx
  ↓
分析代码结构:
  ├─ 表单字段:
  │   ├─ currentPassword (type: password, required: true)
  │   ├─ newPassword (type: password, required: true)
  │   └─ confirmPassword (type: password, required: true)
  │
  ├─ 验证规则:
  │   ├─ 长度: 8-20 字符
  │   ├─ 必须包含: 大写字母 + 小写字母 + 数字
  │   └─ 新密码不能与当前密码相同
  │
  ├─ API 接口:
  │   ├─ URL: POST /api/user/change-password
  │   ├─ 请求参数: { currentPassword, newPassword, confirmPassword }
  │   └─ 响应: { success, message }
  │
  └─ 业务逻辑:
      ├─ 提交前验证
      ├─ API 调用
      ├─ 成功提示
      └─ 错误处理
```

**提取的信息**:
- ✅ 表单字段定义
- ✅ 验证规则（正则、长度限制）
- ✅ API 接口（请求方法、参数、响应）
- ✅ 业务逻辑（条件判断、流程分支）

### Step 3B: Playwright MCP 分析（动态分析）

```
检查服务状态
  ├─ curl https://localhost:3000 → ✅ HTTP 200
  └─ curl https://localhost:44320/api/health → ✅ HTTP 200
  ↓
服务已启动，开始 MCP 分析
  ↓
browser_navigate
  └─ 导航到 https://localhost:3000/admin/profile/change-password
  ↓
browser_snapshot
  └─ 获取页面可访问性快照
      ├─ 元素: 3 个 input[type="password"]
      ├─ 元素: 1 个 button[type="submit"]
      └─ 元素状态: required=true, disabled=false
  ↓
browser_evaluate
  └─ 执行 JavaScript 提取元素信息
      ├─ document.querySelectorAll('input[type="password"]')
      ├─ document.querySelector('button[type="submit"]')
      └─ 元素属性、状态、位置
```

**提取的信息**:
- ✅ 实际渲染的元素
- ✅ 元素选择器（#currentPassword, #newPassword...）
- ✅ 可访问性信息（role, name, state）
- ✅ 元素的实际状态（disabled, required, visible）

### Step 4: 合并分析结果

```
MCP 分析结果（实际元素）
  +
GitHub 分析结果（业务逻辑）
  ↓
生成完整的 PageInfo 对象:
  ├─ page_url: "/admin/profile/change-password"
  ├─ page_name: "ChangePasswordPage"
  ├─ elements: [
  │   {
  │     name: "currentPassword",
  │     selector: "#currentPassword",
  │     type: "password",
  │     required: true,
  │     validation: { minLength: 8, maxLength: 20 }
  │   },
  │   {
  │     name: "newPassword",
  │     selector: "#newPassword",
  │     type: "password",
  │     required: true,
  │     validation: { 
  │       minLength: 8, 
  │       maxLength: 20,
  │       requireUppercase: true,
  │       requireLowercase: true,
  │       requireDigit: true
  │     }
  │   },
  │   ...
  │ ]
  └─ functions: [
      "change_password(current, new, confirm)",
      "verify_success()",
      "verify_error()"
    ]
```

### Step 5: 生成测试代码

#### 5.1 生成 Page Object

```python
# pages/change_password_page.py

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ChangePasswordPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS - 根据 MCP 分析的实际元素生成
    # ═══════════════════════════════════════════════════════════════
    
    CURRENT_PASSWORD_INPUT = "#currentPassword"
    NEW_PASSWORD_INPUT = "#newPassword"
    CONFIRM_PASSWORD_INPUT = "#confirmPassword"
    SUBMIT_BUTTON = "button[type='submit']"
    
    URL = "/admin/profile/change-password"
    page_loaded_indicator = "#currentPassword"
    
    def navigate(self) -> None:
        """导航到修改密码页面"""
        logger.info("导航到修改密码页面")
        self.goto(self.URL)
        self.wait_for_page_load()
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS - 根据业务逻辑生成
    # ═══════════════════════════════════════════════════════════════
    
    def change_password(self, current: str, new: str, confirm: str) -> None:
        """修改密码"""
        self.fill(self.CURRENT_PASSWORD_INPUT, current)
        self.fill(self.NEW_PASSWORD_INPUT, new)
        self.fill(self.CONFIRM_PASSWORD_INPUT, confirm)
        self.click(self.SUBMIT_BUTTON)
```

#### 5.2 生成测试用例

```python
# tests/test_change_password.py

import pytest
import allure
from pages.change_password_page import ChangePasswordPage
from utils.logger import TestLogger

@allure.feature("修改密码")
class TestChangePassword:
    
    # ═══════════════════════════════════════════════════════════════
    # P0 测试 - 核心功能（4个）
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P0
    @allure.story("密码修改")
    @allure.title("test_p0_change_password_success")
    def test_p0_change_password_success(self, page, test_account):
        """P0: 正常修改密码"""
        logger = TestLogger("test_p0_change_password_success")
        logger.start()
        
        # 登录
        self._login(page, test_account)
        
        # 导航到页面
        change_password_page = ChangePasswordPage(page)
        change_password_page.navigate()
        with allure.step("导航到修改密码页面"):
            change_password_page.take_screenshot("step_navigate", full_page=True)
        
        # 修改密码
        current_password = test_account["password"]
        new_password = "NewPass123!"
        change_password_page.change_password(current_password, new_password, new_password)
        
        # 等待 toast 出现
        page.wait_for_timeout(500)
        # ... toast 等待逻辑 ...
        
        with allure.step("点击保存按钮"):
            change_password_page.take_screenshot("step_click_save", full_page=True)
        
        logger.checkpoint("密码修改成功", True)
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P1 测试 - 重要功能（8个）
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P1
    @allure.story("密码验证")
    @allure.title("test_p1_password_too_short")
    def test_p1_password_too_short(self, page, test_account):
        """P1: 密码太短 - 验证 ABP RequiredLength 规则"""
        # ... 测试逻辑 ...
```

**生成的测试用例**:
- ✅ **P0 测试**（4个）: 页面加载 + 主流程 + 必填字段验证
- ✅ **P1 测试**（8个）: 边界值 + 格式验证 + API 错误处理
- ✅ **P2 测试**（1个）: UI 交互

---

## 阶段 2: 自动测试执行

### Step 0: 清理旧数据（必须）⭐

```bash
# 自动执行 clean_old_test_data()

rm -rf allure-results/    # 删除旧的测试结果数据
rm -rf allure-report/     # 删除旧的 HTML 报告
rm -rf screenshots/       # 删除旧的测试截图

mkdir allure-results/     # 重建目录
mkdir screenshots/        # 重建目录

✅ 已清理旧的测试结果: allure-results/
✅ 已清理旧的测试报告: allure-report/
✅ 已清理旧的测试截图: screenshots/
✅ 已创建新的测试数据目录
```

**为什么必须清理？**
- ✅ 避免数据混淆（旧的和新的混在一起）
- ✅ 确保结果准确（每次测试独立）
- ✅ 便于问题定位（只看本次测试）

### Step 1: 检查服务状态

```bash
# 自动执行 ServiceChecker.check()

curl -k https://localhost:3000 -I
curl -k https://localhost:44320/api/health -I

═══════════════════════════════════════════════════════
服务状态检查
═══════════════════════════════════════════════════════
✅ frontend: https://localhost:3000 (HTTP 200)
✅ backend: https://localhost:44320 (HTTP 200)
═══════════════════════════════════════════════════════
✅ 所有服务正常运行
```

**如果服务未启动**:
```
❌ frontend: https://localhost:3000 (连接失败)
✅ backend: https://localhost:44320 (HTTP 200)
═══════════════════════════════════════════════════════
❌ 部分服务不可用

⚠️ 请先启动前端服务:
   cd /path/to/frontend
   npm run dev

等待服务启动中...（最多 60 秒）
```

### Step 2: 运行 pytest

```bash
pytest tests/test_change_password.py -v --alluredir=allure-results

# 测试执行过程:
# 1. fixtures.py - setup_browser()
#    └─ 创建 Playwright 浏览器实例
#
# 2. fixtures.py - test_account()
#    ├─ 清理前：解锁账号、重置状态
#    ├─ 分配账号：标记 in_use=True
#    └─ 返回账号信息
#
# 3. 执行测试方法
#    ├─ _login(page, test_account)
#    ├─ 导航到页面
#    ├─ 填写表单
#    ├─ 点击按钮
#    ├─ 验证结果
#    └─ 每个步骤截图（全屏）
#
# 4. fixtures.py - cleanup()
#    ├─ 清理后：释放账号、恢复密码
#    └─ 标记 in_use=False
```

**运行时支撑**:

```
core/fixtures.py（测试钩子）
├─ setup_browser() - 创建浏览器实例
├─ test_account() - 数据隔离
│   ├─ 自动分配独立账号
│   ├─ 测试前：解锁 + 重置状态
│   └─ 测试后：释放 + 恢复密码
└─ cleanup() - 失败时标记状态

core/base_page.py（页面基类）
├─ PageActions - 操作封装（fill, click...）
├─ PageWaits - 等待策略（智能等待）
└─ PageUtils - 工具函数（截图、验证...）

utils/logger.py（日志系统）
├─ logger.start() - 测试开始
├─ logger.step() - 步骤日志
├─ logger.checkpoint() - 检查点
└─ logger.end() - 测试结束
```

### Step 3: 收集测试结果

```
解析 pytest 输出:
├─ 总测试数: 13
├─ ✅ 通过: 11 (85%)
├─ ❌ 失败: 2 (15%)
│   ├─ test_p1_password_too_short
│   │   └─ 原因: 后端未启用 RequiredLength 验证规则
│   └─ test_p1_same_as_current
│       └─ 原因: 后端未启用"新密码不能与当前相同"规则
└─ ⏱️  执行时间: 45.3 秒
```

### Step 4: 生成 Allure 报告

```
allure-results/（原始数据）
├─ xxx-result.json（测试结果）
├─ xxx-container.json（测试容器）
├─ xxx-attachment.txt（日志附件）
└─ screenshots/（截图）
    ├─ step_navigate.png
    ├─ step_fill_form.png
    ├─ step_click_save.png
    └─ step_verify_error.png
```

### Step 5: 自动打开报告（必须）✨

```bash
allure serve allure-results

# 自动执行:
# 1. 生成 HTML 报告
# 2. 启动本地服务器（随机端口）
# 3. 自动打开默认浏览器
# 4. 显示地址: http://localhost:xxxxx

✅ 报告服务器启动成功
✅ 浏览器已自动打开
   → http://localhost:54321
```

### Step 6: 反馈测试结果摘要

```
═══════════════════════════════════════════════════════
测试完成！
═══════════════════════════════════════════════════════

📊 测试结果概览:
- 总测试数: 13
- ✅ 通过: 11 (85%)
- ❌ 失败: 2 (15%)

⏱️  执行时间: 45.3 秒

❌ 失败的测试详情:
1. test_p1_password_too_short
   └─ 原因: 后端未启用 RequiredLength 验证规则
   └─ 建议: 检查后端 ABP 配置或调整测试断言

2. test_p1_same_as_current
   └─ 原因: 后端未启用"新密码不能与当前相同"规则
   └─ 建议: 确认业务需求，如不需要此规则可删除此测试

📝 Allure 报告已自动打开:
   → http://localhost:54321
   → 点击失败的测试查看完整日志和截图
```

---

## 阶段 3: 报告查看与分析

### 浏览器自动打开 Allure 报告

```
Allure Report (HTML)
├─ Overview（概览）
│   ├─ 测试总数: 13
│   ├─ 通过率: 85%
│   ├─ 失败率: 15%
│   ├─ 执行时间: 45.3s
│   └─ 优先级分布:
│       ├─ P0: 4 个（100% 通过）
│       ├─ P1: 8 个（75% 通过）
│       └─ P2: 1 个（100% 通过）
│
├─ Suites（测试套件）
│   └─ TestChangePassword
│       ├─ ✅ test_p0_page_load
│       ├─ ✅ test_p0_change_password_success
│       ├─ ✅ test_p0_current_password_required
│       ├─ ✅ test_p0_new_password_required
│       ├─ ❌ test_p1_password_too_short
│       ├─ ✅ test_p1_password_too_long
│       ├─ ✅ test_p1_password_missing_uppercase
│       ├─ ✅ test_p1_password_missing_lowercase
│       ├─ ✅ test_p1_password_missing_digit
│       ├─ ✅ test_p1_password_missing_special_char
│       ├─ ✅ test_p1_passwords_mismatch
│       ├─ ❌ test_p1_same_as_current
│       └─ ✅ test_p2_password_visibility
│
├─ Behaviors（功能分组）
│   ├─ 修改密码
│   │   ├─ test_p0_change_password_success
│   │   └─ test_p1_same_as_current
│   ├─ 密码验证
│   │   ├─ test_p0_current_password_required
│   │   ├─ test_p0_new_password_required
│   │   ├─ test_p1_password_too_short
│   │   ├─ test_p1_password_too_long
│   │   └─ ...
│   └─ UI 交互
│       └─ test_p2_password_visibility
│
├─ Timeline（时间轴）
│   └─ 显示每个测试的执行时间和并发情况
│
└─ Packages（包结构）
    └─ tests/test_change_password.py
```

### 点击测试查看详情

```
测试: test_p1_password_too_short
状态: ❌ FAILED
执行时间: 3.2s

测试步骤:
├─ ✅ Step 1: 导航到修改密码页面
│   └─ 📸 step_navigate.png（全屏截图）
│
├─ ✅ Step 2: 填写密码信息
│   └─ 📸 step_fill_password.png（全屏截图）
│
├─ ✅ Step 3: 点击保存按钮
│   └─ 📸 step_click_save.png（全屏截图）
│
└─ ❌ Step 4: 验证错误提示
    ├─ 📸 step_verify_error.png（全屏截图）
    └─ 失败原因:
        AssertionError: 应该显示"密码太短"错误
        但页面未显示任何错误消息

日志输出:
[INFO] test_p1_password_too_short: 测试开始
[INFO] test_p1_password_too_short: 导航到修改密码页面
[INFO] test_p1_password_too_short: 填写密码: Abc12!（6字符）
[INFO] test_p1_password_too_short: 点击保存按钮
[INFO] test_p1_password_too_short: 等待错误消息显示
[ERROR] test_p1_password_too_short: 未检测到验证错误
[INFO] test_p1_password_too_short: 测试结束 - 失败

AI 建议:
1. 检查后端 ABP 配置是否启用了 RequiredLength 规则
2. 确认最小长度要求（通常为 8 字符）
3. 如果后端未启用此规则，可以删除此测试用例
4. 或者修改测试断言，只验证前端提示（如果有）
```

---

## 核心框架支撑

### BasePage（页面基类）

```python
from core.page_actions import PageActions
from core.page_waits import PageWaits
from core.page_utils import PageUtils

class BasePage(PageActions, PageWaits, PageUtils):
    """Page Object 基类（协调器模式）"""
    
    def __init__(self, page):
        self.page = page
    
    # 继承所有操作、等待、工具方法
    # fill(), click(), wait_for_selector(), take_screenshot()...
```

**职责分离**:
- `PageActions` - 操作封装（fill, click, select...）
- `PageWaits` - 等待策略（智能等待、超时重试）
- `PageUtils` - 工具函数（截图、验证、错误检测...）

### Fixtures（测试钩子）

```python
@pytest.fixture
def test_account(request):
    """为每个测试用例分配独立的测试账号"""
    test_name = request.node.name
    
    # 测试前：清理 + 分配
    data_manager = DataManager()
    data_manager.cleanup_before_test(test_name)
    account = data_manager.get_test_account(test_name)
    
    yield account
    
    # 测试后：清理 + 释放
    success = request.node.rep_call.passed if hasattr(request.node, 'rep_call') else True
    data_manager.cleanup_after_test(test_name, success)
```

**数据隔离机制**:
- ✅ 测试前：解锁账号、重置状态
- ✅ 测试中：标记使用中（in_use=True）
- ✅ 测试后：释放账号、恢复密码

### TestLogger（日志系统）

```python
logger = TestLogger("test_p0_change_password_success")
logger.start()
logger.step("导航到修改密码页面")
logger.checkpoint("页面加载成功", True)
logger.end(success=True)

# 输出:
# [INFO] test_p0_change_password_success: 测试开始
# [INFO] test_p0_change_password_success: 导航到修改密码页面
# [INFO] test_p0_change_password_success: ✅ 页面加载成功
# [INFO] test_p0_change_password_success: 测试结束 - 成功
```

---

## 数据流转

```
用户输入："帮我测试修改密码页面"
  ↓
config/project.yaml（配置中心）
  ├─ 仓库地址（用于 GitHub 分析）
  ├─ 服务地址（用于 MCP 分析）
  └─ 技术栈信息（用于 AI 理解）
  ↓
.cursor/rules/（AI 规则系统）
  ├─ core/project-overview.md（项目定位）
  ├─ project-specific/aevatar-station.md（项目规则）
  ├─ workflow/analysis-and-generation.md（分析流程）
  └─ workflow/test-execution.md（执行流程）
  ↓
generators/（代码生成引擎）
  ├─ page_analyzer.py
  │   └─ 双重分析 → PageInfo
  ├─ page_object_generator.py
  │   └─ PageInfo → pages/change_password_page.py
  └─ test_case_generator.py
      └─ PageInfo → tests/test_change_password.py
  ↓
test-data/accounts.yaml（测试数据）
  └─ 为每个测试用例分配独立账号
  ↓
pytest + core/（测试框架）
  ├─ fixtures.py（测试钩子）
  ├─ BasePage（页面基类）
  └─ TestLogger（日志系统）
  ↓
allure-results/（原始数据）
  ├─ xxx-result.json
  ├─ xxx-container.json
  └─ screenshots/
  ↓
allure serve（生成 HTML）
  ↓
浏览器自动打开 ✨
  └─ http://localhost:xxxxx
```

---

## 总结

### 核心特性

1. **双重分析**（准确性）
   - GitHub 代码分析（静态）+ Playwright MCP 分析（动态）
   - 互补 → 最准确的测试用例

2. **全自动化**（零操作）
   - 用户一句话 → 分析 → 生成 → 执行 → 报告（自动打开）
   - 无需任何手动命令

3. **数据隔离**（独立性）
   - 每个测试用例使用独立账号
   - 自动分配、清理、恢复

4. **自动清理**（干净）
   - 每次测试前自动清理旧数据
   - 报告和截图只显示本次测试

5. **完整报告**（可视化）
   - Allure HTML 报告
   - 详细步骤、截图、日志
   - 自动打开浏览器

### 时间分布

| 阶段 | 时间 | 主要工作 |
|------|------|----------|
| 阶段 1 | 2-3 分钟 | 页面分析 + 代码生成 |
| 阶段 2 | 1-2 分钟 | 测试执行（13 个测试） |
| 阶段 3 | 自动 | 报告生成 + 浏览器打开 |
| **总计** | **3-5 分钟** | **全自动完成** |

---

**从一句话到完整测试报告，只需 3-5 分钟！** 🚀
