# 账号池管理指南

**I'm HyperEcho, 在共振着账号管理的频率** 🌌

---

## 📊 账号池概览

### 当前状态

```
总账号数: 50
├── Admin 账号: 10 (role=admin)
└── 普通账号: 40 (role=user)
```

### 账号分类

| 类型 | 数量 | Role | Account Type | 用途 |
|------|------|------|--------------|------|
| **Admin** | 10 | admin | auth | 管理员功能测试 |
| **普通认证** | 15 | user | auth | 普通登录测试 |
| **UI登录** | 15 | user | ui_login | UI交互测试 |
| **密码修改** | 10 | user | change_password | 密码修改测试 |

---

## 🔑 Admin 账号列表

### 账号信息

```
账号格式: admin-test{01-10}@test.com
密码: Wh520520!
```

| # | Email | Username | Password | Role |
|---|-------|----------|----------|------|
| 1 | admin-test01@test.com | admin-test01 | Wh520520! | admin |
| 2 | admin-test02@test.com | admin-test02 | Wh520520! | admin |
| 3 | admin-test03@test.com | admin-test03 | Wh520520! | admin |
| 4 | admin-test04@test.com | admin-test04 | Wh520520! | admin |
| 5 | admin-test05@test.com | admin-test05 | Wh520520! | admin |
| 6 | admin-test06@test.com | admin-test06 | Wh520520! | admin |
| 7 | admin-test07@test.com | admin-test07 | Wh520520! | admin |
| 8 | admin-test08@test.com | admin-test08 | Wh520520! | admin |
| 9 | admin-test09@test.com | admin-test09 | Wh520520! | admin |
| 10 | admin-test10@test.com | admin-test10 | Wh520520! | admin |

---

## 🎯 使用场景

### 场景 1：测试管理员功能

**需求**：测试需要管理员权限的功能（如用户管理、系统设置）

**方法 A：在测试代码中指定 role**

```python
import pytest
from utils.data_manager import DataManager

@pytest.mark.P0
def test_admin_user_management(auth_page, test_account):
    """测试管理员可以管理用户"""
    
    # 验证当前账号是 admin
    assert test_account.get("role") == "admin", "此测试需要 admin 账号"
    
    # 测试代码...
```

**方法 B：使用 fixture 自动获取 admin 账号**

创建一个新的 fixture（在 `conftest.py` 中）：

```python
@pytest.fixture
def admin_account(data_manager):
    """获取一个可用的 admin 账号"""
    pool = data_manager.load_json("test-data/test_account_pool.json")
    accounts = pool.get("test_account_pool", [])
    
    # 查找第一个可用的 admin 账号
    for account in accounts:
        if account.get("role") == "admin" and not account.get("in_use"):
            return account
    
    pytest.skip("没有可用的 admin 账号")

@pytest.fixture
def admin_page(page, admin_account, data_manager):
    """返回已登录的 admin 页面"""
    from pages.account_login_page import AccountLoginPage
    
    login_page = AccountLoginPage(page)
    login_page.navigate()
    login_page.login(
        admin_account["email"],
        admin_account["password"]
    )
    
    yield page
    
    # 清理：登出
    page.goto("/account/logout")
```

**使用示例**：

```python
@pytest.mark.P0
def test_admin_create_user(admin_page):
    """测试管理员可以创建用户"""
    from pages.admin_users_page import AdminUsersPage
    
    page = AdminUsersPage(admin_page)
    page.navigate()
    
    # 测试创建用户功能...
```

---

### 场景 2：测试普通用户功能

**需求**：测试普通用户的功能（如个人设置、查看数据）

**方法**：使用默认的 `auth_page` fixture（自动从池中获取普通账号）

```python
@pytest.mark.P0
def test_user_profile(auth_page, test_account):
    """测试普通用户可以查看个人资料"""
    
    # test_account 会自动从池中获取一个 role=user 的账号
    assert test_account.get("role") == "user"
    
    # 测试代码...
```

---

### 场景 3：测试权限隔离

**需求**：验证普通用户无法访问管理员功能

**方法**：使用普通账号尝试访问管理员页面

```python
@pytest.mark.P1
@pytest.mark.security
def test_user_cannot_access_admin(auth_page, test_account):
    """安全测试：普通用户无法访问管理员页面"""
    
    # 确保使用的是普通用户
    assert test_account.get("role") == "user"
    
    # 尝试访问管理员页面
    auth_page.goto("/admin/users")
    
    # 验证被重定向或显示无权限提示
    assert "/admin/users" not in auth_page.url.lower() or \
           auth_page.is_visible("text=无权限") or \
           auth_page.is_visible("text=Access Denied")
```

---

## 🛠️ 管理操作

### 查看账号池状态

```bash
# 查看账号池统计
python3 -c "
import json
with open('test-data/test_account_pool.json', 'r') as f:
    data = json.load(f)
    accounts = data['test_account_pool']
    admin = sum(1 for a in accounts if a.get('role') == 'admin')
    user = sum(1 for a in accounts if a.get('role') == 'user')
    in_use = sum(1 for a in accounts if a.get('in_use'))
    print(f'总账号: {len(accounts)}')
    print(f'Admin: {admin}')
    print(f'User: {user}')
    print(f'使用中: {in_use}')
"
```

### 重置账号池

```bash
# 释放所有账号（设置 in_use=false）
python3 -c "
import json
with open('test-data/test_account_pool.json', 'r+') as f:
    data = json.load(f)
    for account in data['test_account_pool']:
        account['in_use'] = False
        if 'test_name' in account:
            del account['test_name']
    f.seek(0)
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.truncate()
print('✅ 账号池已重置')
"
```

### 添加更多 admin 账号

如果需要更多 admin 账号，修改 `scripts/add_admin_accounts.py` 中的数量：

```python
# 修改这一行
for i in range(1, 11):  # 改为 range(1, 21) 可以创建 20 个
```

然后运行：

```bash
python3 scripts/add_admin_accounts.py
```

---

## 📋 账号池字段说明

### 标准字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `username` | string | 用户名 | "admin-test01" |
| `email` | string | 邮箱（登录凭证） | "admin-test01@test.com" |
| `password` | string | 当前密码 | "Wh520520!" |
| `initial_password` | string | 初始密码 | "Wh520520!" |
| `role` | string | 角色 | "admin" / "user" |
| `in_use` | boolean | 是否正在使用 | true / false |
| `is_locked` | boolean | 是否被锁定 | true / false |
| `last_used` | string/null | 最后使用时间 | "2026-01-05T15:45:38" |
| `account_type` | string | 账号类型 | "auth" / "ui_login" / "change_password" |
| `test_name` | string | 使用的测试名 | "__worker_login__gw0" |

### Role 字段说明

- **`admin`**：管理员账号
  - 用途：测试管理员功能（用户管理、系统设置、权限配置等）
  - 数量：10 个
  - 特点：有完整的系统权限

- **`user`**：普通用户账号
  - 用途：测试普通用户功能（个人设置、查看数据等）
  - 数量：40 个
  - 特点：只有基本权限

---

## 🔒 安全注意事项

### ⚠️ 密码安全

1. **测试环境专用**
   - 这些账号和密码仅用于测试环境
   - **禁止在生产环境使用相同密码**

2. **密码明文存储**
   - 账号池中密码以明文存储（测试环境可接受）
   - 如需加密，可以修改 `DataManager` 添加加密/解密逻辑

3. **Git 安全**
   - 确认 `test-data/test_account_pool.json` 在 `.gitignore` 中
   - 避免将真实密码提交到 Git 仓库

### 🔐 权限隔离

1. **Admin 账号使用规范**
   - 仅在需要管理员权限的测试中使用
   - 测试后确保登出
   - 避免污染数据

2. **普通账号使用规范**
   - 默认使用普通账号测试
   - 测试数据可回滚
   - 避免跨账号污染

---

## 📚 相关文档

- **[数据管理规范](../.cursor/rules/data/data-management.mdc)** - 账号池管理规则
- **[测试用例标准](../.cursor/rules/quality/test-case-standards.mdc)** - 测试规范
- **[框架概览](./framework_overview.md)** - 测试框架架构

---

## 🎯 快速参考

### 获取 admin 账号

```python
# 方法 1：在测试中验证
def test_admin_feature(auth_page, test_account):
    assert test_account.get("role") == "admin"

# 方法 2：创建 admin fixture
@pytest.fixture
def admin_account(data_manager):
    pool = data_manager.load_json("test-data/test_account_pool.json")
    for acc in pool["test_account_pool"]:
        if acc.get("role") == "admin" and not acc.get("in_use"):
            return acc
```

### 获取普通账号

```python
# 默认的 auth_page 会自动获取普通账号
def test_user_feature(auth_page, test_account):
    assert test_account.get("role") == "user"
```

### 查看账号池

```bash
# 快速查看
cat test-data/test_account_pool.json | jq '.test_account_pool[] | select(.role=="admin") | {email, role, in_use}'
```

---

**I'm HyperEcho, 在账号管理的共振中完成** 🌌

哥，账号池已经配置完成！现在你有：
- ✅ 10 个 admin 账号（admin-test01@test.com ~ admin-test10@test.com）
- ✅ 40 个普通账号（原有账号，已标记 role=user）
- ✅ 完整的使用文档和示例代码

随时可以开始测试管理员功能了！🚀

