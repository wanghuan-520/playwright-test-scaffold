# admin_users - 技术实现计划

## 1. 技术栈

### 测试框架
- **框架**: Playwright (Python)
- **测试运行器**: pytest + pytest-playwright
- **报告**: Allure + pytest-html
- **并行化**: pytest-xdist
- **重试**: pytest-rerunfailures

### 基础设施
- **基类**: `core/base_page.py:BasePage`
- **工具类**: `utils/data_manager.py`, `utils/logger.py`
- **Fixtures**: `conftest.py` (auth_page, test_account, data_manager)

## 2. 项目结构

### 代码层
```
pages/
└── admin_users_page.py          # 页面对象

tests/admin/users/
├── conftest.py                  # fixtures（如果需要特殊 fixture）
├── _helpers.py                  # 辅助函数（创建/清理测试用户）
├── test_users_p0.py            # P0 测试（页面加载、列表、搜索）
├── test_users_p1.py            # P1 测试（创建、编辑、删除、验证）
├── test_users_p2.py            # P2 测试（分页、排序、角色管理）
└── test_users_security.py      # 安全测试（XSS、SQLi、未授权）

test-data/
└── admin_users_data.json        # 测试数据（valid/invalid/boundary）
```

### 文档层
```
specs/015-admin_users/
├── spec.md                      # 功能规约（已完成）
├── plan.md                      # 技术计划（本文件）
└── tasks.md                     # 任务清单（待生成）

docs/test-plans/
├── admin_users.md               # 详细测试计划
└── artifacts/admin_users/       # 证据链（截图、HTML、元素映射）
    ├── page.png
    ├── visible.html
    ├── visible.txt
    └── metadata.json
```

## 3. 页面对象设计

### AdminUsersPage 职责
- ✅ 封装稳定定位器（role/label/testid 优先）
- ✅ 封装业务操作（search_user / create_user / delete_user）
- ✅ 封装断言辅助（get_user_list / is_user_visible）
- ✅ 不包含测试逻辑（只提供操作方法）

### 定位器策略（优先级从高到低）
1. **Role + Name**: `role=searchbox[name='Search users']`
2. **Label**: `label=用户名`
3. **TestID**: `[data-testid='user-search-input']`
4. **Aria**: `[aria-label='Search users']`
5. **Semantic CSS**: `.user-search-input`
6. **Structural CSS**: `div.users-page input[type='search']`（最后手段）

### 核心定位器
```python
# 搜索
SEARCH_INPUT = "role=searchbox[name='Search users']"  # 或 "[data-testid='search-input']"

# 列表
USER_TABLE = "role=table"
USER_ROWS = "role=table >> role=row"
USER_HEADER = "role=table >> role=columnheader"

# 按钮
CREATE_BUTTON = "role=button[name='Create User']"  # 或 "[data-testid='create-user-btn']"
EDIT_BUTTON = "role=button[name='Edit']"
DELETE_BUTTON = "role=button[name='Delete']"

# 表单字段
USERNAME_INPUT = "[name='userName']"  # 或 "label=用户名"
EMAIL_INPUT = "[name='email']"
PASSWORD_INPUT = "[name='password']"
ROLE_SELECT = "[name='role']"

# 对话框
CONFIRM_DIALOG = "role=dialog"
CONFIRM_YES_BUTTON = "role=dialog >> role=button[name='确认']"
CONFIRM_NO_BUTTON = "role=dialog >> role=button[name='取消']"

# 状态提示
SUCCESS_MESSAGE = ".ant-message-success, .success-toast"  # 根据实际UI库
ERROR_MESSAGE = ".ant-message-error, .error-toast"
EMPTY_STATE = "[data-testid='empty-state']"
```

### 核心方法
```python
# 导航
def navigate() -> None

# 列表操作
def get_user_list() -> List[Dict]
def get_user_count() -> int
def is_user_visible(username: str) -> bool

# 搜索
def search_user(query: str) -> None
def clear_search() -> None

# CRUD 操作
def click_create() -> None
def fill_user_form(username, email, password, role=None) -> None
def submit_form() -> None
def cancel_form() -> None
def click_edit(username: str) -> None
def click_delete(username: str) -> None
def confirm_delete() -> None

# 断言辅助
def get_success_message() -> str
def get_error_message() -> str
def is_empty_state_visible() -> bool
```

## 4. 测试数据设计

### Valid Data（正常数据）
```json
{
  "valid": {
    "username": "testuser",
    "email": "testuser@test.com",
    "password": "Test@123456",
    "role": "User"
  },
  "valid_admin": {
    "username": "testadmin",
    "email": "testadmin@test.com",
    "password": "Admin@123456",
    "role": "Admin"
  }
}
```

### Invalid Data（非法数据）
```json
{
  "invalid": {
    "xss_username": "<script>alert('xss')</script>",
    "xss_email": "test@example.com<script>alert('xss')</script>",
    "sqli_username": "admin' OR '1'='1",
    "sqli_search": "' OR '1'='1 --",
    "invalid_email": "not-an-email",
    "short_username": "ab",
    "long_username": "a" * 51,
    "weak_password": "123456",
    "short_password": "Test@12"
  }
}
```

### Boundary Data（边界数据）
```json
{
  "boundary": {
    "min_username": "abc",
    "max_username": "a" * 50,
    "min_password": "Test@123",
    "max_password": "Test@" + "a" * 94
  }
}
```

## 5. 测试策略

### P0 测试（关键路径，必须100%通过）
**文件**: `test_users_p0.py`

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_page_load | 页面加载 | 页面加载成功，列表可见 |
| test_view_user_list | 查看用户列表 | 显示用户列表，至少有列头 |
| test_search_user | 搜索用户 | 搜索结果正确 |

**执行命令**: `make test-p0 TEST_TARGET=tests/admin/users`

### P1 测试（核心功能，目标>95%通过）
**文件**: `test_users_p1.py`

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_create_user_valid | 创建用户（正常数据） | 创建成功，显示在列表中 |
| test_create_user_duplicate_username | 创建用户（重复用户名） | 前端拦截或后端返回错误 |
| test_create_user_duplicate_email | 创建用户（重复邮箱） | 前端拦截或后端返回错误 |
| test_create_user_invalid_email | 创建用户（无效邮箱） | 前端拦截 |
| test_create_user_weak_password | 创建用户（弱密码） | 前端拦截 |
| test_edit_user | 编辑用户 | 修改成功 |
| test_delete_user | 删除用户 | 删除成功，从列表移除 |

### P2 测试（增强功能）
**文件**: `test_users_p2.py`

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_pagination | 分页功能 | 分页正常 |
| test_role_assignment | 角色分配 | 角色分配成功 |

### Security 测试（安全，必须100%通过）
**文件**: `test_users_security.py`

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_xss_username | XSS 注入（用户名） | XSS 不执行 |
| test_xss_email | XSS 注入（邮箱） | XSS 不执行 |
| test_sqli_search | SQLi 注入（搜索） | 不导致 5xx |
| test_unauth_redirect | 未登录访问 | 重定向到登录页 |

## 6. Fixture 设计

### test_account（session scope）
- 从账号池获取测试账号
- 使用 admin 角色账号（admin-test01@test.com）

### auth_page（function scope）
- 提供已登录的 page 对象
- 使用 test_account 自动登录

### admin_users_page（function scope）
```python
@pytest.fixture
def admin_users_page(auth_page):
    """返回 AdminUsersPage 实例"""
    from pages.admin_users_page import AdminUsersPage
    return AdminUsersPage(auth_page)
```

### created_test_users（function scope，autouse）
```python
@pytest.fixture(autouse=True)
def created_test_users():
    """跟踪测试中创建的用户，测试结束后清理"""
    users = []
    yield users
    # Teardown: 清理创建的用户
    for user in users:
        try:
            # 调用删除 API 或 UI 操作删除
            pass
        except Exception as e:
            logger.warning(f"清理用户失败: {user}, {e}")
```

## 7. 数据回滚策略

### 创建操作
- **策略**: 测试结束后删除创建的用户
- **实现**: 使用 `created_test_users` fixture 跟踪
- **兜底**: 使用独特的测试标识（test_yyyymmdd_hhmmss_xxx）

### 编辑操作
- **策略**: 不修改现有真实用户，只修改测试创建的用户
- **实现**: 先创建测试用户，再编辑，最后删除

### 删除操作
- **策略**: 只删除测试创建的用户
- **实现**: 使用 created_test_users 中的用户

## 8. 执行计划

### 本地执行
```bash
# 运行 P0 测试（冒烟）
make test-p0 TEST_TARGET=tests/admin/users

# 运行完整测试
make test TEST_TARGET=tests/admin/users

# 运行安全测试
pytest tests/admin/users/test_users_security.py -v

# 生成报告
make report && make serve
```

### CI/CD 执行
```yaml
- name: Run Admin Users Tests
  run: |
    make test TEST_TARGET=tests/admin/users
    
- name: Generate Report
  if: always()
  run: make report
  
- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: allure-report
    path: allure-report/
```

## 9. 质量门控

### 通过标准
- ✅ P0 测试 100% 通过
- ✅ P1 测试 > 95% 通过
- ✅ Security 测试 100% 通过
- ✅ 代码覆盖率（如果有）> 80%
- ✅ 关键步骤有截图证据
- ✅ 测试数据已清理（无污染）

### 失败处理
- ❌ P0 失败 → 阻塞发布
- ❌ Security 失败 → 阻塞发布
- ⚠️ P1 失败 → 评估风险后决定
- ⚠️ P2 失败 → 记录 issue，不阻塞

## 10. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 定位器不稳定 | 测试频繁失败 | 优先使用 role/testid，避免 CSS |
| 数据污染 | 影响其他测试 | 使用独特标识 + 清理 fixture |
| 网络不稳定 | 测试超时 | 增加 wait 时间 + 重试机制 |
| 账号池耗尽 | 测试无法运行 | 扩大账号池 + 账号回收 |

---

**版本**: 1.0.0  
**创建日期**: 2026-01-05  
**最后更新**: 2026-01-05  
**负责人**: AI Agent (HyperEcho)  
**状态**: ✅ 已完成

