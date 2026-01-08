# Playwright Test Scaffold - Architecture

> AI 驱动的自动化测试脚手架 - 架构文档

## 相关文档

- **[QUICKSTART.md](../QUICKSTART.md)** ⚡ - 3 步生成测试
- **[Spec-Kit 指南](./spec-kit-guide.md)** - AI 驱动的规约→代码工作流
- **[框架概览](./framework_overview.md)** - pytest + Playwright 运行链路

## 使用方式

核心链路：**"URL → 动态分析 → 全量生成 → 执行 → 报告"**

```
# 执行测试
make test TEST_TARGET=tests/...

# 生成报告
make report && make serve
```

## 目录结构

```
playwright-test-scaffold/
├── conftest.py                   # pytest 根配置
├── pytest.ini                    # pytest 配置
├── requirements.txt              # 依赖清单
│
├── config/
│   └── project.yaml              # 项目配置中心
│
├── core/                         # 核心框架层
│   ├── base_page.py              # Page Object 基类
│   ├── page_actions.py           # 页面操作封装
│   ├── page_waits.py             # 页面等待策略
│   ├── fixtures.py               # pytest fixtures
│   └── fixture/                  # fixtures 实现拆分
│
├── generators/                   # 代码生成引擎
│   ├── page_types.py             # PageElement, PageInfo 数据类
│   ├── page_analyzer.py          # 页面分析器
│   ├── element_extractor.py      # 元素提取器
│   ├── test_code_generator.py    # 测试代码生成器
│   ├── page_object_generator.py  # Page Object 生成器
│   ├── test_case_generator.py    # 测试用例生成器
│   ├── test_data_generator.py    # 测试数据生成器
│   ├── test_plan_generator.py    # 测试计划生成器
│   └── utils.py                  # 公共工具函数
│
├── utils/                        # 工具模块
│   ├── config.py                 # 配置管理器
│   ├── logger.py                 # 日志系统
│   ├── data_manager.py           # 数据管理器
│   └── service_checker.py        # 服务健康检查
│
├── pages/                        # Page Object 实现层
│   ├── example_page.py           # 示例页面对象
│   └── login_page.py             # 登录页对象模板
│
├── tests/                        # 测试用例层
│   └── test_example.py           # 示例测试
│
├── test-data/                    # 测试数据
│   ├── test_account_pool.json    # 测试账号池
│   └── example_data.json         # 示例测试数据
│
├── docs/                         # 文档
│   ├── architecture.md           # 本文档
│   ├── framework_overview.md     # 框架概览
│   └── spec-kit-guide.md         # Spec-Kit 指南
│
├── specs/                        # Spec-Kit 规格目录
│
├── scripts/                      # 工具脚本
│
├── allure-results/               # Allure 原始结果
├── allure-report/                # Allure HTML 报告
└── screenshots/                  # 测试截图
```

## 模块职责

### `config/project.yaml`

统一管理所有项目配置：

| 配置项 | 用途 |
|--------|------|
| `repositories` | 代码仓库地址 |
| `environments` | 多环境服务地址 |
| `test_data` | 测试数据路径 |
| `browser` | 浏览器配置 |

### `core/` 核心框架层

- **`base_page.py`** - Page Object 基类（协调器）
- **`page_actions.py`** - 页面操作封装
- **`page_waits.py`** - 页面等待策略
- **`fixtures.py`** - pytest fixtures

### `generators/` 代码生成引擎

- **`page_analyzer.py`** - 页面分析器
- **`test_code_generator.py`** - 测试代码生成器
- **`test_plan_generator.py`** - 测试计划生成器

### `utils/` 工具模块

- **`config.py`** - 配置管理器
- **`data_manager.py`** - 数据管理器
- **`service_checker.py`** - 服务健康检查

## 设计原则

1. **AI 优先** - 通过自然语言对话生成代码
2. **配置集中** - 所有配置统一在 `project.yaml`
3. **服务感知** - 测试前自动检查服务状态
4. **单一职责** - 每个模块职责明确
5. **文件控制** - 每个文件不超过 400 行
6. **协调器模式** - 使用协调器统一管理子模块

## 架构模式

### 协调器模式

```
协调器（Coordinator）
    ├── 子生成器 1
    ├── 子生成器 2
    └── 子生成器 3
```

### 模板方法模式

```python
class BasePage(ABC):
    @abstractmethod
    def navigate(self) -> None:
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        pass
```

### 组合模式

```python
class BasePage(ABC, PageActions, PageWaits):
    """组合操作能力和等待能力"""
```

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-01-08 | **框架提纯**: 删除业务代码，变成通用测试框架 |
| 2026-01-05 | **测试报告优化**: 统一测试报告文件夹结构 |
| 2025-12-16 | **重大重构**: 拆分超大文件，所有文件控制在 400 行以内 |
