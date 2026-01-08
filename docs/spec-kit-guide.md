# Spec-Kit 框架指南

> **规约驱动开发** - 人类写规约，AI 生成代码

---

## 核心理念

```
传统模式：人类 → 写规约 → 写代码 → 测试 → 修 Bug
Spec-Kit：人类 → 写规约 → AI 生成代码 → AI 测试 → 验收
```

**三大支柱**：
1. **Constitution（宪法）** - 项目的永恒原则
2. **Spec-Driven Workflow** - 意图 → 计划 → 任务 → 代码
3. **AI Automation** - AI 按规约生成符合标准的代码

---

## 文件结构

```
.specify/
├── memory/
│   └── constitution.md      # 宪法：项目原则和标准
├── templates/               # Spec-Kit 模板
└── scripts/                 # 自动化脚本

specs/<xxx>-<feature>/
├── spec.md                  # 功能规约（WHAT）
├── plan.md                  # 技术计划（HOW）
└── tasks.md                 # 任务清单
```

---

## 快速使用

### 步骤 1：写功能规约

```
在 Cursor 中输入：
/speckit.specify

功能描述：
我想测试登录页面，用户可以：
- 用邮箱登录
- 用手机号登录
- 忘记密码
```

**输出**：`specs/001-login/spec.md`

### 步骤 2：生成技术计划

```
/speckit.plan

上下文：基于 specs/001-login/spec.md
```

**输出**：`specs/001-login/plan.md`

### 步骤 3：生成任务清单

```
/speckit.tasks

上下文：基于 spec.md 和 plan.md
```

**输出**：`specs/001-login/tasks.md`

### 步骤 4：生成测试代码

```
@ui-automation-code-generator.mdc 

基于 specs/001-login 生成测试代码
```

**输出**：
- `pages/login_page.py`
- `tests/login/test_login_p0.py`
- `test-data/login_data.json`

---

## 核心命令

| 命令 | 作用 | 输出 |
|------|------|------|
| `/speckit.specify` | 生成功能规约 | spec.md |
| `/speckit.plan` | 生成技术计划 | plan.md |
| `/speckit.tasks` | 生成任务清单 | tasks.md |
| `@ui-test-plan-generator.mdc` | 探索页面 | 测试计划 |
| `@ui-automation-code-generator.mdc` | 生成代码 | Page Object + 测试用例 |

---

## Constitution（宪法）

位于 `.specify/memory/constitution.md`，定义：

- **代码原则** - 文件行数限制、函数长度、命名规范
- **测试标准** - Page Object 模式、数据管理、优先级划分
- **架构规范** - 目录结构、模块划分、文档要求

**AI 生成代码时必须遵守宪法约束。**

---

## 最佳实践

### 1. 先规约，后代码

```
❌ 直接写代码
✅ 先写 spec.md → 再生成代码
```

### 2. 一个功能一个目录

```
specs/
├── 001-login/        # 登录功能
├── 002-register/     # 注册功能
└── 003-profile/      # 个人资料
```

### 3. 规约要具体

```
❌ 用户可以登录
✅ 用户输入邮箱和密码，点击登录按钮，成功后跳转到首页
```

### 4. 优先级划分

- **P0**: 核心功能，必须测试
- **P1**: 重要功能，应该测试
- **P2**: 增强功能，可以测试
- **Security**: 安全测试，必须测试

---

## 一键测试模板

**在 Cursor 中复制粘贴：**

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：<URL>
账号：<测试账号>
密码：<测试密码>
```

**AI 会自动：**
1. 探索页面并分析功能
2. 生成 Spec-Kit 文档
3. 生成测试代码

**然后运行：**

```bash
make test TEST_TARGET=tests/<feature>
make serve
```

---

## 相关文档

- [框架概览](./framework_overview.md)
- [架构文档](./architecture.md)
- [快速开始](../QUICKSTART.md)
