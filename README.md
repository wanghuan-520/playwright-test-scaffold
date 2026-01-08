# 🎭 Playwright Test Scaffold

> **AI 驱动的 Playwright 自动化测试框架** - 用自然语言生成测试，全自动执行

<!-- 徽章区域 -->
[![CI](https://github.com/wanghuan-520/playwright-test-scaffold/actions/workflows/ci.yml/badge.svg)](https://github.com/wanghuan-520/playwright-test-scaffold/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.49-green.svg)](https://playwright.dev/)
[![pytest](https://img.shields.io/badge/pytest-7.4-orange.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-purple.svg)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](Dockerfile)

---

## ✨ 核心特性

### 🤖 AI 驱动的测试生成

```
步骤 1：在 Cursor 中 @ 规则文件，提供 URL 和登录信息
  ↓
AI 自动完成：页面分析 → 测试计划 → 代码生成
  ↓
步骤 2：执行测试脚本，生成 Allure 报告
```

### 🔍 双重分析保证准确性

- **代码静态分析** - 深度理解业务逻辑、验证规则、API 接口
- **Playwright MCP 动态分析** - 获取实际渲染的元素、交互状态
- **智能合并** - 两种分析结果互补，生成最准确的测试用例

### 🎯 关键特性

| 特性 | 说明 |
|------|------|
| 🧹 **自动清理** | 每次测试前自动清理旧数据（报告、截图、结果） |
| 🔐 **数据隔离** | 每个测试用例使用独立账号，自动分配、清理、恢复 |
| 📸 **关键步骤截图** | 所有关键步骤自动截图，附加到 Allure 报告 |
| ⚡ **智能等待** | 所有操作自动等待元素可见、可点击，无需手动 sleep |
| 🩺 **服务检查** | 测试前自动检查服务状态，未启动时智能等待 |
| 📊 **Allure 报告** | 自动生成并打开 HTML 报告 |
| 🎨 **可维护性** | 倾向小文件与清晰分层，持续把复杂逻辑拆分到职责单一的模块 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium

# 安装 Allure（用于报告）
# Mac
brew install allure

# Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

### 2. 配置项目

复制配置模板并编辑 `config/project.yaml`：

```bash
cp config/project.yaml.example config/project.yaml
```

```yaml
project:
  name: "Your Project Name"
  description: "项目描述"
  version: "1.0.0"

repositories:
  frontend:
    local_path: "/path/to/your/frontend"   # 可选，便于静态分析
    url: ""
    branch: "main"
  backend:
    local_path: "/path/to/your/backend"    # 可选，便于静态分析
    url: ""
    branch: "main"

environments:
  default: "dev"
  dev:
    frontend:
      url: "https://localhost:3000"
      health_check: "/"
    backend:
      url: "https://localhost:44320"
      health_check: "/api/health"

test_data:
  accounts:
    path: "test-data/test_account_pool.json"
```

### 3. 准备测试数据

复制并编辑测试账号池：

```bash
cp test-data/test_account_pool.json.example test-data/test_account_pool.json
```

```json
{
  "test_account_pool": [
    { "username": "testuser01", "email": "testuser01@example.com", "password": "Test123456!" },
    { "username": "testuser02", "email": "testuser02@example.com", "password": "Test123456!" }
  ]
}
```

### 4. 运行测试

```bash
# 运行指定目录的测试
make test TEST_TARGET=tests/

# 生成报告
make report

# 打开报告
make serve
```

### 5. Docker 方式运行（可选）

```bash
# 运行单元测试
docker-compose up test-unit

# 运行测试并生成覆盖率报告
docker-compose up test-cov

# 进入交互式 Shell
docker-compose run --rm shell
```

---

## 🛠️ 开发工具

```bash
# 安装 pre-commit hooks
make install-hooks

# 代码检查
make lint

# 代码格式化
make format

# 运行框架单元测试
make test-unit

# 运行单元测试 + 覆盖率
make test-cov
```

---

## 📁 项目结构

```
playwright-test-scaffold/
├── .cursor/rules/              # AI 规则系统（模块化）
│   ├── core/                   # 核心规则
│   ├── generation/             # 代码生成规则
│   ├── quality/                # 质量标准
│   └── data/                   # 数据管理规则
│
├── .specify/                   # Spec-Kit 配置
│   ├── memory/                 # 项目宪法与记忆
│   ├── templates/              # 规约模板
│   └── scripts/                # 自动化脚本
│
├── config/
│   ├── project.yaml            # 项目配置中心
│   └── project.yaml.example    # 配置模板
│
├── core/                       # 核心框架层
│   ├── base_page.py            # Page Object 基类
│   ├── fixtures.py             # pytest fixtures
│   ├── page_actions.py         # 页面操作封装
│   ├── page_waits.py           # 页面等待策略
│   └── page_utils.py           # 页面工具函数
│
├── generators/                 # 代码生成引擎
│   ├── page_analyzer.py        # 页面分析器
│   ├── page_object_generator.py
│   ├── test_case_generator.py
│   └── test_data_generator.py
│
├── utils/                      # 工具模块
│   ├── config.py               # 配置管理器
│   ├── logger.py               # 日志系统
│   └── service_checker.py      # 服务健康检查
│
├── pages/                      # Page Objects（生成）
│   ├── example_page.py         # 示例 Page Object
│   └── login_page.py           # 登录页 Page Object
│
├── tests/                      # 测试用例
│   └── test_example.py         # 示例测试
│
├── test-data/                  # 测试数据
│   ├── example_data.json       # 示例数据
│   └── test_account_pool.json.example
│
├── specs/                      # 规约文件（Spec-Kit）
│
├── docs/                       # 文档
│
├── allure-results/             # Allure 原始数据
├── allure-report/              # Allure HTML 报告
└── screenshots/                # 测试截图
```

---

## 🧭 使用流程

### 步骤 1：生成测试代码（在 Cursor 中）

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc

帮我测试这个页面：https://your-site.com/login
账号：test@example.com
密码：YourPassword123!
```

AI 将自动完成：
- 📋 页面分析与测试计划生成
- 🧩 Page Object 代码生成
- ✅ 测试用例代码生成
- 📦 测试数据文件生成

### 步骤 2：执行测试并生成报告

```bash
# 使用 4 个 worker 并行执行测试
pytest tests/<你的模块> -n 4 --alluredir=allure-results

# 生成并打开 Allure 报告
make serve
```

---

## ⚙️ 配置说明

### 常用环境变量

| 环境变量 | 作用 |
|---------|------|
| `TEST_ENV=dev` | 选择运行环境 |
| `REUSE_LOGIN=1` | 复用登录态，更快且降低 lockout 风险 |
| `PRECHECK_ACCOUNTS=1` | 运行前预检账号池 |
| `KEEP_ALLURE_HISTORY=1` | 清理目录时保留趋势数据 |
| `APPEND_ALLURE_RESULTS=1` | 追加模式，不清空历史结果 |

### Makefile 命令

```bash
make test TEST_TARGET=tests/    # 运行测试
make report                      # 生成 Allure 报告
make serve                       # 打开报告
make clean                       # 清理所有结果
make clean-cache                 # 清空缓存
```

---

## 🏷️ 测试优先级

| 标记 | 说明 | 覆盖场景 |
|------|------|----------|
| `@pytest.mark.P0` | 核心功能（必须通过） | 页面加载、主流程、必填字段验证 |
| `@pytest.mark.P1` | 重要功能 | 边界值测试、格式验证、API 错误处理 |
| `@pytest.mark.P2` | 一般功能 | UI 交互、可访问性 |

```bash
# 只运行 P0 测试
pytest -m P0

# 运行 P0 和 P1 测试
pytest -m "P0 or P1"
```

---

## 📊 Allure 报告

### 报告内容

| 模块 | 说明 |
|------|------|
| **Overview** | 测试概览、通过率、失败率、执行时间趋势 |
| **Suites** | 测试套件列表，可查看每个测试的详细步骤 |
| **Behaviors** | 按功能分组 |
| **Timeline** | 时间轴，显示并发执行情况 |

### 查看测试详情

点击任意测试 → 查看：
- ✅ 测试步骤
- 📸 每个步骤的截图
- 📝 日志输出
- ❌ 失败原因

---

## 🔧 扩展指南

### 添加新的 Page Object

1. 在 `pages/` 目录创建新文件
2. 继承 `BasePage` 基类
3. 定义元素选择器和操作方法

```python
from core.base_page import BasePage

class MyPage(BasePage):
    # 选择器
    USERNAME_INPUT = "[name='username']"
    SUBMIT_BUTTON = "button[type='submit']"
    
    def fill_username(self, username: str):
        self.fill(self.USERNAME_INPUT, username)
    
    def click_submit(self):
        self.click(self.SUBMIT_BUTTON)
```

### 添加新的测试用例

1. 在 `tests/` 目录创建新文件
2. 使用 fixtures 获取页面对象
3. 编写测试逻辑

```python
import pytest
import allure

@pytest.mark.P0
@allure.feature("登录功能")
def test_login_success(auth_page):
    with allure.step("验证登录成功"):
        assert auth_page.is_logged_in()
```

---

## 🤝 贡献指南

### 代码规范

- **文件大小**: 单个文件不超过 **400 行**
- **函数**: 短小、职责单一
- **注释**: 中文注释 + 英文代码
- **格式**: Black + isort

### 提交规范

```bash
<type>(<scope>): <subject>

# 示例
feat(generators): 添加新的页面分析器
fix(core): 修复 BasePage 等待超时问题
docs(readme): 更新文档
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [框架讲解](docs/framework_overview.md) | 框架整体说明 |
| [架构设计](docs/architecture.md) | 架构说明、设计模式 |
| [Spec-Kit 指南](docs/spec-kit-guide.md) | Spec-Driven Development |
| [项目宪法](.specify/memory/constitution.md) | 项目核心原则与标准 |

---

## 📄 License

MIT License

---

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化框架
- [Pytest](https://pytest.org/) - Python 测试框架
- [Allure](https://docs.qameta.io/allure/) - 测试报告
- [Cursor](https://cursor.sh/) - AI 代码编辑器

---

**Happy Testing! 🎭**

_让 AI 帮你写测试，你专注于创造价值！_ ✨
