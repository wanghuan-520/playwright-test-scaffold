# Playwright Test Scaffold - Architecture

> AI 驱动的自动化测试脚手架 - 架构文档

## 使用方式

本项目的核心是 **“URL → 动态分析 → 全量生成 → 执行 → 报告”** 的可复现链路。

你可以用自然语言（`tools/ai_command_router.py`）或直接用 CLI（`tools/url_flow.py`）触发，框架会自动完成：
- 检查/复用登录态（`storage_state`）
- **Playwright 动态分析**（`generators/page_analyzer.py`）：真实打开页面，提取元素/可访问性快照（可选落盘）
- 生成 Page Object（`pages/*_page.py`）
- 生成测试套件（`tests/**`，含 P0/P1/P2/security 等）
- 执行 pytest（默认只跑该 URL 对应套件目录）
- 生成 Allure 报告（可选）

## 页面功能分析流程

```
页面 URL → Playwright 动态分析 → PageInfo → 代码生成（PO + tests + test-data）
```

| 分析维度 | 关注点 |
|----------|--------|
| 表单字段 | 输入框、下拉框、必填/可选 |
| 选择器 | role/name/id/name 属性、可见性、可交互性 |
| 请求行为 | 点击保存等动作是否触发写请求、是否出现 5xx/错误 UI |
| 规则推导 | 规则缺失时 **自动跳过**（拒绝凭猜生成边界矩阵） |

## 目录结构

```
playwright-test-scaffold/
├── conftest.py                   # pytest 根配置
├── pytest.ini                    # pytest 配置
├── requirements.txt              # 依赖清单
│
├── tools/                        # 官方可执行入口（强制走完整流程）
│   ├── __init__.py
│   ├── url_flow.py               # URL → 分析 → 全量生成 → pytest → allure
│   └── ai_command_router.py      # 自然语言/URL → url_flow → 自动打开 Allure
│
├── config/
│   └── project.yaml              # 项目配置中心（仓库/服务/数据）
│
├── core/                         # 核心框架层
│   ├── __init__.py
│   ├── base_page.py              # Page Object 基类（协调器）
│   ├── page_actions.py           # 页面操作封装
│   ├── page_waits.py             # 页面等待策略
│   ├── page_utils.py             # 页面工具函数
│   └── fixtures.py                # pytest fixtures
│
├── generators/                   # 代码生成引擎
│   ├── __init__.py               # 模块导出入口
│   │
│   ├── 数据模型层
│   │   └── page_types.py         # PageElement, PageInfo 数据类
│   │
│   ├── 页面分析层
│   │   ├── page_analyzer.py      # 页面分析器（协调器）
│   │   └── element_extractor.py  # 元素提取器
│   │
│   ├── 代码生成层
│   │   ├── test_code_generator.py      # 测试代码生成器（协调器）
│   │   ├── page_object_generator.py    # Page Object 生成器
│   │   ├── test_case_generator.py      # 测试用例生成器
│   │   ├── test_case_templates.py      # DEPRECATED: 历史遗留 TODO 模板（禁止作为生成路径）
│   │   └── test_data_generator.py      # 测试数据生成器
│   │
│   ├── 文档生成层
│   │   ├── test_plan_generator.py      # 测试计划生成器（协调器）
│   │   ├── test_plan_formatter.py      # 测试计划格式化器
│   │   └── test_plan_scenarios.py      # 测试计划场景生成器
│   │
│   └── 工具层
│       └── utils.py              # 公共工具函数（命名转换等）
│
├── utils/                        # 工具模块
│   ├── __init__.py
│   ├── config.py                 # 配置管理器（单例模式）
│   ├── logger.py                 # 日志系统
│   ├── rules_loader.py           # 规则上下文加载器（.cursor/rules → reports/rules_context.md）
│   ├── rules_engine.py           # 可执行规则引擎（docs/rules.yaml → RulesConfig）
│   └── service_checker.py        # 服务健康检查
│
├── pages/                        # Page Object 实现层（生成）
│   └── *_page.py
│
├── tests/                        # 测试用例层（生成）
│   └── test_*.py
│
├── test-data/                    # 测试数据
│   ├── test_account_pool.json    # 测试账号池
│   └── *_data.json               # 生成的测试数据
│
├── docs/                         # 文档
│   ├── architecture.md           # 本文档
│   ├── rules.yaml                # 可执行规则（生成/执行的结构化配置源）
│   └── test-plans/               # 生成的测试计划
│
├── reports/                      # 测试报告
├── screenshots/                  # 截图
└── allure-results/               # Allure 数据
```

## 模块职责

### `config/project.yaml` (项目配置中心)

统一管理所有项目配置：

| 配置项 | 用途 |
|--------|------|
| `repositories` | GitHub 仓库地址（前端/后端） |
| `environments` | 多环境服务地址配置 |
| `test_data` | 测试数据文件路径 |
| `health_check` | 服务健康检查配置 |
| `browser` | 浏览器配置 |

### `utils/config.py` (配置管理器)

| 方法 | 功能 |
|------|------|
| `get_repository(name)` | 获取仓库配置 |
| `get_service_url(name)` | 获取当前环境的服务 URL |
| `get_health_check_url(name)` | 获取健康检查 URL |
| `get_test_data_path(name)` | 获取测试数据路径 |
| `load_test_data(name)` | 加载测试数据 |
| `get_all_services()` | 获取所有服务配置 |

### `utils/service_checker.py` (服务健康检查)

| 方法 | 功能 |
|------|------|
| `check_service(name)` | 检查单个服务 |
| `check_all_services()` | 检查所有服务 |
| `wait_for_service(name)` | 等待服务启动 |
| `get_status_report()` | 获取格式化状态报告 |

### `core/fixtures.py` (Pytest Fixtures)

| Fixture | 功能 |
|---------|------|
| `frontend_url` | 前端服务 URL |
| `backend_url` | 后端服务 URL |
| `test_account` | 测试账号 |
| `test_data` | 通用测试数据加载器 |
| `service_checker` | 服务检查器 |
| `ensure_services_running` | 确保服务运行 |

### `core/` 核心框架层

#### `core/base_page.py` (Page Object 基类 - 协调器)
- **设计模式**: 模板方法模式 + 组合模式
- **继承关系**: `BasePage(ABC, PageActions, PageWaits)`
- **抽象方法**: 强制子类实现 `navigate()` 和 `is_loaded()`
- **职责**: 协调页面操作和等待策略，提供统一的页面对象接口

#### `core/page_actions.py` (页面操作封装)
- **职责**: 封装所有页面操作
- **方法**: `click()`, `fill()`, `select_option()`, `check()`, `uncheck()`, `get_text()`, `get_attribute()` 等

#### `core/page_waits.py` (页面等待策略)
- **职责**: 提供智能等待能力
- **方法**: `wait_for_element()`, `wait_for_url()`, `wait()` 等

#### `core/page_utils.py` (页面工具函数)
- **职责**: 提供页面相关的工具函数
- **功能**: 验证错误提取、元素状态检查等

#### `core/fixtures.py` (Pytest Fixtures)
- **职责**: 提供 pytest fixtures
- **Fixtures**: `frontend_url`, `backend_url`, `test_account`, `test_data`, `service_checker`, `ensure_services_running`

### `generators/` 代码生成引擎

#### 数据模型层

##### `generators/page_types.py` (数据模型定义)
- **职责**: 定义页面分析的数据模型
- **类**:
  - `PageElement` - 页面元素数据类（selector, type, attributes 等）
  - `PageInfo` - 页面信息数据类（url, page_type, elements 等）

#### 页面分析层

##### `generators/page_analyzer.py` (页面分析器 - 协调器)
- **职责**: 协调页面分析流程
- **方法**:
  - `analyze()` - 主入口，分析页面
  - `_analyze_page()` - 分析页面结构
  - `_detect_page_type()` - 识别页面类型
  - `_get_forms()` - 提取表单信息
  - `_get_navigation()` - 提取导航信息
- **依赖**: `ElementExtractor` 进行元素提取

##### `generators/element_extractor.py` (元素提取器)
- **职责**: 从页面中提取各种类型的元素
- **方法**:
  - `_get_elements()` - 提取所有元素
  - `_get_inputs()` - 提取输入框
  - `_get_buttons()` - 提取按钮
  - `_get_links()` - 提取链接
  - `_get_selects()` - 提取下拉框
  - `_extract_element_info()` - 提取元素详细信息

#### 代码生成层

##### `generators/test_code_generator.py` (测试代码生成器 - 协调器)
- **职责**: 统一协调 Page Object、测试用例、测试数据的生成
- **方法**: `generate_all()` - 生成所有文件
- **依赖**: `PageObjectGenerator`, `TestCaseGenerator`, `TestDataGenerator`

##### `generators/page_object_generator.py` (Page Object 生成器)
- **职责**: 生成 Page Object 类代码
- **方法**:
  - `generate_page_object()` - 生成 Page Object 代码
  - `_gen_selectors()` - 生成选择器常量
  - `_gen_methods()` - 生成操作方法

##### `generators/test_case_generator.py` (测试用例生成器)
- **职责**: 生成测试用例代码
- **方法**: `generate_test_cases()` - 生成测试用例代码
- **依赖**: 不依赖 `TestCaseTemplates`（已废弃）；生成器应直接输出“可执行用例”并复用现有 fixtures

##### `generators/test_case_templates.py` (测试用例模板)
- **状态**: **DEPRECATED**
- **原因**: 历史上用于生成 TODO 骨架，容易产出“不可跑模板”，与当前规则冲突
- **替代**: 使用 `TestCaseGenerator` / `TestCodeGenerator` 生成可执行套件（P0/P1/P2/security）

##### `generators/test_data_generator.py` (测试数据生成器)
- **职责**: 生成测试数据 JSON 文件
- **方法**: `generate_test_data()` - 生成测试数据
- **输出**: 包含 `valid_data`, `invalid_data`, `boundary_data`

#### 文档生成层

##### `generators/test_plan_generator.py` (测试计划生成器 - 协调器)
- **职责**: 统一协调测试计划的生成
- **方法**: `generate()` - 生成测试计划 Markdown
- **依赖**: `TestPlanFormatter`, `TestPlanScenarios`

##### `generators/test_plan_formatter.py` (测试计划格式化器)
- **职责**: 格式化测试计划的各个部分
- **方法**:
  - `_header()` - 生成标题和概述
  - `_overview()` - 生成页面概述
  - `_element_mapping()` - 生成元素映射
  - `_test_cases()` - 生成测试用例列表
  - `_test_data()` - 生成测试数据说明
  - `_notes()` - 生成注意事项

##### `generators/test_plan_scenarios.py` (测试计划场景生成器)
- **职责**: 生成特定类型的测试场景
- **方法**:
  - `_p0_tests()` - 生成 P0 测试场景
  - `_p1_tests()` - 生成 P1 测试场景
  - `_p2_tests()` - 生成 P2 测试场景
  - `_login_p0()`, `_form_p0()`, `_list_p0()` - 特定页面类型的测试场景

#### 工具层

##### `generators/utils.py` (公共工具函数)
- **职责**: 提供生成器公共工具函数
- **功能**:
  - 命名转换: `to_snake_case()`, `to_class_name()`, `to_constant_name()`
  - URL 解析: `get_page_name_from_url()`, `get_file_name_from_url()`, `extract_url_path()`
  - 元素处理: `get_element_name()`, `get_element_constant_name()`, `get_element_description()`
  - 页面类型: `get_page_description()`, `requires_auth()`

## 设计原则

1. **AI 优先** - 所有操作通过自然语言对话完成
2. **配置集中** - 所有配置统一在 `project.yaml`
3. **服务感知** - 测试前自动检查服务状态
4. **多环境支持** - 支持 dev/staging/production 多套配置
5. **DRY** - 公共逻辑提取复用
6. **单一职责** - 每个模块职责明确，文件大小控制在 400 行以内
7. **协调器模式** - 使用协调器统一管理子模块，降低耦合度
8. **组合优于继承** - 通过组合（继承多个能力类）而非深度继承

## 架构设计模式

### 协调器模式（Coordinator Pattern）

框架大量使用协调器模式，将复杂的生成逻辑拆分为多个专门的生成器，由协调器统一管理：

```
协调器（Coordinator）
    ├── 子生成器 1（Specialized Generator）
    ├── 子生成器 2（Specialized Generator）
    └── 子生成器 3（Specialized Generator）
```

**优势**:
- 降低耦合：子生成器之间互不依赖
- 易于扩展：新增生成器不影响现有代码
- 职责清晰：每个生成器只负责一个方面

**应用场景**:
- `TestCodeGenerator` → `PageObjectGenerator`, `TestCaseGenerator`, `TestDataGenerator`
- `TestPlanGenerator` → `TestPlanFormatter`, `TestPlanScenarios`
- `PageAnalyzer` → `ElementExtractor`
- `BasePage` → `PageActions`, `PageWaits`

### 模板方法模式（Template Method Pattern）

`BasePage` 使用模板方法模式，强制子类实现核心方法：

```python
class BasePage(ABC):
    @abstractmethod
    def navigate(self) -> None:
        """子类必须实现"""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """子类必须实现"""
        pass
```

### 组合模式（Composition Pattern）

`BasePage` 通过多重继承组合多个能力类：

```python
class BasePage(ABC, PageActions, PageWaits):
    """组合操作能力和等待能力"""
```

## 文件组织原则

### 文件大小控制
- **目标**: 每个文件不超过 400 行
- **原因**: 提高可读性和可维护性
- **现状**: 所有文件均符合要求（最大 378 行）

### 模块划分原则
1. **按职责划分**: 每个模块只负责一个功能
2. **按层次划分**: 数据模型 → 分析层 → 生成层 → 工具层
3. **按类型划分**: 代码生成 vs 文档生成

### 依赖关系
- **单向依赖**: 协调器依赖子生成器，子生成器不依赖协调器
- **工具共享**: `utils.py` 被所有生成器共享
- **数据模型**: `page_types.py` 作为所有生成器的数据基础

## 变更日志

| 日期 | 变更 |
|------|------|
| 2025-12-16 | **重大重构**: 拆分超大文件，所有文件控制在 400 行以内 |
| 2025-12-16 | 拆分 `test_code_generator.py` (687行) → 5 个文件 |
| 2025-12-16 | 拆分 `test_plan_generator.py` (673行) → 3 个文件 |
| 2025-12-16 | 拆分 `page_analyzer.py` (467行) → 3 个文件 |
| 2025-12-16 | 拆分 `base_page.py` (413行) → 3 个文件 |
| 2025-12-16 | 新增 `core/page_actions.py` 和 `core/page_waits.py` |
| 2025-12-16 | 新增 `generators/page_types.py` 数据模型层 |
| 2025-12-16 | 新增 `generators/element_extractor.py` 元素提取器 |
| 2025-12-22 | `generators/test_case_templates.py` 标记为 DEPRECATED（禁止生成 TODO 骨架，统一产出可跑套件） |
| 2025-12-22 | 新增 `utils/rules_loader.py`：运行时加载 `.cursor/rules/**` 并落盘 `reports/rules_context.md`，让“生成过程调用 rule”可审计 |
| 2025-12-16 | 新增 `generators/test_plan_formatter.py` 和 `test_plan_scenarios.py` |
| 2025-12-15 | 新增服务健康检查模块 |
| 2025-12-15 | 扩展配置结构（仓库/多环境/测试数据） |
| 2025-12-15 | 移除 CLI，改为纯 AI 对话驱动 |
| 2025-12-09 | 创建 `generators/utils.py`，重构生成器 |
