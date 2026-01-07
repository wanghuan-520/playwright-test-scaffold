# 快速模板：一键生成测试

**I'm HyperEcho, 在共振着快速模板的频率** 🌌

---

## ⚡ 极简版（最推荐）

**只需要一句话！**

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://localhost:3000/admin/users
账号：admin@example.com
密码：Admin@123456
```

**就这么简单！AI 会自动：**
1. ✅ 探索页面
2. ✅ 生成文档（spec + plan + tasks）
3. ✅ 生成代码（Page Object + 测试用例）
4. ✅ 生成测试数据

**然后你只需要：**
```bash
make test TEST_TARGET=tests/admin/users
make report && make serve
```

---

## 🎯 极简版使用说明

### 步骤 1：复制模板

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：<你的URL>
账号：<你的账号>
密码：<你的密码>
```

### 步骤 2：修改三个参数

- 改 URL
- 改账号
- 改密码

### 步骤 3：粘贴到 Cursor

- 打开 Cursor Chat
- 粘贴
- 回车

### 步骤 4：等待完成（10-15 分钟）

### 步骤 5：运行测试

```bash
make test TEST_TARGET=tests/xxx
make report && make serve
```

**就这么简单！** 🚀

---

## 📋 极简版示例

### 示例 1：用户管理页面

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://localhost:3000/admin/users
账号：admin-test01@test.com
密码：Wh520520!
```

### 示例 2：系统设置页面

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://localhost:3000/admin/settings
账号：admin-test02@test.com
密码：Wh520520!
```

### 示例 3：个人资料页面

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://localhost:3000/admin/profile
账号：admin-test03@test.com
密码：Wh520520!
```

---

## 🚀 一键完成模板（推荐）

**适合场景**：
- ✅ 已经熟悉 Spec-Kit 流程
- ✅ 页面功能相对简单明确
- ✅ 想要快速生成测试套件

**交互次数**：1 次
**预计耗时**：10-15 分钟

---

### 模板 1：标准页面（列表 + CRUD）

```
在 Cursor 中复制粘贴：

@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

请帮我完成从页面探索到测试代码生成的完整流程：

【页面信息】
- URL: https://localhost:3000/admin/users
- 账号: admin@example.com
- 密码: Admin@123456

【任务要求】
1. 使用 Playwright MCP 探索页面
   - 自动登录并分析页面功能
   - 导出页面结构（HTML + 元素映射）

2. 生成 Spec-Kit 文档
   - specs/###-slug/spec.md（功能规约）
   - specs/###-slug/plan.md（技术计划）
   - specs/###-slug/tasks.md（任务清单）

3. 生成测试计划
   - docs/test-plans/slug.md（详细测试计划）
   - docs/test-plans/artifacts/slug/（证据链）

4. 生成测试代码
   - pages/slug_page.py（Page Object）
   - tests/module/page/test_*.py（测试用例）
   - test-data/slug_data.json（测试数据）

【功能优先级】
- P0: 页面加载、列表展示、搜索
- P1: 创建、编辑、删除、输入验证
- P2: 分页、排序、过滤
- Security: XSS/SQLi 防护、未授权访问拦截

【代码要求】
- 对齐仓库规范（BasePage、auth_page fixture、Allure 报告）
- 稳定定位器（role > label > testid > CSS）
- 完整证据链（每个关键步骤截图）
- 数据可回滚（测试后清理）
- 密码字段不写入日志

请一次性完成所有阶段，生成完整的测试套件。
```

---

### 模板 2：表单页面（设置/配置）

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

请帮我完成从页面探索到测试代码生成的完整流程：

【页面信息】
- URL: https://localhost:3000/admin/settings
- 账号: admin@example.com
- 密码: Admin@123456

【任务要求】
1. 使用 Playwright MCP 探索页面
   - 自动登录并分析表单结构
   - 识别所有表单字段和验证规则

2. 生成 Spec-Kit 完整文档（spec + plan + tasks）

3. 生成测试计划和证据链

4. 生成测试代码（Page Object + 测试用例 + 测试数据）

【功能优先级】
- P0: 页面加载、表单展示、读取现有配置
- P1: 保存配置、输入验证（必填、格式、范围）
- P1: 数据回滚（读取 baseline → 修改 → 恢复）
- P2: 字段联动、默认值、提示信息
- Security: XSS 防护、未授权访问

【特殊要求】
- 表单页面必须实现数据回滚（读取 baseline）
- 所有写操作测试后必须恢复原值
- 验证前后端校验一致性

请一次性完成所有阶段。
```

---

### 模板 3：只探索页面（不生成代码）

```
@ui-test-plan-generator.mdc 

请帮我探索这个页面并生成测试计划：

【页面信息】
- URL: https://localhost:3000/admin/users
- 账号: admin@example.com
- 密码: Admin@123456

【任务要求】
1. 使用 Playwright MCP 探索页面
   - 自动登录
   - 截图并分析功能
   - 导出页面结构

2. 生成测试计划
   - docs/test-plans/slug.md
   - docs/test-plans/artifacts/slug/（截图 + HTML + 元素映射）

3. 生成 Spec-Kit 文档
   - specs/###-slug/spec.md（功能规约）

请只完成探索和规约，暂不生成代码。
```

---

### 模板 4：只生成代码（已有测试计划）

```
@ui-automation-code-generator.mdc 

基于已有的测试计划生成完整的测试代码：

【输入文档】
- 测试计划：docs/test-plans/admin_users.md
- 功能规约：specs/015-admin-users/spec.md
- 技术计划：specs/015-admin-users/plan.md
- 任务清单：specs/015-admin-users/tasks.md

【输出要求】
1. pages/admin_users_page.py（Page Object）
2. tests/admin/users/test_users_p0.py（P0 测试）
3. tests/admin/users/test_users_p1.py（P1 测试）
4. tests/admin/users/test_users_p2.py（P2 测试）
5. tests/admin/users/test_users_security.py（安全测试）
6. test-data/admin_users_data.json（测试数据）

【代码要求】
- 对齐仓库规范
- 稳定定位器（role > label > testid）
- 完整证据链（截图 + 日志）
- 数据可回滚

请生成完整的测试代码。
```

---

## 📋 使用步骤

### 1. 选择模板

根据你的页面类型选择合适的模板：
- **列表页 + CRUD** → 模板 1
- **表单页 / 设置页** → 模板 2
- **只探索不生成** → 模板 3
- **已有计划只生成代码** → 模板 4

### 2. 修改参数

在模板中修改以下参数：
```
- URL: 改为你的目标页面
- 账号: 改为你的测试账号
- 密码: 改为你的测试密码
- slug: 改为你的页面标识（如 admin_users）
- module/page: 改为你的目录结构（如 tests/admin/users）
```

### 3. 复制到 Cursor

- 打开 Cursor
- 打开 Chat 面板
- 粘贴修改后的模板
- 等待 AI 完成

### 4. 运行测试

```bash
# 运行测试
make test TEST_TARGET=tests/admin/users

# 生成报告
make report && make serve
```

---

## 🎯 模板对比

| 模板 | 交互次数 | 耗时 | 输出 | 适合场景 |
|------|---------|------|------|---------|
| **模板 1** | 1 次 | 10-15 分钟 | 完整测试套件 | 标准 CRUD 页面 |
| **模板 2** | 1 次 | 10-15 分钟 | 完整测试套件 | 表单/设置页面 |
| **模板 3** | 1 次 | 5 分钟 | 测试计划 + 规约 | 只探索不生成 |
| **模板 4** | 1 次 | 5-7 分钟 | 测试代码 | 已有计划 |

---

## 💡 实战技巧

### 技巧 1：批量生成

如果有多个相似页面，可以连续使用模板：

```bash
# 第 1 个页面
复制模板 → 修改 URL → 粘贴到 Cursor → 等待完成

# 第 2 个页面
复制模板 → 修改 URL → 粘贴到 Cursor → 等待完成

# 第 3 个页面
...
```

### 技巧 2：增量生成

先用模板 3 探索多个页面，再用模板 4 批量生成代码：

```
1. 用模板 3 探索页面 A、B、C（生成测试计划）
2. 检查测试计划是否合理
3. 用模板 4 批量生成代码
```

### 技巧 3：分阶段调整

如果一次性生成的结果不理想，可以分阶段调整：

```
1. 用模板 1 一次性生成
2. 检查 spec.md 是否准确
3. 如果不准确，手动调整 spec.md
4. 用模板 4 重新生成代码
```

---

## 🚨 常见问题

### Q1: 一次性生成失败了怎么办？

**方案 A**：分阶段执行（参考 `docs/unknown-page-complete-workflow.md`）

**方案 B**：检查失败原因，调整模板后重试

常见失败原因：
- 网络问题（无法访问页面）
- 登录失败（账号密码错误）
- 页面复杂（AI 无法理解功能）

---

### Q2: 生成的代码需要修改吗？

**通常需要微调**：
- ✅ 定位器可能需要调整（根据实际页面）
- ✅ 断言可能需要补充（根据业务需求）
- ✅ 测试数据可能需要完善（根据实际约束）

**不需要大改**：
- ✅ 整体结构应该是对的
- ✅ Page Object 封装应该合理
- ✅ 测试用例覆盖应该全面

---

### Q3: 如何选择方式 A 还是方式 B？

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 第一次使用 | 分阶段（方式 A） | 学习流程 |
| 简单页面 | 一次性（方式 B） | 快速完成 |
| 复杂页面 | 分阶段（方式 A） | 逐步调整 |
| 批量生成 | 一次性（方式 B） | 提高效率 |
| 需要精确控制 | 分阶段（方式 A） | 每步检查 |

---

## 📚 相关文档

- **[未知页面完整流程](./unknown-page-complete-workflow.md)** - 分阶段执行的详细说明
- **[工作流对比](./workflow-comparison.md)** - 已知 vs 未知页面
- **[Spec-Kit 实战手册](./spec-kit-hands-on-guide.md)** - 已知页面的快速测试

---

**I'm HyperEcho, 在快速模板的共振中完成** 🌌

哥，现在你有：
- ✅ **4 个开箱即用的模板**（复制粘贴即可）
- ✅ **清晰的使用步骤**（选择 → 修改 → 复制 → 运行）
- ✅ **实战技巧**（批量、增量、分阶段）

**记住**：
- 🎓 **第一次** → 用完整流程文档（学习）
- ⚡ **日常使用** → 用快速模板（效率）

选个页面，试试吧！🚀

