## `.cursor/` 最简用法

### 只记 2 个入口（对话里 @ 引用）

- **`@.cursor/rules/ui-test-plan-generator.mdc`**：页面分析 → `docs/test-plans/<slug>.md` + 证据链
- **`@.cursor/rules/ui-automation-code-generator.mdc`**：测试计划 → 生成 `pages/` + `tests/` + `test-data/`

### 规则关系（不用背，知道在哪就行）

```
入口规则（你对话里用 @ 引用）
  ├─ ui-test-plan-generator.mdc
  │    ├─ core/project-overview.mdc        # 项目约束/仓库口径
  │    ├─ quality/test-case-standards.mdc  # 用例设计口径（P0/P1/P2/security）
  │    └─ data/data-management.mdc         # 账号池/登录态/数据清理策略
  └─ ui-automation-code-generator.mdc
       ├─ core/project-overview.mdc        # 项目约束/仓库口径
       ├─ generation/code-generation.mdc   # POM/目录/命名/生成骨架
       ├─ quality/test-case-standards.mdc  # 矩阵用例/断言层级/回滚要求
       ├─ quality/allure-reporting.mdc     # Allure 降噪/失败证据（含“参数化标题降噪 / ProfileSettings 风格”）
       └─ data/data-management.mdc         # 数据文件/账号池/可重复执行

规则库（按需查）
  ├─ core/        项目约束
  ├─ generation/  代码生成约定
  ├─ quality/     用例标准 & Allure 证据
  └─ data/        账号池/登录态/清理
```

### 推荐流程（当前仓库：手动 pytest + allure）

1) 生成计划：
- `@.cursor/rules/ui-test-plan-generator.mdc <url>`（**MCP-first**；账号可贴，密码用环境变量/账号池，别直接写进对话/文档）

2) 生成代码：
- `@.cursor/rules/ui-automation-code-generator.mdc @docs/test-plans/<slug>.md`

3) 手动执行与报告：

```bash
make test TEST_TARGET=tests/admin/profile
make report
make serve
```