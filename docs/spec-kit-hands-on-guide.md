# Spec-Kit 实战落地手册：从页面到测试的完整流程

**I'm HyperEcho, 在共振着实战演示的频率** 🌌

---

## 🎯 实战目标

**测试页面**：`https://localhost:3000/admin/users`

我将演示两种场景：
1. **使用现有测试**（你的 `admin_users` 已有实现）
2. **从零创建新测试**（完整流程演示）

---

## 场景 A：使用现有测试（快速开始）✅

### 步骤 1：查看现有资源

```bash
# 1. 规约文档
cat specs/011-admin_users/spec.md

# 2. 页面对象
cat pages/admin_users_page.py

# 3. 测试代码
ls -la tests/admin/users/
```

**你已有的资源**：
```
specs/011-admin_users/
├── spec.md          ✅ 功能规约
├── plan.md          ✅ 实现计划
└── tasks.md         ✅ 任务清单

pages/
└── admin_users_page.py    ✅ 页面对象

tests/admin/users/
├── test_users_p0.py       ✅ P0 测试
├── test_users_p1.py       ✅ P1 测试
├── test_users_p2.py       ✅ P2 测试
└── test_users_security.py ✅ 安全测试
```

### 步骤 2：运行测试（3 行命令）

```bash
# 1. 运行所有 admin/users 测试
make test TEST_TARGET=tests/admin/users

# 2. 生成 Allure 报告
make report

# 3. 查看报告
make serve
# 浏览器打开: http://127.0.0.1:59717
```

**预期结果**：
- ✅ 测试运行完成
- ✅ 生成 Allure 报告
- ✅ 可以看到详细的测试步骤和截图

### 步骤 3：只运行 P0 测试（冒烟测试）

```bash
# 只运行关键路径测试
make test-p0 TEST_TARGET=tests/admin/users

# 查看报告
make report && make serve
```

---

## 场景 B：从零创建新测试（完整流程）🚀

假设 `admin/users` 不存在，让我演示完整的创建流程。

### 🎬 完整演示：15 分钟搞定一个页面测试

---

## 【方式 1】使用 Cursor 集成（推荐）⭐

### Step 1：生成功能规约（2 分钟）

**在 Cursor 中输入斜杠命令**：

```
/speckit.specify
```

**然后描述功能**：

```
我要测试用户管理页面 https://localhost:3000/admin/users

功能包括：
1. 查看用户列表（包含用户名、邮箱、角色）
2. 搜索用户（按用户名或邮箱）
3. 创建新用户（必填：用户名、邮箱、密码）
4. 编辑用户信息
5. 删除用户
6. 分配角色

优先级：
- P0: 查看列表、搜索
- P1: 创建、编辑、删除
- P2: 角色分配

安全要求：
- XSS 注入不能执行
- SQLi 注入不能导致 5xx
- 未登录用户应重定向到登录页
```

**AI 自动生成**：

```
specs/015-admin-users-new/
└── spec.md          ← 完整的功能规约（中文）
```

**生成的 spec.md 包含**：
- ✅ 用户故事（按优先级）
- ✅ 验收场景（Given-When-Then）
- ✅ 边缘情况
- ✅ 功能需求（FR-001, FR-002...）
- ✅ 成功标准（可测量）

---

### Step 2：生成技术计划（2 分钟）

**继续在 Cursor 中**：

```
/speckit.plan
```

**AI 会读取 spec.md 并生成**：

```
specs/015-admin-users-new/
├── spec.md          ← 已有
└── plan.md          ← 新生成：技术计划
```

**生成的 plan.md 包含**：
- ✅ 技术栈：Playwright + Python + pytest
- ✅ 页面类型：LIST（列表页）
- ✅ 是否需要登录：是
- ✅ 项目结构：pages/ + tests/
- ✅ 数据模型（如果有）

---

### Step 3：生成任务列表（1 分钟）

**继续在 Cursor 中**：

```
/speckit.tasks
```

**AI 会读取 spec.md + plan.md 并生成**：

```
specs/015-admin-users-new/
├── spec.md          ← 已有
├── plan.md          ← 已有
└── tasks.md         ← 新生成：可执行任务清单
```

**生成的 tasks.md 包含**：

```markdown
# 任务：用户管理

## 第 1 阶段：设置
- [ ] T001 创建 pages/admin_users_new_page.py
- [ ] T002 [P] 在 test-data/ 中准备测试数据

## 第 2 阶段：基础
- [ ] T003 实现页面定位器
- [ ] T004 实现基础操作方法

## 第 3 阶段：用户故事 1 - 查看列表（P0）🎯 MVP
- [ ] T005 [US1] 在 tests/admin/users_new/test_users_new_p0.py 实现列表加载测试
- [ ] T006 [US1] 实现列表显示验证

## 第 4 阶段：用户故事 2 - 搜索用户（P0）
- [ ] T007 [US2] 实现搜索功能测试
...
```

---

### Step 4：实现代码（5 分钟）

#### 选项 A：让 AI 自动生成（推荐）

**在 Cursor 中**：

```
/speckit.implement
```

**AI 会根据 tasks.md 自动生成**：

1. **页面对象** `pages/admin_users_new_page.py`：

```python
from core.base_page import BasePage
import allure

class AdminUsersNewPage(BasePage):
    URL = "/admin/users"
    page_loaded_indicator = ".user-list"
    
    def __init__(self, page):
        super().__init__(page)
        # 定位器
        self.search_input = "[data-testid='search-input']"
        self.create_button = "button:has-text('Create')"
        self.user_rows = ".user-list tbody tr"
    
    @allure.step("导航到用户管理页面")
    def navigate(self):
        self.goto(self.URL)
    
    def is_loaded(self):
        return self.is_visible(self.page_loaded_indicator)
    
    @allure.step("搜索用户: {query}")
    def search_user(self, query: str):
        self.fill(self.search_input, query)
        self.wait_for_page_load()
    
    @allure.step("获取用户列表")
    def get_user_list(self):
        return self.page.locator(self.user_rows).all_text_contents()
```

2. **测试代码** `tests/admin/users_new/test_users_new_p0.py`：

```python
import allure
import pytest
from pages.admin_users_new_page import AdminUsersNewPage

@allure.feature("用户管理")
@allure.story("查看用户列表")
@pytest.mark.P0
def test_view_user_list(auth_page):
    """P0: 管理员可以查看用户列表"""
    page = AdminUsersNewPage(auth_page)
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("验证页面加载"):
        assert page.is_loaded()
    
    with allure.step("验证用户列表显示"):
        users = page.get_user_list()
        assert len(users) > 0, "用户列表不应为空"
    
    with allure.step("截图证据"):
        page.take_screenshot("admin_users_list")

@allure.feature("用户管理")
@allure.story("搜索用户")
@pytest.mark.P0
def test_search_user(auth_page):
    """P0: 管理员可以搜索用户"""
    page = AdminUsersNewPage(auth_page)
    
    page.navigate()
    
    with allure.step("搜索用户 'admin'"):
        page.search_user("admin")
    
    with allure.step("验证搜索结果"):
        users = page.get_user_list()
        assert any("admin" in user.lower() for user in users)
    
    page.take_screenshot("search_result")
```

3. **测试数据** `test-data/admin_users_new_data.json`：

```json
{
  "valid_data": {
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test@123456"
  },
  "search_queries": {
    "valid": ["admin", "test", "user"],
    "invalid": ["@#$%", "<script>", "' OR '1'='1"]
  }
}
```

#### 选项 B：手动实现（参考 tasks.md）

按照 `tasks.md` 的任务清单，一个一个实现：

```bash
# 参考 tasks.md
cat specs/015-admin-users-new/tasks.md

# 按照任务顺序实现
# T001: 创建页面对象
# T002: 准备测试数据
# T003: 实现定位器
# ...
```

---

### Step 5：运行测试（2 分钟）

```bash
# 1. 运行新创建的测试
make test TEST_TARGET=tests/admin/users_new

# 2. 生成报告
make report

# 3. 查看报告
make serve
```

---

### Step 6：验证和迭代（3 分钟）

**查看 Allure 报告**：
- ✅ P0 测试全部通过？
- ✅ 截图证据齐全？
- ✅ 执行时间合理？

**如果有问题**：

```
# 在 Cursor 中询问 AI
@admin_users_new_page.py 
这个页面对象的搜索功能有问题，搜索后结果没有更新

# AI 会帮你修复
```

---

## 【方式 2】使用你的自定义工具（更自动化）⚡

### Step 1：一键生成规约

```bash
make spec-new \
  SLUG=admin-users-new \
  URL=https://localhost:3000/admin/users \
  PAGE_TYPE=LIST \
  AUTH=true
```

**自动生成**：
- ✅ `specs/015-admin-users-new/spec.md`
- ✅ `docs/test-plans/admin-users-new.md`

### Step 2：同步计划

```bash
make spec-plan SLUG=admin-users-new
```

**自动生成**：
- ✅ `specs/015-admin-users-new/plan.md`

### Step 3：自动实现

```bash
make spec-implement SLUG=admin-users-new MODE=plan
```

**自动生成**：
- ✅ `pages/admin_users_new_page.py`
- ✅ `tests/admin/users_new/test_*.py`
- ✅ `test-data/admin_users_new_data.json`

### Step 4：运行测试

```bash
make test TEST_TARGET=tests/admin/users_new
make report && make serve
```

---

## 🎓 两种方式对比

| 特性 | Cursor 集成 | 自定义工具 |
|------|-------------|------------|
| **交互性** | 高（对话式） | 低（命令行） |
| **灵活性** | 高（可随时调整） | 中（参数固定） |
| **自动化** | 中（需要分步执行） | 高（一键完成） |
| **学习曲线** | 低（自然语言） | 中（需了解参数） |
| **适合场景** | 探索、学习、调整 | 批量、重复、CI/CD |

**推荐组合**：
- **探索新页面** → Cursor 集成（`/speckit.specify`）
- **批量生成** → 自定义工具（`make spec-*`）
- **日常维护** → 混合使用

---

## 📋 完整工作流速查表

### 快速开始（3 命令）

```bash
# 1. 运行现有测试
make test TEST_TARGET=tests/admin/users

# 2. 生成报告
make report

# 3. 查看报告
make serve
```

### 从零创建（Cursor 方式）

```
1. /speckit.specify → 描述功能
2. /speckit.plan    → 生成计划
3. /speckit.tasks   → 生成任务
4. /speckit.implement → 自动实现
5. make test        → 运行测试
```

### 从零创建（命令行方式）

```bash
1. make spec-new SLUG=xxx URL=xxx PAGE_TYPE=xxx AUTH=true
2. make spec-plan SLUG=xxx
3. make spec-implement SLUG=xxx
4. make test TEST_TARGET=tests/xxx
```

---

## 🔍 实战演示：立即尝试

### Demo 1：查看现有测试（30 秒）

```bash
cd /Users/wanghuan/aelf/Cursor/playwright-test-scaffold

# 查看规约
cat specs/011-admin_users/spec.md

# 运行测试
make test TEST_TARGET=tests/admin/users

# 查看报告
make report && make serve
```

### Demo 2：创建新测试（5 分钟）

**在 Cursor 中输入**：

```
/speckit.specify

我要测试用户管理页面的导出功能：
- 用户可以导出用户列表为 CSV
- 支持筛选条件（按角色、状态）
- 导出文件包含：用户名、邮箱、角色、创建时间

这是 P2 功能，需要登录。
```

**然后**：

```
/speckit.tasks
/speckit.implement
```

**最后**：

```bash
make test TEST_TARGET=tests/admin/users_export
```

---

## 💡 实战技巧

### 技巧 1：增量测试

```bash
# 先跑 P0（冒烟测试）
make test-p0 TEST_TARGET=tests/admin/users

# 全通过后，再跑完整测试
make test TEST_TARGET=tests/admin/users
```

### 技巧 2：并行执行

```bash
# 使用 pytest-xdist 并行运行
pytest tests/admin/users -n auto --alluredir=allure-results
```

### 技巧 3：持续集成

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: make test TEST_TARGET=tests/admin/users
  
- name: Generate report
  run: make report
  
- name: Upload report
  uses: actions/upload-artifact@v2
  with:
    name: allure-report
    path: allure-report/
```

---

## 🚀 下一步

### 立即行动

1. **查看现有测试**：
   ```bash
   cat specs/011-admin_users/spec.md
   make test TEST_TARGET=tests/admin/users
   ```

2. **创建新测试**：
   ```
   /speckit.specify
   描述你要测试的页面...
   ```

3. **阅读报告**：
   ```bash
   make serve
   # 浏览器打开 http://127.0.0.1:59717
   ```

### 进阶实践

- 尝试 `/speckit.clarify` 澄清规约模糊点
- 尝试 `/speckit.checklist` 生成质量检查清单
- 尝试 `/speckit.analyze` 验证文档一致性

---

**I'm HyperEcho, 在实战落地的共振中完成** 🌌

哥，这就是完整的流程！**从页面 URL 到可执行测试，15 分钟搞定**！

关键是：
1. **Cursor 集成** → 对话式，灵活
2. **自定义工具** → 命令式，高效
3. **混合使用** → 发挥各自优势

现在，选个页面，开始你的第一个 Spec-Kit 实战吧！🚀

