# 未知页面完整测试流程：从零到完整测试的终极工作流

**I'm HyperEcho, 在共振着完整工作流的频率** 🌌

---

## 🎯 场景定义

**输入**：
- ✅ URL：`https://localhost:3000/admin/users`
- ✅ 账号：`admin@example.com`
- ✅ 密码：`Admin@123456`
- ❌ 其他信息：**完全未知**

**目标**：
- ✅ 生成完整的功能规约
- ✅ 生成可执行的测试代码
- ✅ 生成详细的测试报告
- ✅ 全程有证据链可追溯

---

## 📊 完整流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     未知页面 → 完整测试                           │
│                     (6 个阶段，30 分钟完成)                       │
└─────────────────────────────────────────────────────────────────┘

【阶段 0】页面探索（5 分钟）
─────────────────────────────────────────
  工具：Playwright MCP (浏览器自动化)
  输入：URL + 账号 + 密码
  输出：
    ✓ 页面截图
    ✓ HTML 结构
    ✓ 元素列表
    ✓ 功能理解
  证据：docs/test-plans/artifacts/<slug>/
    ├── page.png
    ├── visible.html
    ├── visible.txt
    └── metadata.json

           ↓ (页面证据链)

【阶段 1】功能规约（5 分钟）
─────────────────────────────────────────
  工具：/speckit.specify (Spec-Kit)
  输入：页面证据链 + 功能理解
  输出：specs/###-<slug>/spec.md
    ✓ 用户故事（按优先级）
    ✓ 验收标准（可测量）
    ✓ 风险评估
    ✓ 范围界定
  价值：定义 WHAT（要测什么）

           ↓ (功能规约)

【阶段 2】测试计划（5 分钟）
─────────────────────────────────────────
  工具：@ui-test-plan-generator.mdc + /speckit.plan
  输入：spec.md + 页面证据链
  输出：
    ✓ docs/test-plans/<slug>.md (详细测试计划)
    ✓ specs/###-<slug>/plan.md (技术计划)
  内容：
    ✓ 元素定位器映射
    ✓ 用例设计（P0/P1/P2/security）
    ✓ 数据设计（valid/invalid/boundary）
    ✓ 自动化策略
  价值：定义 HOW（怎么测）

           ↓ (测试计划)

【阶段 3】任务分解（3 分钟）
─────────────────────────────────────────
  工具：/speckit.tasks
  输入：spec.md + plan.md
  输出：specs/###-<slug>/tasks.md
    ✓ 分阶段任务清单
    ✓ 可追踪的验收条件
    ✓ 并行标记
  价值：定义执行步骤（可追踪）

           ↓ (任务清单)

【阶段 4】代码生成（7 分钟）
─────────────────────────────────────────
  工具：@ui-automation-code-generator.mdc
  输入：测试计划 + tasks.md
  输出：
    ✓ pages/<slug>_page.py (Page Object)
    ✓ tests/<module>/<page>/test_*.py (测试代码)
    ✓ test-data/<slug>_data.json (测试数据)
  质量：
    ✓ 稳定定位器
    ✓ 完整断言
    ✓ 证据链（截图 + 日志）
  价值：生成可执行代码

           ↓ (可执行代码)

【阶段 5】执行验证（5 分钟）
─────────────────────────────────────────
  工具：make test + Allure
  输入：测试代码
  输出：
    ✓ 测试执行结果
    ✓ Allure 报告
    ✓ 截图证据
  验证：
    ✓ P0 测试通过
    ✓ 关键步骤有截图
    ✓ 失败有清晰诊断
  价值：验证质量 + 生成证据

           ↓ (测试报告)

✅ 完成！完整的测试套件已就绪
```

---

## 🚀 实战演示：admin/users 页面

### 环境准备

```bash
# 确认环境
cd /Users/wanghuan/aelf/Cursor/playwright-test-scaffold

# 确认服务运行
# 浏览器访问：https://localhost:3000/admin/users
# 确认可以用 admin@example.com / Admin@123456 登录
```

---

## 💡 两种执行方式

### 🎓 方式 A：分阶段执行（推荐新手）

**特点**：每个阶段单独执行，可以检查每个阶段的输出

**适合**：
- ✅ 第一次使用 Spec-Kit
- ✅ 需要学习完整流程
- ✅ 复杂页面需要逐步调整

**交互次数**：5 次（阶段 0 → 1 → 2 → 3 → 4）

---

### ⚡ 方式 B：一次性完成（推荐熟练用户）

**特点**：一次性告诉 AI 完成所有阶段，快速高效

**适合**：
- ✅ 已经熟悉流程
- ✅ 简单页面，功能明确
- ✅ 批量创建测试

**交互次数**：1-2 次（探索 + 生成全套）

**一键完成模板**：

```
在 Cursor 中一次性输入：

@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 
@.cursor/rules/quality/test-case-standards.mdc 

请帮我完成从页面探索到测试代码生成的完整流程：

【页面信息】
- URL: https://localhost:3000/admin/users
- 账号: admin@example.com
- 密码: Admin@123456

【任务要求】
1. 使用 Playwright MCP 探索页面
   - 自动登录
   - 分析页面功能
   - 导出页面结构

2. 生成 Spec-Kit 文档
   - specs/015-admin-users/spec.md（功能规约）
   - specs/015-admin-users/plan.md（技术计划）
   - specs/015-admin-users/tasks.md（任务清单）

3. 生成测试计划
   - docs/test-plans/admin_users.md（详细测试计划）
   - docs/test-plans/artifacts/admin_users/（证据链）

4. 生成测试代码
   - pages/admin_users_page.py（Page Object）
   - tests/admin/users/test_*.py（测试用例）
   - test-data/admin_users_data.json（测试数据）

【功能优先级】
- P0: 查看列表、搜索
- P1: 创建、编辑、删除用户
- P2: 角色管理、分页
- Security: XSS/SQLi 防护、未授权访问拦截

【代码要求】
- 对齐仓库规范（BasePage、auth_page fixture、Allure 报告）
- 稳定定位器（role > label > testid）
- 完整证据链（每个关键步骤截图）
- 数据可回滚（测试后清理）

请一次性完成所有阶段，生成完整的测试套件。
```

**AI 会自动**：
1. ✅ 探索页面并生成测试计划
2. ✅ 生成 Spec-Kit 文档（spec.md, plan.md, tasks.md）
3. ✅ 生成测试代码（Page Object + 测试用例 + 测试数据）

**然后你只需要**：
```bash
# 运行测试
make test TEST_TARGET=tests/admin/users

# 查看报告
make report && make serve
```

---

## 📊 两种方式对比

| 维度 | 方式 A：分阶段执行 | 方式 B：一次性完成 |
|------|-------------------|-------------------|
| **交互次数** | 5 次 | 1-2 次 |
| **耗时** | 30 分钟 | 10-15 分钟 |
| **可控性** | 高（每步检查） | 中（依赖 AI） |
| **学习价值** | 高（理解流程） | 低（快速完成） |
| **出错处理** | 容易定位 | 需要重新执行 |
| **适合场景** | 学习、复杂页面 | 日常、简单页面 |

**推荐策略**：
- 🎓 **第一次使用** → 方式 A（学习流程）
- ⚡ **日常使用** → 方式 B（提高效率）

---

## 🎯 本文档展示方式

**本文档采用方式 A（分阶段执行）**，因为：
- ✅ 更容易理解每个阶段的作用
- ✅ 可以看到每个阶段的输入输出
- ✅ 适合学习和参考

**如果你已经熟悉流程，直接使用方式 B 的一键完成模板即可！**

---

## 【阶段 0】页面探索（5 分钟）⭐

### 一键启动：让 AI 自动探索页面

**在 Cursor 中输入**：

```
@ui-test-plan-generator.mdc 

帮我探索这个页面并生成测试计划：
- URL: https://localhost:3000/admin/users
- 账号: admin@example.com
- 密码: Admin@123456

请：
1. 使用 Playwright MCP 打开页面
2. 登录（如果需要）
3. 截图并导出页面结构
4. 分析页面功能
5. 生成完整的测试计划
```

**AI 会自动完成所有操作**：
1. ✅ 自动打开 Playwright 浏览器
2. ✅ 导航到登录页
3. ✅ 输入账号密码登录
4. ✅ 导航到目标页面 `/admin/users`
5. ✅ 截图并分析页面功能
6. ✅ 导出页面结构（HTML + 元素列表）
7. ✅ 生成完整的测试计划

> 💡 **提示**：你不需要手动打开浏览器或操作页面，AI 会自动处理所有步骤！

**预期输出**：

```
✅ 生成了：
docs/test-plans/admin_users.md
docs/test-plans/artifacts/admin_users/
├── page.png           ← 页面截图
├── visible.html       ← 页面 HTML
├── visible.txt        ← 可见文本
└── metadata.json      ← 元素映射
```

**metadata.json 示例**：

```json
{
  "slug": "admin_users",
  "url": "https://localhost:3000/admin/users",
  "title": "User Management",
  "needs_auth": true,
  "page_type": "LIST",
  "elements": {
    "search_input": {
      "role": "searchbox",
      "label": "Search users",
      "selector": "[aria-label='Search users']"
    },
    "create_button": {
      "role": "button",
      "name": "Create User",
      "selector": "role=button[name='Create User']"
    },
    "user_table": {
      "role": "table",
      "headers": ["Username", "Email", "Role", "Actions"]
    }
  },
  "features_detected": [
    "Search/filter users",
    "Create new user",
    "Edit user",
    "Delete user",
    "Assign roles"
  ]
}
```

---

## 【阶段 1】功能规约（5 分钟）📝

### 步骤 1.1：启动 Spec-Kit 规约生成

**在 Cursor 中输入**：

```
/speckit.specify

基于刚才探索的 admin/users 页面，生成功能规约。

页面功能（从探索中发现）：
1. 用户列表展示
   - 显示用户名、邮箱、角色
   - 支持分页
2. 搜索用户
   - 可按用户名或邮箱搜索
3. 创建用户
   - 必填：用户名、邮箱、密码
   - 可选：角色分配
4. 编辑用户
   - 修改用户信息
5. 删除用户
   - 删除确认对话框
6. 角色管理
   - 分配/移除角色

优先级：
- P0: 查看列表、搜索
- P1: 创建、编辑、删除
- P2: 角色分配、分页

安全要求：
- 未登录用户应重定向
- XSS 注入不能执行
- SQLi 注入不能导致 5xx
- 删除操作需要确认

参考测试计划：docs/test-plans/admin_users.md
```

**AI 自动生成**：

```
✅ 创建了：specs/015-admin-users/spec.md
```

**生成的 spec.md 包含**：

```markdown
# admin_users - 用户管理功能规约

## 0. 核心信息
- **slug**: `admin_users`
- **URL**: `https://localhost:3000/admin/users`
- **页面类型**: LIST
- **是否需要登录态**: 是

## 1. 用户目标（User Story）

### US-1：查看用户列表（P0）🎯 MVP
**作为** 系统管理员  
**我想要** 查看系统中所有用户的列表  
**以便于** 了解当前用户状况并进行管理

**验收场景**：
- ✅ Given: 管理员已登录
- ✅ When: 访问用户管理页面
- ✅ Then: 显示用户列表（用户名、邮箱、角色）

### US-2：搜索用户（P0）
**作为** 系统管理员  
**我想要** 通过用户名或邮箱搜索用户  
**以便于** 快速找到目标用户

### US-3：创建用户（P1）
**作为** 系统管理员  
**我想要** 创建新用户账号  
**以便于** 为新员工开通系统访问权限

**边缘情况**：
- 用户名已存在
- 邮箱已存在
- 密码不符合安全策略
- XSS/SQLi 注入

### US-4：编辑用户（P1）
### US-5：删除用户（P1）
### US-6：角色管理（P2）

## 2. 范围（In/Out）

**In Scope**：
- ✅ 用户 CRUD 操作
- ✅ 搜索和过滤
- ✅ 基本输入验证
- ✅ XSS/SQLi 防护验证

**Out of Scope**：
- ❌ 用户导入/导出
- ❌ 批量操作
- ❌ 权限细粒度配置

## 3. 风险评估

| 风险 | 严重性 | 缓解措施 |
|------|--------|----------|
| 未授权访问 | 高 | 验证登录态拦截 |
| XSS 注入 | 高 | 安全测试套件 |
| 数据污染 | 中 | 测试后清理 |

## 4. 验收标准（Acceptance Criteria）

### FR-001：用户列表加载
- ✅ 页面加载时间 < 2s
- ✅ 显示至少：用户名、邮箱、角色
- ✅ 空状态有提示

### FR-002：搜索功能
- ✅ 支持用户名搜索
- ✅ 支持邮箱搜索
- ✅ 无结果有提示

### FR-003：创建用户
- ✅ 必填字段验证
- ✅ 邮箱格式验证
- ✅ 密码强度验证
- ✅ 重复用户名/邮箱拒绝

### FR-004：安全防护
- ✅ XSS 载荷不执行
- ✅ SQLi 载荷不导致 5xx
- ✅ 未登录用户被重定向

## 5. 成功标准
- ✅ P0 测试 100% 通过
- ✅ P1 测试 > 95% 通过
- ✅ 安全测试全部通过
- ✅ 关键步骤有截图证据
```

---

## 【阶段 2】测试计划（5 分钟）📋

### 步骤 2.1：生成技术计划

**在 Cursor 中输入**：

```
/speckit.plan

基于 specs/015-admin-users/spec.md 生成技术计划
```

**AI 自动生成**：

```
✅ 创建了：specs/015-admin-users/plan.md
```

**生成的 plan.md 包含**：

```markdown
# admin_users - 技术实现计划

## 1. 技术栈
- **框架**: Playwright (Python)
- **测试运行器**: pytest + pytest-playwright
- **报告**: Allure
- **基类**: core/base_page.py:BasePage

## 2. 项目结构

### 代码层
```
pages/
└── admin_users_page.py          # 页面对象

tests/admin/users/
├── conftest.py                  # fixtures
├── _helpers.py                  # 辅助函数
├── test_users_p0.py            # P0 测试
├── test_users_p1.py            # P1 测试
├── test_users_p2.py            # P2 测试
└── test_users_security.py      # 安全测试

test-data/
└── admin_users_data.json        # 测试数据
```

## 3. 页面对象设计

### AdminUsersPage 职责
- ✅ 封装定位器（稳定 selectors）
- ✅ 封装操作（search_user / create_user / delete_user）
- ✅ 封装断言辅助（get_user_list / is_user_visible）

### 定位器策略
- 搜索框：`role=searchbox[name='Search users']`
- 创建按钮：`role=button[name='Create User']`
- 用户表格：`role=table`

## 4. 测试数据设计

### Valid Data
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Test@123456",
  "role": "User"
}
```

### Invalid Data
```json
{
  "xss_username": "<script>alert('xss')</script>",
  "sqli_email": "' OR '1'='1",
  "invalid_email": "not-an-email",
  "weak_password": "123456"
}
```

## 5. 测试策略

### P0 测试（关键路径）
- ✅ 页面加载
- ✅ 列表显示
- ✅ 搜索功能

### P1 测试（核心功能）
- ✅ 创建用户
- ✅ 编辑用户
- ✅ 删除用户
- ✅ 输入验证

### P2 测试（增强功能）
- ✅ 分页
- ✅ 排序
- ✅ 角色管理

### Security 测试
- ✅ XSS 防护
- ✅ SQLi 防护
- ✅ 未授权访问拦截

## 6. 回滚策略
- ✅ 测试创建的用户在测试结束后删除
- ✅ 使用独特的测试数据标识（test_<timestamp>）
```

### 步骤 2.2：验证测试计划已存在

**此时你应该已经有了**：

```
✅ docs/test-plans/admin_users.md（阶段 0 生成的详细测试计划）
✅ specs/015-admin-users/plan.md（刚生成的技术计划）
```

**两者的区别**：
- `docs/test-plans/admin_users.md`：详细的测试计划，包含具体的用例设计、数据设计
- `specs/015-admin-users/plan.md`：技术实现计划，聚焦架构和实现策略

---

## 【阶段 3】任务分解（3 分钟）✅

**在 Cursor 中输入**：

```
/speckit.tasks

基于 specs/015-admin-users/spec.md 和 plan.md 生成任务清单
```

**AI 自动生成**：

```
✅ 创建了：specs/015-admin-users/tasks.md
```

**生成的 tasks.md 包含**：

```markdown
# 任务：admin_users - 用户管理

## 第 1 阶段：设置 📋
- [ ] T001 创建 pages/admin_users_page.py
- [ ] T002 [P] 准备测试数据 test-data/admin_users_data.json

## 第 2 阶段：基础设施 🏗️
- [ ] T003 实现页面定位器
- [ ] T004 实现基础操作方法（navigate / is_loaded）
- [ ] T005 实现辅助方法（_helpers.py）

## 第 3 阶段：用户故事 1 - 查看列表（P0）🎯 MVP
- [ ] T006 [US1] 实现 test_users_p0.py::test_view_user_list
- [ ] T007 [US1] 验证：列表加载、数据显示、截图证据

## 第 4 阶段：用户故事 2 - 搜索（P0）🔍
- [ ] T008 [US2] 实现 test_users_p0.py::test_search_user
- [ ] T009 [US2] 验证：搜索结果、无结果提示

## 第 5 阶段：用户故事 3 - 创建用户（P1）➕
- [ ] T010 [US3] 实现 test_users_p1.py::test_create_user_valid
- [ ] T011 [US3] 实现 test_users_p1.py::test_create_user_duplicate
- [ ] T012 [US3] 实现 test_users_p1.py::test_create_user_invalid_email
- [ ] T013 [US3] 验证：创建成功、错误提示、回滚

## 第 6 阶段：安全测试（P1-security）🔒
- [ ] T014 [SEC] 实现 test_users_security.py::test_xss_username
- [ ] T015 [SEC] 实现 test_users_security.py::test_sqli_email
- [ ] T016 [SEC] 实现 test_users_security.py::test_unauth_redirect
- [ ] T017 [SEC] 验证：XSS 不执行、SQLi 不 5xx、拦截生效

## 第 7 阶段：执行验证 🚀
- [ ] T018 运行 P0 测试：`make test-p0 TEST_TARGET=tests/admin/users`
- [ ] T019 运行完整测试：`make test TEST_TARGET=tests/admin/users`
- [ ] T020 生成报告：`make report && make serve`

## 第 8 阶段：验收 ✅
- [ ] T021 P0 测试 100% 通过
- [ ] T022 P1 测试 > 95% 通过
- [ ] T023 安全测试全部通过
- [ ] T024 关键步骤有截图证据
- [ ] T025 测试后数据已清理
```

---

## 【阶段 4】代码生成（7 分钟）💻

### 步骤 4.1：生成代码

**在 Cursor 中输入**：

```
@ui-automation-code-generator.mdc 

基于以下资源生成完整的测试代码：
- 测试计划：docs/test-plans/admin_users.md
- 功能规约：specs/015-admin-users/spec.md
- 技术计划：specs/015-admin-users/plan.md
- 任务清单：specs/015-admin-users/tasks.md

请生成：
1. pages/admin_users_page.py
2. tests/admin/users/test_users_p0.py
3. tests/admin/users/test_users_p1.py
4. tests/admin/users/test_users_security.py
5. test-data/admin_users_data.json

要求：
- 对齐仓库规范（BasePage、auth_page fixture、Allure 报告）
- 稳定定位器（role > label > testid）
- 完整证据链（每个关键步骤截图）
- 数据可回滚（测试后清理）
```

**AI 自动生成**：

```
✅ 创建了：
pages/admin_users_page.py
tests/admin/users/
├── conftest.py
├── _helpers.py
├── test_users_p0.py
├── test_users_p1.py
├── test_users_p2.py
└── test_users_security.py
test-data/admin_users_data.json
```

### 步骤 4.2：代码示例（自动生成）

**pages/admin_users_page.py**：

```python
from core.base_page import BasePage
from utils.logger import get_logger
import allure

logger = get_logger(__name__)


# ============================================================
# 页面对象：AdminUsersPage
# - 目标：封装用户管理页面的稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class AdminUsersPage(BasePage):
    # SELECTORS（优先 role/label/testid）
    SEARCH_INPUT = "role=searchbox[name='Search users']"
    CREATE_BUTTON = "role=button[name='Create User']"
    USER_TABLE = "role=table"
    USER_ROWS = "role=table >> role=row"
    
    # Form fields
    USERNAME_INPUT = "[name='userName']"
    EMAIL_INPUT = "[name='email']"
    PASSWORD_INPUT = "[name='password']"
    ROLE_SELECT = "[name='role']"
    SUBMIT_BUTTON = "role=button[name='Submit']"
    
    URL = "/admin/users"
    page_loaded_indicator = "role=table"
    
    @allure.step("导航到用户管理页面")
    def navigate(self) -> None:
        self.goto(self.URL)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        return self.is_visible(self.page_loaded_indicator, timeout=5000)
    
    @allure.step("搜索用户: {query}")
    def search_user(self, query: str) -> None:
        self.fill(self.SEARCH_INPUT, query)
        self.wait_for_page_load()
    
    @allure.step("获取用户列表")
    def get_user_list(self) -> list:
        rows = self.page.locator(self.USER_ROWS).all()
        return [row.inner_text() for row in rows if row.is_visible()]
    
    @allure.step("点击创建用户")
    def click_create(self) -> None:
        self.click(self.CREATE_BUTTON)
        self.wait_for_page_load()
    
    @allure.step("填写用户表单")
    def fill_user_form(self, username: str, email: str, password: str, role: str = "User") -> None:
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.EMAIL_INPUT, email)
        # 密码字段使用 page.fill 避免日志泄露
        self.page.fill(self.PASSWORD_INPUT, password)
        logger.debug(f"填写密码: ***")
        self.page.select_option(self.ROLE_SELECT, role)
    
    @allure.step("提交表单")
    def submit_form(self) -> None:
        self.click(self.SUBMIT_BUTTON)
        self.wait_for_page_load()
    
    @allure.step("验证用户是否存在: {username}")
    def is_user_visible(self, username: str) -> bool:
        return self.is_visible(f"text={username}")
```

**tests/admin/users/test_users_p0.py**：

```python
import allure
import pytest
from pages.admin_users_page import AdminUsersPage


@allure.feature("用户管理")
@allure.story("查看用户列表")
@pytest.mark.P0
def test_view_user_list(auth_page):
    """P0: 管理员可以查看用户列表"""
    page = AdminUsersPage(auth_page)
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
        page.take_screenshot("navigate")
    
    with allure.step("验证页面加载"):
        assert page.is_loaded(), "页面未正确加载"
    
    with allure.step("验证用户列表显示"):
        users = page.get_user_list()
        assert len(users) > 0, "用户列表不应为空"
        page.take_screenshot("user_list")
    
    allure.attach(
        f"用户数量: {len(users)}",
        name="用户列表信息",
        attachment_type=allure.attachment_type.TEXT
    )


@allure.feature("用户管理")
@allure.story("搜索用户")
@pytest.mark.P0
def test_search_user(auth_page):
    """P0: 管理员可以搜索用户"""
    page = AdminUsersPage(auth_page)
    
    page.navigate()
    
    with allure.step("搜索用户 'admin'"):
        page.search_user("admin")
        page.take_screenshot("search_result")
    
    with allure.step("验证搜索结果"):
        users = page.get_user_list()
        assert any("admin" in user.lower() for user in users), "搜索结果中应包含 'admin'"
```

**tests/admin/users/test_users_security.py**：

```python
import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from utils.data_manager import DataManager


@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_xss_username(auth_page):
    """安全: XSS 载荷不应执行"""
    page = AdminUsersPage(auth_page)
    dm = DataManager()
    data = dm.load_json("test-data/admin_users_data.json")
    xss_payload = data["invalid"]["xss_username"]
    
    page.navigate()
    page.click_create()
    
    with allure.step(f"输入 XSS 载荷: {xss_payload}"):
        page.fill_user_form(
            username=xss_payload,
            email="test@example.com",
            password="Test@123456"
        )
        page.submit_form()
        page.take_screenshot("xss_attempt")
    
    with allure.step("验证 XSS 未执行"):
        # 验证没有弹出对话框（XSS 未执行）
        assert not page.page.evaluate("() => window.alert.called"), "XSS 不应执行"
        # 验证输入被转义显示
        if page.is_user_visible(xss_payload):
            # 如果显示，应该是转义后的文本，而非执行代码
            page.take_screenshot("xss_escaped")


@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_unauth_redirect(unauth_page):
    """安全: 未登录用户应被重定向"""
    page = AdminUsersPage(unauth_page)
    
    with allure.step("尝试访问用户管理页面"):
        page.navigate()
        page.take_screenshot("unauth_access")
    
    with allure.step("验证重定向到登录页"):
        assert "/account/login" in page.page.url.lower(), "应重定向到登录页"
```

---

## 【阶段 5】执行验证（5 分钟）🚀

### 步骤 5.1：运行测试

```bash
# 1. 先运行 P0 测试（冒烟测试）
make test-p0 TEST_TARGET=tests/admin/users

# 2. 如果 P0 通过，运行完整测试
make test TEST_TARGET=tests/admin/users

# 3. 生成 Allure 报告
make report

# 4. 查看报告
make serve
# 浏览器打开: http://127.0.0.1:59717
```

### 步骤 5.2：验证结果

**在 Allure 报告中检查**：

✅ **P0 测试通过率 = 100%**
- `test_view_user_list` ✅
- `test_search_user` ✅

✅ **P1 测试通过率 > 95%**
- `test_create_user_valid` ✅
- `test_create_user_duplicate` ✅
- `test_create_user_invalid_email` ✅

✅ **安全测试通过率 = 100%**
- `test_xss_username` ✅
- `test_sqli_email` ✅
- `test_unauth_redirect` ✅

✅ **证据链完整**
- 每个关键步骤有截图
- 失败用例有详细诊断
- 日志无敏感信息泄露

---

## 📊 完整文件清单

完成后，你会得到以下完整的文件结构：

```
playwright-test-scaffold/
│
├── specs/015-admin-users/
│   ├── spec.md                    ← 【阶段 1】功能规约
│   ├── plan.md                    ← 【阶段 2】技术计划
│   └── tasks.md                   ← 【阶段 3】任务清单
│
├── docs/test-plans/
│   ├── admin_users.md             ← 【阶段 0】测试计划
│   └── artifacts/admin_users/
│       ├── page.png               ← 【阶段 0】页面截图
│       ├── visible.html           ← 【阶段 0】页面 HTML
│       ├── visible.txt            ← 【阶段 0】可见文本
│       └── metadata.json          ← 【阶段 0】元素映射
│
├── pages/
│   └── admin_users_page.py        ← 【阶段 4】页面对象
│
├── tests/admin/users/
│   ├── conftest.py                ← 【阶段 4】fixtures
│   ├── _helpers.py                ← 【阶段 4】辅助函数
│   ├── test_users_p0.py           ← 【阶段 4】P0 测试
│   ├── test_users_p1.py           ← 【阶段 4】P1 测试
│   ├── test_users_p2.py           ← 【阶段 4】P2 测试
│   └── test_users_security.py     ← 【阶段 4】安全测试
│
├── test-data/
│   └── admin_users_data.json      ← 【阶段 4】测试数据
│
├── allure-results/                ← 【阶段 5】测试结果
├── allure-report/                 ← 【阶段 5】测试报告
└── screenshots/                   ← 【阶段 5】截图证据
```

---

## 🎯 流程总结

### ✅ 输入
- URL + 账号 + 密码

### ✅ 输出
1. **规约文档**：spec.md, plan.md, tasks.md
2. **测试计划**：详细的测试计划和元素映射
3. **可执行代码**：Page Object + 测试用例 + 测试数据
4. **测试报告**：Allure 报告 + 截图证据

### ✅ 证据链
- 页面探索 → 截图 + HTML + 元素映射
- 功能规约 → 用户故事 + 验收标准
- 测试计划 → 用例设计 + 数据设计
- 代码实现 → Page Object + 测试代码
- 执行结果 → Allure 报告 + 截图

### ✅ 质量保证
- ✅ 每个阶段有明确的输入输出
- ✅ 全程可追溯、可审计
- ✅ 代码符合仓库规范
- ✅ 测试数据可回滚

---

## 💡 最佳实践

### 1. 先探索，再规约
- ❌ 不要在不了解页面的情况下直接写规约
- ✅ 先用 MCP 探索页面，理解功能后再写规约

### 2. 规约驱动计划
- ❌ 不要跳过规约直接写测试计划
- ✅ 先定义 WHAT（规约），再定义 HOW（计划）

### 3. 计划驱动代码
- ❌ 不要手写测试代码
- ✅ 让 AI 基于测试计划生成代码

### 4. 代码驱动验证
- ❌ 不要只写代码不运行
- ✅ 立即运行测试，验证质量

### 5. 证据链完整
- ❌ 不要只有代码没有文档
- ✅ 每个阶段都落盘证据

---

## 🚀 快速启动模板

### 单命令启动（推荐新手）

创建一个脚本 `scripts/unknown-page-workflow.sh`：

```bash
#!/bin/bash

# 未知页面完整测试流程脚本
# 输入：URL + 账号 + 密码
# 输出：完整的测试套件

read -p "URL: " URL
read -p "账号: " EMAIL
read -sp "密码: " PASSWORD
echo ""

echo "🚀 启动完整工作流..."

echo "【阶段 0】页面探索..."
echo "请在 Cursor 中执行："
echo "@ui-test-plan-generator.mdc 探索页面：$URL"

read -p "完成阶段 0？(y/n) " done0
if [[ ! $done0 =~ ^[Yy]$ ]]; then exit 1; fi

echo "【阶段 1】功能规约..."
echo "请在 Cursor 中执行："
echo "/speckit.specify"

read -p "完成阶段 1？(y/n) " done1
if [[ ! $done1 =~ ^[Yy]$ ]]; then exit 1; fi

echo "【阶段 2】测试计划..."
echo "请在 Cursor 中执行："
echo "/speckit.plan"

read -p "完成阶段 2？(y/n) " done2
if [[ ! $done2 =~ ^[Yy]$ ]]; then exit 1; fi

echo "【阶段 3】任务分解..."
echo "请在 Cursor 中执行："
echo "/speckit.tasks"

read -p "完成阶段 3？(y/n) " done3
if [[ ! $done3 =~ ^[Yy]$ ]]; then exit 1; fi

echo "【阶段 4】代码生成..."
echo "请在 Cursor 中执行："
echo "@ui-automation-code-generator.mdc 生成代码"

read -p "完成阶段 4？(y/n) " done4
if [[ ! $done4 =~ ^[Yy]$ ]]; then exit 1; fi

echo "【阶段 5】执行验证..."
read -p "测试目标路径: " TEST_PATH
make test TEST_TARGET=$TEST_PATH
make report
make serve

echo "✅ 完整工作流完成！"
```

---

## 📚 相关文档

- **实战落地手册**：`docs/spec-kit-hands-on-guide.md`
- **快速入门**：`docs/spec-kit-quickstart.md`
- **框架详解**：`docs/spec-kit-guide.md`
- **UI 测试计划生成规则**：`.cursor/rules/ui-test-plan-generator.mdc`
- **UI 代码生成规则**：`.cursor/rules/ui-automation-code-generator.mdc`

---

**I'm HyperEcho, 在完整工作流的共振中完成** 🌌

哥，这就是**从未知页面到完整测试的终极工作流**！

**6 个阶段，30 分钟，从零到完整测试套件！**

现在，选一个你想测试的页面，开始你的第一次完整流程吧！🚀

