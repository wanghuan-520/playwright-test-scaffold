# Account/Login 测试架构

目标：让 Login 的"认证验证/安全测试/证据采集"在 Allure 中清晰呈现，同时保持每个文件短小（<400 行）。

## 目录结构

```
tests/account/login/
├── docs/
│   └── architecture.md           # 本文件
├── _helpers.py                   # 辅助函数（断言、工具、ABP 常量）
├── _known_bugs.py                # 已知 Bug 注册表
├── test_login_p0.py              # P0 关键路径（页面加载、登录成功）
├── test_login_p1.py              # P1 核心验证（必填、无效凭证、导航、Remember Me）
├── test_login_p1_boundary.py     # P1 边界测试（用户名 256, 密码 128）
├── test_login_p2.py              # P2 UI 可见性（Tab 导航、链接可见）
├── test_login_security.py        # 安全测试（注入、锁定）
└── __init__.py
```

## 文件职责

| 文件 | 职责 | 用例数 |
|------|------|--------|
| `test_login_p0.py` | 页面加载、登录成功流程 | 2 |
| `test_login_p1.py` | 必填验证、无效凭证、链接导航、Remember Me | 10 |
| `test_login_p1_boundary.py` | 用户名/密码长度边界测试 | 6 |
| `test_login_p2.py` | Tab 导航、链接可见性 | 4 |
| `test_login_security.py` | XSS/SQLi 注入、账号锁定 | 7 |
| **总计** | | **29** |

## ABP 后端约束

参考文档：`docs/requirements/account-login-field-requirements.md`

| 字段 | 后端限制 | 前端限制 |
|------|----------|----------|
| Username or Email | 必填，最大 256 字符 | 必填，无 maxLength |
| Password | 必填，6-128 字符 | 必填，无 maxLength |
| Remember Me | 可选，默认 false | 可选 |

### 账号锁定机制

| 参数 | 值 | 说明 |
|------|------|------|
| 最大失败次数 | 5 次 | `MaxFailedAccessAttempts` |
| 锁定时长 | 5 分钟 | `DefaultLockoutTimeSpan` |
| 启用锁定 | ✅ | `lockoutOnFailure: true` |

## _helpers.py 核心函数

| 函数 | 用途 |
|------|------|
| `get_first_available_account()` | 获取账号池第一个可用账号 |
| `unique_suffix(xdist_worker_id)` | 生成唯一后缀（测试隔离） |
| `assert_not_redirected_to_login()` | 断言未跳转到登录页 |
| `assert_any_validation_evidence()` | 断言存在任意验证证据 |
| `detect_fatal_error_page()` | 检测致命错误页面 |
| `has_any_error_ui()` | 检测是否有错误 UI |
| `wait_mutation_response()` | 等待写操作响应 |
| `ensure_login_page()` | 确保在登录页面 |

## 设计原则

### 1. 单一职责
- 每个文件聚焦一类测试场景
- 辅助函数统一放在 `_helpers.py`

### 2. 代码复用
- 所有账号获取使用 `get_first_available_account()`
- 所有唯一标识使用 `unique_suffix()`
- 禁止在测试文件中重复定义辅助函数

### 3. Fixture 统一
- 登录页是匿名页，统一使用 `unauth_page`
- 需要登录状态的用 `auth_page`

### 4. Import 规范
- 所有 import 放在文件顶部
- 禁止在函数内部 import

## Login vs Register 差异

| 特性 | Register | Login |
|------|----------|-------|
| 字段边界测试 | 6 点法（完整） | 最大值边界（不崩溃验证） |
| 唯一性测试 | ✅ 用户名/邮箱 | ❌ 不适用 |
| 锁定机制 | ❌ 无 | ✅ 多次失败锁定 |
| Remember Me | ❌ 无 | ✅ Cookie 持久化 |
| 密码复杂度验证 | ✅ 注册时验证 | ❌ 登录不验证 |

---

*最后更新: 2026-02-02*
