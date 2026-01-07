# Login 边界值测试账号池配置

## 账号要求

为了避免账号锁定（ABP Identity 默认：连续失败 5次 → 锁定 5分钟），**每个边界值测试需要独立账号**。

### 必需账号（共 6个）

| 用途 | 参数要求 | 数量 | 说明 |
|-----|---------|------|------|
| **Password 边界值** | password长度=31 | 1 | 如：`P123456789012345678901234567!` |
| **Password 边界值** | password长度=32 | 1 | 如：`P1234567890123456789012345678!` |
| **Password 边界值** | password长度=33 | 1 | 如：`P12345678901234567890123456789!` |
| **Username 边界值** | username长度=255 | 1 | 255个字符的用户名 |
| **Username 边界值** | username长度=256 | 1 | 256个字符的用户名 |
| **必填验证** | 普通账号 | 2 | 用于 required_fields_validation 测试（2个参数化case） |

**总计：6个独立账号**

---

## 配置示例

将以下账号添加到 `test-data/test_account_pool.json`：

```json
{
  "test_account_pool": [
    {
      "username": "login_pass31_user",
      "email": "login_pass31@example.com",
      "password": "P123456789012345678901234567!",
      "initial_password": "P123456789012345678901234567!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_boundary", "password_31"],
      "purpose": "test_p1_login_password_length_boundaries[chromium-31]"
    },
    {
      "username": "login_pass32_user",
      "email": "login_pass32@example.com",
      "password": "P1234567890123456789012345678!",
      "initial_password": "P1234567890123456789012345678!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_boundary", "password_32"],
      "purpose": "test_p1_login_password_length_boundaries[chromium-32]"
    },
    {
      "username": "login_pass33_user",
      "email": "login_pass33@example.com",
      "password": "P12345678901234567890123456789!",
      "initial_password": "P12345678901234567890123456789!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_boundary", "password_33"],
      "purpose": "test_p1_login_password_length_boundaries[chromium-33]",
      "note": "⚠️ 此账号 password=33 超过 ABP 约束(32)，需要直接操作数据库或后端 API 创建"
    },
    {
      "username": "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",
      "email": "login_user255@example.com",
      "password": "ValidPass123!",
      "initial_password": "ValidPass123!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_boundary", "username_255"],
      "purpose": "test_p1_login_username_length_boundaries[chromium-255]"
    },
    {
      "username": "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",
      "email": "login_user256@example.com",
      "password": "ValidPass123!",
      "initial_password": "ValidPass123!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_boundary", "username_256"],
      "purpose": "test_p1_login_username_length_boundaries[chromium-256]"
    },
    {
      "username": "login_required_test_user1",
      "email": "login_required1@example.com",
      "password": "ValidPass123!",
      "initial_password": "ValidPass123!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_required"],
      "purpose": "test_p1_login_required_fields_validation[chromium-username_or_email-#LoginInput_UserNameOrEmailAddress]"
    },
    {
      "username": "login_required_test_user2",
      "email": "login_required2@example.com",
      "password": "ValidPass123!",
      "initial_password": "ValidPass123!",
      "in_use": false,
      "is_locked": false,
      "roles": ["default"],
      "tags": ["login_required"],
      "purpose": "test_p1_login_required_fields_validation[chromium-password-#LoginInput_Password]"
    }
  ]
}
```

---

## 账号创建步骤

### 1. 普通账号（password ≤ 32）

通过注册页面或 API 正常创建：
- `login_pass31_user` (password=31)
- `login_pass32_user` (password=32)
- `login_user255` (username=255)
- `login_user256` (username=256)
- `login_required_test_user1/2`

### 2. 特殊账号（password = 33）⚠️

**问题**：ABP 后端约束 password最大=32，无法通过注册接口创建 password=33 的账号。

**解决方案（三选一）：**

#### 方案A：放弃 password=33 的真实登录测试（推荐）
- 仅测试前端行为（不截断）+ 后端拒绝行为
- 不需要 `login_pass33_user` 账号

#### 方案B：直接操作数据库
```javascript
// MongoDB 示例
db.Users.insertOne({
  userName: "login_pass33_user",
  email: "login_pass33@example.com",
  passwordHash: "<hash of P12345678901234567890123456789!>",
  // ... 其他必需字段
})
```

#### 方案C：临时放宽后端约束
修改后端 `IdentityOptions` → 重启 → 注册账号 → 改回约束 → 重启

---

## 自动分配机制

测试框架的 `test_account` fixture 会根据**测试用例名称**自动分配账号：

```python
# test_Login_p1_abp_constraints.py::test_p1_login_password_length_boundaries[chromium-31]
# ↓
# 自动分配 purpose="test_p1_login_password_length_boundaries[chromium-31]" 的账号
# ↓
# login_pass31_user
```

**优点：**
- ✅ 每个测试用独立账号
- ✅ 避免累计失败触发锁定
- ✅ 并行执行安全
- ✅ 测试前后自动清理

---

## 验证

运行测试前，使用 `account_precheck` 工具验证账号可用性：

```bash
cd /Users/wanghuan/aelf/Cursor/playwright-test-scaffold
python3 -m utils.account_precheck
```

预期输出：
```
✅ login_pass31_user: ok
✅ login_pass32_user: ok
✅ login_user255: ok
✅ login_user256: ok
⚠️  login_pass33_user: 不存在或无效（可选账号）
```

---

## 注意事项

1. **锁定阈值**：ABP Identity 默认连续失败 5次 → 锁定 5分钟
2. **账号隔离**：每个测试用独立账号，确保失败计数不累积
3. **password=33**：如果无法创建，测试会自动降级为"仅验证前端+后端行为"
4. **并行执行**：账号池大小应 ≥ 并行 worker 数量 × 测试用例数

