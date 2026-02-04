# Admin Users UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `http://localhost:5173/admin/users`
- **slug**: `admin_users`
- **生成时间**: 2026-01-16 10:00:00
- **是否需要登录态**: 是
- **证据链目录**: `docs/test-plans/artifacts/admin_users/`

## 1. 页面概述
- **页面类型**: LIST
- **主要功能（用户任务流）**:
  - 进入用户管理页面并确认列表可见
  - 查看用户列表（分页/筛选/搜索）
  - 编辑用户信息
  - 删除用户（如支持）
  - 管理用户角色/权限
- **风险点**:
  - 鉴权/权限：未登录或权限不足时的跳转与提示必须正确
  - 数据安全：不得暴露敏感信息（密码/Token）
  - 稳定性：定位器漂移/异步加载导致 flaky
- **测试优先级**: 高（涉及用户管理，影响系统安全性）

## 2. 页面元素映射
### 2.1 关键元素识别

| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |
|---------|----------|----------|----------|--------|----------|----------|
| input | Search | 搜索输入 | role/name | `page.get_by_role("textbox", name="Search")` | 可输入 / 可清空 / 实时过滤 | 需要登录态 |
| button | Add User | 添加用户按钮 | role/name | `page.get_by_role("button", name="Add User")` | 可点击 / loading/禁用态 / 触发结果（弹窗/跳转） | 需要登录态 |
| table | Users Table | 用户列表表格 | role | `page.get_by_role("table")` | 可见 / 数据正确 / 分页正确 | 需要登录态 |
| button | Edit | 编辑按钮 | role/name | `page.get_by_role("button", name="Edit")` | 可点击 / 触发编辑弹窗 | 需要登录态 |
| button | Delete | 删除按钮 | role/name | `page.get_by_role("button", name="Delete")` | 可点击 / 确认对话框 / 删除成功 | 需要登录态 |
| link | Next Page | 下一页 | role/linkText | `page.get_by_role("link", name="Next")` | 可见 / 可交互 / 行为正确 | 需要登录态 |

### 2.2 页面对象设计（骨架）
```python
from core.base_page import BasePage

# ============================================================
# 页面对象：AdminUsersPage
# - 目标：封装稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class AdminUsersPage(BasePage):
    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）
    # SEARCH_INPUT = page.get_by_role("textbox", name="Search")
    # ADD_USER_BUTTON = page.get_by_role("button", name="Add User")
    # USERS_TABLE = page.get_by_role("table")
    # EDIT_BUTTON = page.get_by_role("button", name="Edit")
    # DELETE_BUTTON = page.get_by_role("button", name="Delete")
    # NEXT_PAGE_LINK = page.get_by_role("link", name="Next")

    def navigate(self) -> None:
        self.goto("http://localhost:5173/admin/users")

    def is_loaded(self) -> bool:
        # 以关键元素作为"已加载"判定
        return self.page.get_by_role("table").is_visible()

    # --------------------------------------------------------
    # 业务动作（示例）
    # --------------------------------------------------------
    def search_user(self, keyword: str) -> None:
        # TODO: 搜索用户；失败时保留截图与上下文（证据链）
        self.fill(self.SEARCH_INPUT, keyword)
        self.wait_for_timeout(500)  # 等待搜索响应

    def click_add_user(self) -> None:
        self.click(self.ADD_USER_BUTTON)

    def click_edit_user(self, user_email: str) -> None:
        # TODO: 根据用户邮箱找到对应行，点击编辑按钮
        pass

    def click_delete_user(self, user_email: str) -> None:
        # TODO: 根据用户邮箱找到对应行，点击删除按钮
        pass
```

## 3. 测试用例设计
### 3.1 功能测试用例
- **账号建议**:
  - **管理员账号 email（示例）**: `admin@example.com`（用于用户管理功能）
  - **普通账号 email（示例）**: `testuser@example.com`（用于测试编辑/删除操作）
  - **密码**: 运行期由环境变量/账号池提供；计划与任何落盘文件禁止写入密码

- **TC001**: 页面加载
  - **标签**: [@smoke @p0]
  - **前置条件**: 管理员登录
  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见
  - **预期结果**: 页面可用且无阻塞错误
  - **断言层级**: UI 状态
  - **优先级**: 高

- **TC002**: 用户列表加载
  - **标签**: [@p0]
  - **前置条件**: 管理员登录
  - **测试步骤**: 打开页面 → 等待用户列表/表格区域渲染
  - **预期结果**: 列表渲染成功（空态/加载态可接受，但不得 5xx）
  - **优先级**: 高

- **TC003**: 搜索过滤（Search...）
  - **标签**: [@p1]
  - **测试步骤**: 在 Search 输入框输入关键字 → 观察列表变化
  - **预期结果**: 列表过滤结果可观测（行数变化/空态提示）
  - **优先级**: 中

- **TC004**: 添加用户（如果支持）
  - **标签**: [@p0]
  - **前置条件**: 管理员登录
  - **测试步骤**: 点击 Add User → 填写用户信息 → 提交
  - **预期结果**: 用户创建成功；列表更新显示新用户
  - **优先级**: 高

- **TC005**: 编辑用户信息
  - **标签**: [@p0]
  - **前置条件**: 管理员登录；存在可编辑的用户
  - **测试步骤**: 点击 Edit → 修改用户信息 → 保存
  - **预期结果**: 用户信息更新成功；列表显示更新后的信息
  - **优先级**: 高

- **TC006**: 删除用户（如果支持）
  - **标签**: [@p0 @mutate]
  - **前置条件**: 管理员登录；存在可删除的测试用户
  - **测试步骤**: 点击 Delete → 确认删除 → 验证结果
  - **预期结果**: 用户删除成功；列表不再显示该用户
  - **优先级**: 高（建议使用测试专用账号，避免污染生产数据）

- **TC007**: 分页功能
  - **标签**: [@p1]
  - **前置条件**: 管理员登录；用户数量超过一页
  - **测试步骤**: 点击 Next Page → 验证 URL 参数 → 验证数据内容
  - **预期结果**: 分页切换正确；URL 参数同步；数据内容正确更新
  - **优先级**: 中

- **TC-SEC-001**: 未授权拦截
  - **标签**: [@p1 @security @auth]
  - **前置条件**: 未登录/非管理员
  - **预期结果**: 被拦截或重定向；不得暴露用户数据
  - **优先级**: 中

- **TC-SEC-002**: 敏感信息不泄露
  - **标签**: [@p1 @security]
  - **测试步骤**: 检查用户列表显示内容
  - **预期结果**: 不显示密码明文、Token、敏感个人信息
  - **优先级**: 中

### 3.2 边界测试用例
- **TC-BOUNDARY-001**: 空列表状态
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 清空所有用户（或使用空数据库）→ 访问页面
  - **预期结果**: 显示友好的空状态提示；不出现错误

- **TC-BOUNDARY-002**: 超长搜索关键词
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 输入超长搜索关键词（如 1000 字符）
  - **预期结果**: 正确处理；显示长度限制提示或截断

- **TC-BOUNDARY-003**: 特殊字符搜索
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 输入特殊字符搜索（如 `<script>`, `' OR 1=1`）
  - **预期结果**: 正确处理；不执行脚本；不出现 SQL 注入

### 3.3 异常测试用例
- **TC-EXCEPTION-001**: 网络异常处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟网络中断后操作
  - **预期结果**: 显示网络错误提示；允许重试

- **TC-EXCEPTION-002**: 服务器错误处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟 5xx 错误
  - **预期结果**: 显示友好错误提示；不暴露服务器内部信息

- **TC-EXCEPTION-003**: 并发操作处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 同时编辑同一用户
  - **预期结果**: 正确处理并发冲突；显示相应提示

## 4. 测试数据设计（JSON）
```json
{
  "valid": [
    {
      "searchKeyword": "test",
      "userEmail": "testuser@example.com",
      "userName": "Test User"
    }
  ],
  "invalid": [
    {
      "case": "empty_search",
      "searchKeyword": ""
    },
    {
      "case": "non_existent_user",
      "searchKeyword": "nonexistent@example.com"
    },
    {
      "case": "special_chars_search",
      "searchKeyword": "<script>alert('xss')</script>"
    }
  ],
  "boundary": [
    {
      "case": "very_long_search",
      "searchKeyword": "__1000_CHARS_STRING__"
    },
    {
      "case": "sql_injection_search",
      "searchKeyword": "' OR 1=1 --"
    }
  ]
}
```

## 5. 自动化实现建议（对齐本仓库）
### 5.1 页面类实现
- 建议 PageObject：`pages/admin_users_page.py`（类名 `AdminUsersPage`，继承 `core/base_page.py:BasePage`）
- 把"业务动作"封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/admin/users/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码
- 删除操作标记 `@pytest.mark.mutate`，默认回归会排除

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检
- 登录态复用：使用 `REUSE_LOGIN=1` 启用 storage_state 复用，减少登录频率
- 删除操作：建议使用测试专用账号，避免污染生产数据

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）

