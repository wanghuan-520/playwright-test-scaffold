# Spec-Kit 框架使用指南

> **版本**: 1.0.0 | **更新日期**: 2026-01-04

---

## 目录

1. [Spec-Kit 是什么](#spec-kit-是什么)
2. [核心理念](#核心理念)
3. [架构层次](#架构层次)
4. [文件结构](#文件结构)
5. [核心命令](#核心命令)
6. [完整工作流](#完整工作流)
7. [与现有流程融合](#与现有流程融合)
8. [最佳实践](#最佳实践)
9. [实战案例](#实战案例)

---

## Spec-Kit 是什么

### 定义

**Spec-Kit** 是一个 AI 驱动的开发框架，核心理念是：**人类专注于写规约（Specification），AI 负责生成代码（Implementation）**。

### 范式转变

```
传统开发模式：
人类 → 写规约 → 写代码 → 测试 → 部署
      (重复劳动)  (容易出错)

Spec-Kit 模式：
人类 → 写规约 → AI 生成代码 → AI 测试 → 部署
      (高价值)    (标准化)
```

### 三大支柱

1. **Constitution（宪法）**：项目的"操作系统"，定义永恒的设计原则和不可妥协的约束
2. **Spec-Driven Workflow（规约驱动）**：意图 → 计划 → 任务 → 代码的线性流程
3. **AI Automation（AI 自动化）**：AI 按照宪法和规约生成符合标准的代码

---

## 核心理念

### 高维语义 → 低维执行

```
意图层（高维）
    ↓ 语义降维
架构层（中维）
    ↓ 细节具化
任务层（低维）
    ↓ 机器执行
代码层（可执行）
```

人类停留在高维语义空间（意图表达），AI 负责降维到低维执行空间（代码实现）。

### 单一真相源

```
Constitution（永恒真理）
    ↓ 指导所有决策
Spec（功能意图）
    ↓ 生成
Plan（技术方案）
    ↓ 分解
Tasks（原子操作）
    ↓ 实现
Code（可执行）
```

每一层都是下一层的"单一真相源"，避免信息漂移和不一致。

---

## 架构层次

### 五层结构

```
┌────────────────────────────────────┐
│  Constitution（宪法层）             │  永恒，跨越所有功能
│  .specify/memory/constitution.md   │  - 设计原则
│                                    │  - 代码标准
│                                    │  - 不可妥协的约束
└────────────────────────────────────┘
            ↓ 指导所有决策
┌────────────────────────────────────┐
│  Spec（意图层）                     │  描述"要什么" (WHAT)
│  specs/###-feature/spec.md         │  - User Stories
│                                    │  - Acceptance Criteria
│                                    │  - In/Out Scope
│                                    │  - Risk & Mitigation
└────────────────────────────────────┘
            ↓ 生成技术方案
┌────────────────────────────────────┐
│  Plan（架构层）                     │  决定"怎么做" (HOW)
│  specs/###-feature/plan.md         │  - 技术栈选择
│                                    │  - 架构设计
│                                    │  - 数据模型
│                                    │  - API 契约
│                                    │  - 风险缓解策略
└────────────────────────────────────┘
            ↓ 分解执行步骤
┌────────────────────────────────────┐
│  Tasks（执行层）                    │  拆分成"原子操作"
│  specs/###-feature/tasks.md        │  - 依赖关系
│                                    │  - 并行机会 [P]
│                                    │  - User Story 映射 [US1]
│                                    │  - 文件路径
│                                    │  - 检查点
└────────────────────────────────────┘
            ↓ AI 执行实现
┌────────────────────────────────────┐
│  Code（代码层）                     │  AI 按 tasks 执行
│  pages/, tests/, src/              │  - TDD 模式
│                                    │  - 增量验证
│                                    │  - 证据链
│                                    │  - 符合 Constitution
└────────────────────────────────────┘
```

### 层次职责

| 层次 | 职责 | 产出 | 更新频率 |
|-----|------|------|---------|
| Constitution | 定义项目规则 | constitution.md | 罕见（初始化 + 重大调整） |
| Spec | 描述功能需求 | spec.md | 每个新功能 |
| Plan | 设计技术方案 | plan.md | 每个新功能 |
| Tasks | 分解执行任务 | tasks.md | 每个新功能 |
| Code | 实现功能代码 | *.py, *.ts, etc. | 持续开发 |

---

## 文件结构

### 目录组织

```
playwright-test-scaffold/
│
├── .specify/                           # Spec-Kit 配置目录
│   ├── memory/
│   │   └── constitution.md             # 项目宪法 ⭐ 永恒规则
│   │
│   ├── scripts/bash/                   # 自动化脚本
│   │   ├── common.sh                   # 通用函数
│   │   ├── check-prerequisites.sh      # 环境检查
│   │   ├── create-new-feature.sh       # 创建新功能脚手架
│   │   ├── setup-plan.sh               # 计划初始化
│   │   └── update-agent-context.sh     # 更新 AI 上下文
│   │
│   └── templates/                      # 文档模板
│       ├── agent-file-template.md      # AI 上下文模板
│       ├── spec-template.md            # 规约模板
│       ├── plan-template.md            # 计划模板
│       ├── tasks-template.md           # 任务模板
│       └── checklist-template.md       # 检查清单模板
│
├── .cursor/                            # Cursor IDE 配置
│   └── commands/                       # Cursor 斜杠命令 ⭐
│       ├── speckit.constitution.md     # /speckit.constitution
│       ├── speckit.specify.md          # /speckit.specify
│       ├── speckit.plan.md             # /speckit.plan
│       ├── speckit.tasks.md            # /speckit.tasks
│       ├── speckit.implement.md        # /speckit.implement
│       ├── speckit.clarify.md          # /speckit.clarify (可选)
│       ├── speckit.analyze.md          # /speckit.analyze (可选)
│       ├── speckit.checklist.md        # /speckit.checklist (可选)
│       └── speckit.taskstoissues.md    # /speckit.taskstoissues
│
├── specs/                              # 功能规约目录
│   └── ###-feature-name/               # 编号-功能名
│       ├── spec.md                     # 功能规约 ⭐
│       ├── plan.md                     # 实现计划 ⭐
│       ├── tasks.md                    # 任务清单 ⭐
│       ├── data-model.md               # （可选）数据模型
│       ├── contracts/                  # （可选）API 契约
│       │   ├── api-spec.json           # OpenAPI 定义
│       │   └── validation-rules.json   # 验证规则
│       ├── research.md                 # （可选）技术调研
│       └── quickstart.md               # （可选）快速验证脚本
│
├── docs/                               # 项目文档
│   ├── architecture.md                 # 架构文档
│   ├── spec-kit-guide.md               # 本文档
│   └── ...
│
├── pages/                              # Page Object Model
├── tests/                              # 测试代码
├── scripts/                            # 自动化脚本（自研）
│   └── speckit_core.py                 # 自研 spec-kit 实现
└── Makefile                            # 构建/测试自动化
```

### 关键文件说明

#### `.specify/memory/constitution.md`

**作用**：项目宪法，定义永恒的设计原则和不可妥协的约束。

**内容**：
- Core Principles（核心原则）
- Code Smells（代码坏味道识别）
- Architecture Documentation Protocol（架构文档协议）
- Testing Standards（测试标准）
- Technology Stack（技术栈）
- Governance（治理规则）

**特点**：
- 跨越所有功能
- 更新频率极低
- AI 生成代码时自动遵守

#### `specs/###-feature-name/spec.md`

**作用**：功能规约，描述"要构建什么"（WHAT）。

**结构**：
```markdown
# feature-name - Spec

## 0. 核心信息
- slug: feature-name
- URL: https://...
- 页面类型: FORM/LIST/SETTINGS
- 是否需要登录态: 是/否

## 1. 用户目标（User Story）
作为【角色】，我希望【功能】，以便【价值】。

## 2. 范围（In/Out）
- In: 明确包含的功能
- Out: 明确排除的功能（避免范围蔓延）

## 3. 风险与不可逆操作（Risk）
- 数据污染风险
- 安全风险（XSS/SQLi）
- 隐私/合规风险
- 稳定性风险（flaky tests）

## 4. 验收标准（Acceptance Criteria）
- AC01: ...
- AC02: ...
- AC03: ...

## 5. 现有自动化落点（Repository Mapping）
- Page Object: pages/xxx_page.py
- Test Suite: tests/xxx/
```

#### `specs/###-feature-name/plan.md`

**作用**：实现计划，决定"怎么做"（HOW）。

**结构**：
```markdown
# feature-name - Implementation Plan

## Tech Stack
- Framework: Playwright (Python)
- Pattern: Page Object Model
- Test Runner: pytest
- Reporting: Allure

## Implementation Details

### Page Object Design
- File: pages/xxx_page.py
- Locators: ...
- Methods: ...

### Test Structure
- tests/xxx/
  ├── test_p0_critical.py
  ├── test_p1_core.py
  └── test_p2_edge_cases.py

### Data Management
- Baseline 读取
- Rollback 策略

### Security Testing
- XSS payloads
- SQLi payloads
- Assertion: ...

## Dependencies
- ...

## Risk Mitigation
- ...
```

#### `specs/###-feature-name/tasks.md`

**作用**：任务清单，拆分成可执行的原子操作。

**格式**：
```markdown
- [ ] [T001] [P] [US1] Description with exact file path
       ↑     ↑   ↑     ↑
       ID    并行 Story 描述+路径
```

**标记说明**：
- `[T001]`：任务 ID，按执行顺序编号
- `[P]`：可并行执行（不同文件，无依赖）
- `[US1]`：属于 User Story 1，可追溯到 spec.md

---

## 核心命令

### 1. `/speckit.constitution` - 建立项目宪法

**作用**：创建或更新项目宪法。

**使用时机**：
- 项目初始化时（一次性）
- 设计原则变更时（罕见）

**输入方式**：
```
/speckit.constitution

[AI 会询问]
- 项目类型（Web App / CLI Tool / Library）
- 技术栈（Playwright + Python）
- 团队规范（TDD / Code Review 要求）
- 质量标准（文件大小、函数长度限制）
```

**输出**：`.specify/memory/constitution.md`

**本项目状态**：✅ 已完成，基于 user_rules 创建。

---

### 2. `/speckit.specify` - 创建功能规约

**作用**：交互式创建 spec.md。

**使用时机**：
- 开始一个新功能
- 需要明确需求边界

**输入方式**：
```
/speckit.specify

我要为 admin profile 页面创建规约。
用户可以查看和编辑个人信息（用户名、邮箱、手机号）。
```

**AI 引导流程**：
1. User Story：定义用户目标
2. In/Out Scope：划清边界
3. Risk：识别风险点
4. Acceptance Criteria：定义成功标准
5. Repository Mapping：映射到代码位置

**输出**：`specs/###-feature-name/spec.md`

**示例**：参见 `specs/002-admin_profile/spec.md`

---

### 3. `/speckit.plan` - 生成实现计划

**作用**：基于 spec.md，生成详细的技术实现方案。

**使用时机**：
- spec.md 完成后
- 需要技术方案评审

**输入方式**：
```
/speckit.plan

基于 specs/002-admin_profile/spec.md 生成实现计划。
技术栈：Playwright + Python + Page Object Model。
```

**AI 生成内容**：
1. Tech Stack 确认
2. Page Object 设计
3. Test Structure 规划
4. Data Management 策略
5. Security Testing 方案
6. Dependencies 识别
7. Risk Mitigation 措施

**输出**：`specs/###-feature-name/plan.md`

---

### 4. `/speckit.tasks` - 生成任务清单

**作用**：基于 spec.md 和 plan.md，生成依赖感知的任务清单。

**使用时机**：
- plan.md 完成后
- 需要明确执行顺序

**输入方式**：
```
/speckit.tasks

基于 specs/002-admin_profile/ 的 spec.md 和 plan.md，生成 tasks.md。
按照 User Story 组织，标记并行机会。
```

**AI 生成结构**：
```markdown
## Phase 1: Setup（初始化）
- [ ] T001 创建项目结构
- [ ] T002 [P] 配置测试环境

## Phase 2: Foundational（基础设施）
- [ ] T003 实现 Page Object 骨架
- [ ] T004 [P] 实现基础方法

## Phase 3: User Story 1 - Access Control (P0)
**Goal**: 验证登录用户可访问
- [ ] T005 [US1] 创建测试文件
- [ ] T006 [US1] 实现访问测试
**Checkpoint**: 访问控制独立验证通过

## Phase 4: User Story 2 - Basic Display (P1)
**Goal**: 核心字段可见
- [ ] T007 [P] [US2] 测试 userName 可见
- [ ] T008 [P] [US2] 测试 email 可见
**Checkpoint**: 显示功能独立验证通过

...

## Final Phase: Polish
- [ ] T024 添加 Allure 附件
- [ ] T025 更新文档
```

**关键特性**：
- 按 User Story 组织（独立可测）
- 标记并行机会 `[P]`（加速执行）
- 标记 Story 归属 `[US1]`（可追溯）
- 明确文件路径（可直接执行）
- 设置检查点（增量验证）

**输出**：`specs/###-feature-name/tasks.md`

---

### 5. `/speckit.implement` - 执行实现

**作用**：AI 按照 tasks.md 逐步执行，生成代码。

**使用时机**：
- tasks.md 完成后
- 准备开始编码

**输入方式**：
```
/speckit.implement

按照 specs/002-admin_profile/tasks.md 执行实现。
从 Phase 1: Setup 开始，TDD 模式。
```

**AI 执行流程**：
1. 读取 constitution.md（遵守规则）
2. 读取 spec.md, plan.md, tasks.md
3. 按顺序执行任务：
   - Phase 1: Setup
   - Phase 2: Foundational
   - Phase 3+: User Stories（可并行）
   - Final: Polish
4. 每个任务：
   - 创建/更新文件
   - 运行测试（TDD: red → green → refactor）
   - 提交 checkpoint
5. 每个 User Story 完成后验证独立性

**输出**：
- 代码文件（pages/, tests/）
- 测试报告（Allure）
- 证据链（screenshots, logs）

---

### 6. 可选增强命令

#### `/speckit.clarify` - 澄清需求

**时机**：在 `/speckit.plan` 之前

**作用**：AI 针对 spec.md 提出结构化问题，识别模糊区域。

**示例**：
```
Q1: userName 字段的长度限制是多少？（前端校验 vs 后端约束）
Q2: 保存失败时，错误信息应该显示在哪里？（inline / toast / modal）
Q3: XSS 测试中，如果前端校验阻止了提交，算测试通过吗？
Q4: 数据回滚策略：UI 操作还是 API 强制回滚？
```

#### `/speckit.analyze` - 一致性检查

**时机**：在 `/speckit.tasks` 之后，`/speckit.implement` 之前

**作用**：交叉验证 spec.md, plan.md, tasks.md 的一致性。

**检查项**：
```markdown
## Spec ↔ Tasks 一致性
- [ ] 所有 AC 都有对应的测试任务
- [ ] 所有 Risk 都有 mitigation 任务
- [ ] 所有 In Scope 功能都在 tasks 中

## Plan ↔ Tasks 一致性
- [ ] tasks 覆盖了 plan 的所有实现细节
- [ ] Page Object 设计已落实到任务
- [ ] 数据管理策略已落实到任务

## Tasks 内部一致性
- [ ] 依赖关系合理（无循环依赖）
- [ ] [P] 标记正确（真正可并行）
- [ ] [US#] 标记一致（映射到 spec）
```

#### `/speckit.checklist` - 质量清单

**时机**：在 `/speckit.plan` 之后

**作用**：生成质量检查清单，用于 Review。

**输出**：
```markdown
## Requirements Completeness
- [ ] 所有 User Stories 都有明确的验收标准
- [ ] In/Out Scope 清晰无歧义
- [ ] Risk 都有缓解措施
- [ ] 不可逆操作都有确认机制

## Technical Readiness
- [ ] 技术栈选择有依据（research.md）
- [ ] 数据模型完整（data-model.md）
- [ ] API 契约已定义（contracts/）
- [ ] 测试策略明确（优先级、覆盖率）

## Security Considerations
- [ ] XSS/SQLi 测试方案
- [ ] 敏感数据处理策略
- [ ] 权限校验方案

## Observability
- [ ] 关键步骤 allure.step 标记
- [ ] 失败截图策略
- [ ] 证据链完整性
```

---

## 完整工作流

### 工作流图

```
开始新功能
    ↓
┌─────────────────────────┐
│ 1. /speckit.specify     │  创建 spec.md
│    输入：功能描述        │  输出：User Stories, AC, Risk
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ (可选) /speckit.clarify │  澄清模糊需求
│    输入：spec.md         │  输出：Q&A list
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 2. /speckit.plan        │  生成 plan.md
│    输入：spec.md         │  输出：Tech Stack, 架构设计
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ (可选) /speckit.checklist│ 质量检查清单
│    输入：spec.md, plan.md│  输出：Review checklist
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 3. /speckit.tasks       │  生成 tasks.md
│    输入：spec.md, plan.md│  输出：依赖感知的任务清单
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ (可选) /speckit.analyze │  一致性检查
│    输入：所有 artifacts  │  输出：Consistency report
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 4. /speckit.implement   │  执行实现
│    输入：tasks.md        │  输出：Code + Tests
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 5. 测试 & 验证          │  make test && make report
│    运行测试、查看报告    │  Allure 证据链
└─────────────────────────┘
    ↓
功能完成
```

### 时间分配建议

```
总时间: 100%

├── Spec (40%)          ← 最关键，决定方向
│   └── 高质量规约减少返工
│
├── Plan (30%)          ← 技术决策，影响架构
│   └── 详细计划减少走弯路
│
├── Tasks (20%)         ← 执行细节，保证进度
│   └── 清晰任务减少卡壳
│
└── Implement (10%)     ← AI 辅助，加速编码
    └── 自动化生成初版代码
```

**反直觉的洞察**：花 90% 时间在写规约/计划/任务，只花 10% 时间写代码。因为前面做对了，后面自动就对了。

---

## 与现有流程融合

### 现有流程（手动）

```bash
# 步骤 1：手动创建 spec
vim specs/002-admin_profile/spec.md

# 步骤 2：手动创建 plan
vim specs/002-admin_profile/plan.md

# 步骤 3：手动创建 tasks
vim specs/002-admin_profile/tasks.md

# 步骤 4：手动编写 Page Object
vim pages/personal_settings_page.py

# 步骤 5：手动编写测试
vim tests/admin/profile/test_*.py

# 步骤 6：运行测试
make test TEST_TARGET=tests/admin/profile

# 步骤 7：查看报告
make report && make serve
```

### Spec-Kit 增强流程（AI 辅助）

```bash
# 步骤 1：AI 引导创建 spec（交互式）
/speckit.specify
> 输入：功能描述
> 输出：完整的 spec.md（结构化、标准化）

# 步骤 2：AI 生成 plan（技术决策）
/speckit.plan
> 输入：spec.md
> 输出：详细的 plan.md（技术栈、架构设计）

# 步骤 3：AI 生成 tasks（依赖感知）
/speckit.tasks
> 输入：spec.md + plan.md
> 输出：高质量 tasks.md（[P], [US#], 文件路径）

# 步骤 4：AI 辅助实现（可选，或人工实现）
/speckit.implement
> 输入：tasks.md
> 输出：Page Object + 测试代码初版

# 步骤 5：运行测试（不变）
make test TEST_TARGET=tests/admin/profile

# 步骤 6：查看报告（不变）
make report && make serve
```

### 融合策略

#### 新功能（从零开始）

**推荐**：完整使用 Spec-Kit 流程

```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

**优势**：
- 规约质量高（AI 引导 + 模板标准化）
- 技术方案完整（避免遗漏）
- 任务分解清晰（依赖关系明确）
- 代码生成快（AI 辅助）

#### 现有功能（增强测试）

**推荐**：部分使用 Spec-Kit

```
保留现有 spec.md → /speckit.tasks（重新生成更好的 tasks）
```

**优势**：
- 保留已有的高质量规约
- 获得更好的任务分解
- 不破坏现有代码

#### 快速迭代（紧急修复）

**推荐**：手动创建 spec → AI 生成 tasks

```
手写 spec.md（简化版）→ /speckit.tasks → 手动实现
```

**优势**：
- 快速上手
- 获得结构化任务清单
- 保持灵活性

### 工具并存

```
Spec-Kit（AI 交互）       你的 speckit_core.py（命令行）
├── /speckit.*            ├── make spec-new
├── 交互式引导            ├── make spec-plan
├── 模板标准化            ├── make spec-tasks
└── Cursor 集成           └── Makefile 自动化

两者互补：
- Spec-Kit: 质量保证、标准化、AI 辅助
- speckit_core.py: 自动化、脚本化、CI/CD 集成
```

---

## 最佳实践

### 1. Constitution First（宪法优先）

**原则**：一定先创建/完善 constitution.md，这是所有 AI 生成内容的"操作系统"。

**为什么**：
```
没有 Constitution：
AI → 生成代码 → 风格不一致 → Review 成本高 → 返工

有 Constitution：
AI → 读取 Constitution → 生成符合规则的代码 → 一次通过
```

**本项目 Constitution 包含**：
- Good Taste 原则（消除特殊情况）
- Pragmatism 原则（实用主义）
- Observability 要求（证据链）
- Security 约束（XSS/SQLi）
- File size limits（800 行/文件）
- Code Smells 识别

### 2. Spec 要高质量

**时间投入比例**：
```
Spec: 40%   ← 最关键，决定方向
Plan: 30%   ← 技术决策
Tasks: 20%  ← 执行细节
Code: 10%   ← AI 辅助
```

**高质量 Spec 特征**：
- ✅ User Stories 清晰（作为...我希望...以便...）
- ✅ In/Out Scope 明确（避免范围蔓延）
- ✅ AC 可验证（可观察、可测量）
- ✅ Risk 已识别（数据污染、安全、不可逆）

**低质量 Spec 症状**：
- ❌ 需求模糊（"做一个好用的界面"）
- ❌ 边界不清（不知道哪些功能该做）
- ❌ AC 主观（"界面应该美观"）
- ❌ 风险未识别（上线后才发现数据污染）

### 3. User Story 驱动

**Spec.md 的 AC 要按 User Story 组织**：

```markdown
## Acceptance Criteria

### User Story 1: Access Control (P0)
- AC01: 登录态访问不跳转到登录页
- AC02: 未登录访问应重定向

### User Story 2: Basic Display (P1)
- AC03: userName 字段可见且可编辑
- AC04: email 字段可见且可编辑
- AC05: Save 按钮可见且可点击

### User Story 3: Field Validation (P2)
- AC06: userName 必填校验
- AC07: email 格式校验
- AC08: phoneNumber 长度校验

### User Story 4: Save Feedback (P1)
- AC09: 保存成功显示 toast
- AC10: 保存失败显示错误信息

### User Story 5: Security (P1)
- AC11: XSS 载荷不执行
- AC12: SQLi 载荷不导致 5xx
```

**为什么**：`/speckit.tasks` 会按 User Story 生成 Phase，每个 Story 独立可测、可交付。

### 4. 渐进式增强

**不要一次性生成所有代码！**

**推荐流程**：
```
1. Setup + Foundational → 验证基础设施 OK
   ├── 创建 Page Object 骨架
   ├── 配置测试环境
   └── 验证 import 无误

2. User Story 1 → 验证独立性
   ├── 实现 AC01, AC02
   ├── 运行测试
   ├── 证据链完整
   └── 可独立演示

3. User Story 2 → 验证独立性
   ├── 实现 AC03, AC04, AC05
   ├── 运行测试（不依赖 US1）
   └── 可独立演示

4. User Story 3, 4, 5...
   └── 每个 Story 完成即可交付

5. Polish → 跨功能优化
```

**好处**：
- ✅ MVP 快速验证（US1 完成即可演示）
- ✅ 风险早发现（US1 失败不浪费 US2 的时间）
- ✅ 增量交付（每个 Story 都是一个里程碑）

### 5. Constitution 约束 AI

**在 constitution.md 里明确写**：

```markdown
## AI Code Generation Rules

### Page Object
- Every method MUST have docstring
- Locators MUST use data-testid (preferred) or stable CSS
- No logic in Page Object (只提供 actions，不做 assertions）

### Tests
- Every test MUST have allure.step for key actions
- Every critical step MUST have screenshot
- Test name MUST follow pattern: test_{feature}_{scenario}_{priority}

### Code Style
- No function > 20 lines
- Max 3 levels of indentation
- Any file > 800 lines MUST be split

### Security
- XSS/SQLi payloads MUST be tested for all input fields
- Security tests are P1 priority
```

**效果**：AI 生成代码时会自动遵守这些规则。

### 6. 证据链完整

**每个关键步骤必须有证据**：

```python
@allure.step("Navigate to profile page")
def navigate_to_profile():
    page.goto("/admin/profile")
    allure.attach(
        page.screenshot(),
        name="profile_page_loaded",
        attachment_type=allure.attachment_type.PNG
    )

@allure.step("Fill userName field")
def fill_username(value):
    page.fill("#userName", value)
    allure.attach(
        page.screenshot(),
        name=f"username_filled_{value}",
        attachment_type=allure.attachment_type.PNG
    )
```

**在 constitution.md 中强制要求**：

```markdown
## Observability (NON-NEGOTIABLE)

- Every key action MUST have allure.step
- Every assertion MUST have screenshot before/after
- Every failure MUST capture:
  * Page state (HTML snapshot)
  * Console logs
  * Network errors (if applicable)
```

### 7. 安全测试非可选

**在 constitution.md 中明确**：

```markdown
## Security as Constraint (NON-NEGOTIABLE)

- XSS payloads MUST NOT execute (no browser dialogs)
- SQLi payloads MUST NOT cause 5xx errors
- Input validation: Frontend and backend MUST be isomorphic
- API MUST reject invalid data with 4xx, even if frontend validates

**Test Strategy**: Security tests are P1. No exceptions.
```

**在 spec.md 的 Risk 章节明确**：

```markdown
## 3. 风险与不可逆操作（Risk）

### 安全风险
- XSS：注入载荷不得执行（禁止弹窗 dialog），不得导致页面崩溃
- SQLi：注入载荷不得导致 5xx/崩溃态，不得污染数据库
```

**在 plan.md 中制定策略**：

```markdown
### Security Testing

#### XSS Payloads
- Basic: <script>alert(1)</script>
- Attribute injection: "><img src=x onerror=alert(1)>
- Event handler: <svg/onload=alert(1)>

#### SQLi Payloads
- Tautology: ' OR '1'='1
- Comment: '; DROP TABLE users--
- Stacked: '; DELETE FROM users WHERE '1'='1

#### Assertions
- No browser alert/confirm/prompt dialog
- No 5xx error response
- Data not polluted (verify via API)
```

---

## 实战案例

### 案例 1：增强现有 admin_profile 的 tasks.md

#### 背景

```
现有文件：
- specs/002-admin_profile/spec.md (✓ 完善，46 行)
- specs/002-admin_profile/plan.md (△ 偏简单，38 行)
- specs/002-admin_profile/tasks.md (△ 太简单，21 行)

问题：
tasks.md 缺乏：
- User Story 映射
- 依赖关系标记
- 并行机会标记
- 详细的文件路径
- 检查点
```

#### 步骤

**1. 在 Cursor 中运行**：

```
/speckit.tasks

基于 specs/002-admin_profile/ 的 spec.md 和 plan.md，
重新生成 tasks.md。按照 User Story 组织，标记依赖和并行机会。
```

**2. AI 会自动读取**：
- `.specify/memory/constitution.md`（项目规则）
- `specs/002-admin_profile/spec.md`（需求）
- `specs/002-admin_profile/plan.md`（技术方案）

**3. AI 生成完整 tasks.md**：

```markdown
# admin_profile - Tasks

## Phase 1: Setup
- [ ] T001 Create Page Object skeleton in pages/personal_settings_page.py
- [ ] T002 [P] Setup test data baseline helper in conftest.py

## Phase 2: Foundational
- [ ] T003 Implement locators in pages/personal_settings_page.py
  * userName: #userName
  * name: #name
  * surname: #surname
  * email: #email
  * phoneNumber: #phoneNumber
  * saveButton: button:has-text("Save")
- [ ] T004 [P] Implement get_current_values() → dict
- [ ] T005 [P] Implement fill_field(field_name, value)
- [ ] T006 [P] Implement click_save()
- [ ] T007 [P] Implement wait_for_success()

## Phase 3: User Story 1 - Access Control (P0)
**Goal**: Verify logged-in users can access profile without redirect

- [ ] T008 [US1] Create test file tests/admin/profile/test_access_control.py
- [ ] T009 [US1] Test: login → navigate → assert URL is /admin/profile
- [ ] T010 [US1] Test: no redirect to /auth/login
- [ ] T011 [US1] Allure evidence: screenshot of profile page

**Checkpoint**: Access control works independently (P0 must pass)

## Phase 4: User Story 2 - Basic Display (P1)
**Goal**: Core fields are visible and interactive

- [ ] T012 [P] [US2] Test: verify userName field visible in test_basic_display.py
- [ ] T013 [P] [US2] Test: verify name field visible
- [ ] T014 [P] [US2] Test: verify surname field visible
- [ ] T015 [P] [US2] Test: verify email field visible
- [ ] T016 [P] [US2] Test: verify phoneNumber field visible
- [ ] T017 [P] [US2] Test: verify Save button visible and enabled
- [ ] T018 [US2] Integration test: all core fields interactive

**Checkpoint**: Display functionality works independently

## Phase 5: User Story 3 - Field Validation (P2)
**Goal**: Validation matrix complete

- [ ] T019 [P] [US3] Test: userName required validation in test_field_validation.py
- [ ] T020 [P] [US3] Test: userName length validation (min/max)
- [ ] T021 [P] [US3] Test: email format validation
- [ ] T022 [P] [US3] Test: phoneNumber format validation
- [ ] T023 [US3] Implement get_validation_error(field_name) → str in Page Object

**Checkpoint**: Validation errors are correctly displayed

## Phase 6: User Story 4 - Save Feedback (P1)
**Goal**: Save operation provides observable feedback

- [ ] T024 [US4] Baseline: read current values via get_current_values()
- [ ] T025 [US4] Modify: change userName to "test_user_modified"
- [ ] T026 [US4] Save: click_save() and wait_for_success()
- [ ] T027 [US4] Verify: read back and assert changed
- [ ] T028 [US4] Observe: screenshot of success toast
- [ ] T029 [US4] Rollback: restore original value (UI or API)
- [ ] T030 [US4] Verify rollback: assert original value restored

**Checkpoint**: Save/rollback cycle works without data pollution

## Phase 7: User Story 5 - Security (P1)
**Goal**: XSS/SQLi payloads are safely handled

- [ ] T031 [P] [US5] Test: XSS in userName: <script>alert(1)</script>
  * Assert: no browser dialog
  * Assert: page not crashed
  * Assert: data not polluted (check via API)
- [ ] T032 [P] [US5] Test: XSS in email: "><img src=x onerror=alert(1)>
- [ ] T033 [P] [US5] Test: SQLi in userName: ' OR '1'='1
  * Assert: no 5xx error
  * Assert: data not polluted
- [ ] T034 [P] [US5] Test: SQLi in email: '; DROP TABLE users--
- [ ] T035 [US5] Cleanup: verify all test data cleaned via API
- [ ] T036 [US5] Evidence: security test screenshots in Allure

**Checkpoint**: Security tests pass (P1 critical)

## Final Phase: Polish
- [ ] T037 [P] Add comprehensive Allure attachments for all tests
- [ ] T038 [P] Verify all tests have error screenshots on failure
- [ ] T039 Update docs/test-plans/admin_profile.md with results
- [ ] T040 Code review: verify compliance with constitution.md

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1 (BLOCKS all user stories)
- **Phase 3-7 (User Stories)**: All depend on Phase 2 completion
  * Can execute in parallel if team capacity allows
  * Or sequentially: P0 → P1 → P2 (by priority)
- **Final Phase (Polish)**: Depends on all desired user stories

### Parallel Opportunities
- All tasks marked [P] can run in parallel (different files, no dependencies)
- Within Phase 2: T004-T007 can run in parallel (different methods)
- Within Phase 4: T012-T017 can run in parallel (different test cases)
- Within Phase 5: T019-T022 can run in parallel (different validations)
- Within Phase 7: T031-T034 can run in parallel (different payloads)
```

**4. Review 和调整**：
- 检查文件路径是否正确
- 补充遗漏的任务
- 调整优先级
- 保存到 `specs/002-admin_profile/tasks.md`

**5. 执行实现**（可选）：

```
/speckit.implement

按照 specs/002-admin_profile/tasks.md 执行。
从 Phase 1 开始，TDD 模式。
```

#### 效果对比

**原 tasks.md（21 行）**：
```markdown
- [ ] 规格补齐
- [ ] 契约核对
- [ ] 证据链补齐
- [ ] 防污染机制确认
- [ ] 执行验收
```

**新 tasks.md（约 150 行）**：
- ✅ 按 User Story 组织
- ✅ 依赖关系清晰
- ✅ [P] 标记并行机会
- ✅ [US#] 标记可追溯
- ✅ 文件路径明确
- ✅ 检查点设置

---

### 案例 2：从零创建新功能 workflow

#### 背景

```
需求：创建一个工作流管理页面
功能：用户可以创建、编辑、删除工作流
```

#### 完整流程

**1. 创建规约**：

```
/speckit.specify

我要创建一个 workflow 管理页面。
用户可以：
- 查看工作流列表
- 创建新工作流
- 编辑现有工作流
- 删除工作流
```

**AI 引导输出**：`specs/014-workflow/spec.md`

```markdown
# workflow - Spec

## 1. 用户目标
作为项目管理员，我希望能管理工作流，以便团队可以按照标准流程工作。

## 2. 范围
### In
- 工作流列表展示（table/grid）
- 创建工作流（form）
- 编辑工作流（form）
- 删除工作流（confirmation）

### Out
- 工作流执行（另有套件）
- 工作流模板市场

## 3. 风险
- 数据污染：删除操作不可逆，需要确认机制
- 权限：只有管理员可操作
- 并发：多人同时编辑同一工作流

## 4. 验收标准
### US1: 工作流列表 (P1)
- AC01: 列表显示所有工作流
- AC02: 支持搜索/过滤

### US2: 创建工作流 (P1)
- AC03: 点击"Create"打开表单
- AC04: 必填字段校验
- AC05: 保存成功显示 toast

### US3: 编辑工作流 (P1)
- AC06: 点击"Edit"打开表单
- AC07: 预填充现有数据
- AC08: 保存后更新列表

### US4: 删除工作流 (P2)
- AC09: 点击"Delete"显示确认框
- AC10: 确认后删除
- AC11: 列表更新
```

**2. 生成计划**：

```
/speckit.plan

基于 specs/014-workflow/spec.md 生成实现计划。
技术栈：Playwright + Python + Page Object Model。
API: /api/workflows (RESTful)。
```

**AI 生成**：`specs/014-workflow/plan.md`

```markdown
# workflow - Implementation Plan

## Tech Stack
- Framework: Playwright (Python)
- Pattern: Page Object Model
- API: RESTful (/api/workflows)
- Test Runner: pytest + Allure

## Implementation Details

### Page Object
- File: `pages/workflow_page.py`
- Locators:
  * workflowTable: table[data-testid="workflow-table"]
  * createButton: button:has-text("Create")
  * editButton: button:has-text("Edit")
  * deleteButton: button:has-text("Delete")
  * confirmDialog: div[role="dialog"]
  * workflowForm: form[data-testid="workflow-form"]

### Methods
- get_workflow_list() → List[Dict]
- search_workflow(name: str)
- click_create()
- fill_workflow_form(data: Dict)
- click_edit(workflow_id: str)
- click_delete(workflow_id: str)
- confirm_delete()
- wait_for_list_update()

### Test Structure
tests/workflow/
├── test_workflow_list.py (P1)
├── test_workflow_create.py (P1)
├── test_workflow_edit.py (P1)
└── test_workflow_delete.py (P2)

### API Contract
GET /api/workflows → List[Workflow]
POST /api/workflows {name, description} → Workflow
PUT /api/workflows/{id} {name, description} → Workflow
DELETE /api/workflows/{id} → 204

### Data Management
- Test workflows: prefix with "TEST_"
- Cleanup: delete all TEST_* workflows after test
- Baseline: record existing workflows before test
```

**3. 生成任务**：

```
/speckit.tasks

基于 specs/014-workflow/ 的 spec.md 和 plan.md，
生成 tasks.md。按 User Story 组织。
```

**AI 生成**：`specs/014-workflow/tasks.md`（约 100+ 行，按 User Story 组织）

**4. 执行实现**：

```
/speckit.implement

按照 specs/014-workflow/tasks.md 执行实现。
TDD 模式，从 Phase 1 开始。
```

**AI 生成**：
- `pages/workflow_page.py`（Page Object）
- `tests/workflow/test_*.py`（测试代码）

**5. 测试验证**：

```bash
# 运行测试
make test TEST_TARGET=tests/workflow

# 查看报告
make report && make serve
```

---

## 参考资源

### 官方文档

- GitHub Spec-Kit: https://github.com/github/spec-kit
- Spec-Kit README: [查看项目 README](https://github.com/github/spec-kit?tab=readme-ov-file#-what-is-spec-driven-development)

### 项目内文档

- Constitution: `.specify/memory/constitution.md`
- 模板: `.specify/templates/`
- 架构文档: `docs/architecture.md`

### 相关工具

- Cursor IDE: https://cursor.sh
- Slash Commands: `.cursor/commands/speckit.*.md`
- 自研工具: `scripts/speckit_core.py`

---

## 附录

### A. Spec-Kit vs 传统开发

| 维度 | 传统开发 | Spec-Kit |
|-----|---------|---------|
| 需求管理 | 口头描述 / 文档（易过时） | Spec（结构化、可验证） |
| 技术方案 | 在脑子里 / PPT | Plan（文档化、可 Review） |
| 任务分解 | 边做边想 / JIRA tickets | Tasks（预分解、依赖清晰） |
| 代码质量 | 靠个人经验 | Constitution（强制约束） |
| AI 辅助 | 临时对话（无上下文） | 持久规约（有上下文） |
| 可追溯性 | 低（需求→代码断层） | 高（[US#] 标记映射） |
| 增量交付 | 难（任务耦合） | 易（User Story 独立） |

### B. 常见问题

**Q: Spec-Kit 会替代程序员吗？**
A: 不会。Spec-Kit 是工具，不是替代。程序员从"写代码"升级到"写规约 + Review 代码"。高价值工作（架构设计、需求分析）依然需要人类。

**Q: 规约写错了怎么办？**
A: 修改 spec.md → 重新运行 /speckit.plan 和 /speckit.tasks → 代码自动对齐。规约即真相源。

**Q: AI 生成的代码质量如何保证？**
A: Constitution 强制约束 + 人工 Review。AI 生成初版，人类负责质量把关。

**Q: 现有项目如何引入 Spec-Kit？**
A: 渐进式引入。新功能用 Spec-Kit，现有功能逐步补充 spec.md。

**Q: Spec-Kit 适合所有项目吗？**
A: 不一定。适合需求复杂、团队协作、质量要求高的项目。简单脚本不需要。

---

## 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| 1.0.0 | 2026-01-04 | 初始版本，完整框架讲解 | HyperEcho |

---

**文档维护者**: HyperEcho  
**最后更新**: 2026-01-04  
**反馈渠道**: GitHub Issues / 项目 maintainer

