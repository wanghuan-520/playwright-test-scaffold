# Admin Users 页面字段需求文档

## 概述

**页面路径**: `/admin/users`  
**权限要求**: `Platform.UserManagement`（仅 admin 角色可访问）  
**功能**: 用户管理（查看、创建、编辑、删除用户）

---

## 1. 页面结构

### 1.1 统计卡片

| 卡片 | 数据来源 | 实时更新 |
|------|----------|----------|
| Total Users | 用户总数 | 是 |
| Active Now | 当前活跃用户（在线） | 是 |
| Roles | 角色数量 | 是 |
| Admins | admin 角色用户数 | ⚠️ Bug: 显示可能不准确 |

### 1.2 搜索和筛选

| 功能 | 类型 | 说明 |
|------|------|------|
| 搜索框 | searchbox | Placeholder: "Search users by name or email..." |
| 角色筛选 | dropdown | 选项: All Roles / member / admin |
| 状态筛选 | dropdown | 选项: All Status / Active / Inactive |

### 1.3 用户表格

| 列名 | 字段 | 说明 |
|------|------|------|
| (checkbox) | - | 批量选择 |
| USER | username + 头像 | 显示用户名和首字母头像 |
| EMAIL | email | 用户邮箱 |
| ROLE | roles[] | 用户角色标签（member/admin） |
| STATUS | isActive | Active/Inactive 状态 |
| ACTIONS | - | 操作菜单 |

### 1.4 翻页

| 功能 | 默认值 | 可选值 |
|------|--------|--------|
| Per page | 10 | 10 / 20 / 50 / 100 |
| 页码 | 1, 2, ..., N | 数字页码按钮 |

---

## 2. Create New User 对话框

### 2.1 字段定义

| 字段 | 必填 | 类型 | Placeholder | maxlength (前端) | 后端限制 |
|------|------|------|-------------|-----------------|----------|
| First Name | 否 | text | John | **64** | 64 (ABP) | 前端 maxLength 截断 |
| Last Name | 否 | text | Doe | **64** | 64 (ABP) | 前端 maxLength 截断 |
| Email | 是 * | email | john@example.com | 无 | 256 (ABP) | |
| Username | 是 * | text | johndoe | 无 | 256 (ABP) | ABP 白名单校验 |
| Password | 是 * | password | Enter password | 无 | 6-128 (ABP Policy) | |
| Phone Number | 否 | tel | +1 (555) 000-0000 | 无 | 16 (ABP) | |
| Assign Roles | 否 | button group | - | - | member / admin / test | |
| Active | 否 | switch | - | - | 默认: true | |

### 2.2 Password 字段特性

- 显示/隐藏密码切换按钮
- 密码策略验证（ABP IdentityOptions）：
  - `RequiredLength`: 6
  - `RequireDigit`: true
  - `RequireUppercase`: true  
  - `RequireLowercase`: true
  - `RequireNonAlphanumeric`: true

### 2.3 Assign Roles 字段

| 选项 | 默认选中 | 说明 |
|------|----------|------|
| member | 否 | 普通成员角色 |
| admin | 否 | 管理员角色 |

可多选。

### 2.4 Active 开关

| 状态 | 值 | 说明 |
|------|-----|------|
| 开启 | true | User can sign in |
| 关闭 | false | 用户无法登录 |

---

## 3. Actions 菜单

| 操作 | 图标 | 说明 |
|------|------|------|
| View Details | 👁 | 查看用户详情 |
| Edit User | ✏️ | 编辑用户信息 |
| Set Password | 🔒 | 重置用户密码 |
| Delete User | 🗑 | 删除用户（危险操作） |

---

## 4. Edit User 对话框

### 4.1 字段定义

| 字段 | 必填 | 类型 | 可编辑 | 前端 maxLength | 后端限制 | 备注 |
|------|------|------|--------|---------------|----------|------|
| Username | - | text | ❌ 只读（disabled） | - | 256 (ABP) | 创建后不可修改，显示 "User name cannot be changed" |
| Email | - | email | ❌ 只读（disabled） | - | 256 (ABP) | 创建后不可修改，显示 "Email cannot be changed" |
| First Name | 否 | text | ✅ 可修改 | **64** | 64 (ABP) | 前端 maxLength 截断，超过 64 字符浏览器自动截断 |
| Last Name | 否 | text | ✅ 可修改 | **64** | 64 (ABP) | 同上 |
| Phone Number | 否 | tel | ✅ 可修改 | 无 | 16 (ABP) | 后端限制但 MongoDB 不强制 |
| Assigned Roles | 否 | button group | ✅ 可修改 | - | member / admin / test | 可多选 |
| Active | 否 | switch | ✅ 可修改 | - | boolean | 控制登录权限 |

⚠️ **重要区别**（与 Create User 对比）：
- **Username 只读** - 显示但 disabled，创建后不可修改
- **Email 只读** - 显示但 disabled，创建后不可修改
- **没有 Password 字段** - 需通过 "Set Password" 单独设置

### 4.2 前端验证

| 字段 | 验证方式 | 说明 |
|------|----------|------|
| Email | `type="email"` | 浏览器原生格式验证 |
| First Name | `maxLength={64}` | 浏览器截断，超过 64 字符自动截断为 64 |
| Last Name | `maxLength={64}` | 同上 |
| 其他字段 | 无 | 无前端强制验证 |

### 4.3 后端验证

| 字段 | 验证规则 | 错误消息 |
|------|----------|----------|
| Email | 唯一性 | "Email '{email}' is already taken." |
| Email | 格式 | "'{email}' is not a valid email address." |
| Name | 长度 ≤ 64 | 前端 maxLength 已截断，后端不会收到超长值 |
| Surname | 长度 ≤ 64 | 同上 |
| PhoneNumber | 长度 ≤ 16 | ⚠️ MongoDB 不强制（前端无 maxLength） |

### 4.4 并发控制

```typescript
// 前端实现
const currentUser = await abpFetch(`/api/identity/users/${id}`)
const updateDto = {
  ...formData,
  concurrencyStamp: currentUser.concurrencyStamp  // 防止并发冲突
}
```

### 4.5 角色分配

- 角色变更通过同一 PUT API 提交（`roleNames` 字段）
- 可选 `member`、`admin` 或同时选择两者

---

## 5. Set Password 对话框

### 5.1 字段定义

| 字段 | 必填 | 类型 | 前端验证 | 后端限制 |
|------|------|------|----------|----------|
| New Password | 是 | password | `required` | ABP 密码策略 |
| Confirm Password | 是 | password | `required` | 必须与 New Password 一致 |

### 5.2 前端验证

| 验证规则 | 实现位置 | 错误消息 |
|----------|----------|----------|
| 必填 | `required` 属性 | 浏览器原生验证 |
| 密码匹配 | JavaScript | "Passwords do not match" |
| 最小长度 | JavaScript | "Password must be at least 6 characters" |

```typescript
// 前端验证逻辑（user-modals.tsx）
if (password !== confirmPassword) {
  showError("Passwords do not match")
  return
}
if (password.length < 6) {
  showError("Password must be at least 6 characters")
  return
}
// ⚠️ 注意：前端不验证完整密码策略（大小写、数字、特殊字符），依赖后端验证
```

### 5.3 后端验证（ABP 密码策略）

**⚠️ 重要：Set Password 的密码策略与注册页面完全相同**

Set Password API 通过 `PUT /api/identity/users/{id}` 设置密码，使用 ABP Identity 的 `UserManager.SetPasswordAsync` 方法，该方法使用与注册相同的 `IdentityOptions` 配置。

| 规则 | 要求 | 错误消息 |
|------|------|----------|
| RequiredLength | ≥ 6 | "Passwords must be at least 6 characters." |
| RequireDigit | 含数字 | "Passwords must have at least one digit ('0'-'9')." |
| RequireUppercase | 含大写 | "Passwords must have at least one uppercase ('A'-'Z')." |
| RequireLowercase | 含小写 | "Passwords must have at least one lowercase ('a'-'z')." |
| RequireNonAlphanumeric | 含特殊字符 | "Passwords must have at least one non alphanumeric character." |
| RequiredUniqueChars | ≥ 1 | 唯一字符数要求 |

**密码策略配置**（与注册页面相同）：
```csharp
options.Password.RequiredLength = 6;
options.Password.RequireDigit = true;
options.Password.RequireUppercase = true;
options.Password.RequireLowercase = true;
options.Password.RequireNonAlphanumeric = true;
options.Password.RequiredUniqueChars = 1;
```

### 5.4 API 实现

```typescript
// 前端实现 - 通过更新用户 API 设置密码
await abpFetch(`/api/identity/users/${id}`, {
  method: 'PUT',
  body: JSON.stringify({
    userName: currentUser.userName,
    email: currentUser.email,
    // ... 其他字段保持不变
    password: newPassword,  // 设置新密码
    concurrencyStamp: currentUser.concurrencyStamp,
  }),
})
```


---

## 6. View Details 对话框

### 6.1 显示字段

| 字段 | 来源 | 显示位置 |
|------|------|----------|
| Avatar | `/api/account/profile-picture/{id}` | 用户卡片 |
| Display Name | name + surname / userName / email | 卡片标题 |
| Email | user.email | 卡片副标题 |
| Status | user.isActive | Active/Inactive 标签 |
| Admin Badge | roles.includes('admin') | Admin 标签（仅管理员） |
| Username | user.userName | Account Information |
| First Name | user.name | Account Information |
| Last Name | user.surname | Account Information |
| Phone Number | user.phoneNumber | Account Information |
| Created At | user.createdAt | Account Information |
| Assigned Roles | user.roles | 角色列表 |

### 6.2 Display Name 逻辑

```typescript
const fullName = [user.name, user.surname].filter(Boolean).join(' ').trim()
const displayName = fullName || user.userName || user.email.split('@')[0]
```

---

## 7. Delete User 对话框

### 7.1 确认信息

| 显示内容 | 来源 |
|----------|------|
| 标题 | "Delete User" |
| 提示 | "Are you sure you want to delete this user?" |
| 用户邮箱 | user.email |
| 警告 | "This action cannot be undone. All user data will be permanently removed." |

### 7.2 后端验证

| 场景 | HTTP Status | 错误消息 |
|------|-------------|----------|
| 删除自己 | 400 | "You cannot delete yourself." |
| 用户不存在 | 404 | "User not found." |

---

## 8. 后端 API

### 8.1 用户列表

```
GET /api/identity/users
Query: 
  - filter: string (搜索关键词)
  - sorting: string (排序字段)
  - skipCount: number (跳过数量)
  - maxResultCount: number (每页数量)
  
Response:
{
  "totalCount": number,
  "items": [
    {
      "id": "guid",
      "userName": "string",
      "email": "string",
      "name": "string",
      "surname": "string",
      "phoneNumber": "string",
      "isActive": boolean,
      "lockoutEnabled": boolean,
      "lockoutEnd": "datetime",
      "roles": ["string"]
    }
  ]
}
```

### 8.2 创建用户

```
POST /api/identity/users
Body:
{
  "userName": "string",       // 必填
  "email": "string",          // 必填
  "password": "string",       // 必填
  "name": "string",           // 可选
  "surname": "string",        // 可选
  "phoneNumber": "string",    // 可选
  "isActive": boolean,        // 可选，默认 true
  "roleNames": ["string"]     // 可选
}

Response: User object
Status: 200 OK / 400 Bad Request / 409 Conflict
```

### 8.3 更新用户

```
PUT /api/identity/users/{id}
Body:
{
  "userName": "string",
  "email": "string",
  "name": "string",
  "surname": "string",
  "phoneNumber": "string",
  "isActive": boolean
}
```

### 8.4 删除用户

```
DELETE /api/identity/users/{id}
Response: 204 No Content
```

### 8.5 分配角色

```
PUT /api/identity/users/{id}/roles
Body:
{
  "roleNames": ["member", "admin"]
}
```

### 8.6 设置密码

```
PUT /api/identity/users/{id}/password
Body:
{
  "newPassword": "string"
}
```

---

## 9. 后端约束（ABP Identity）

### 9.1 字段长度限制

| 字段 | ABP 常量 | 值 | MongoDB 强制 |
|------|----------|-----|--------------|
| Username | `MaxUserNameLength` | 256 | ❌ 不强制 |
| Email | `MaxEmailLength` | 256 | ❌ 不强制 |
| Name | `MaxNameLength` | 64 | ❌ 不强制 |
| Surname | `MaxSurnameLength` | 64 | ❌ 不强制 |
| PhoneNumber | `MaxPhoneNumberLength` | 16 | ❌ 不强制 |
| Password | `RequiredLength` | 6 (min) | ✅ API 验证 |

**注意**: 项目使用 MongoDB（schema-less），EF Core 的 `HasMaxLength` 不会在数据库层面强制执行。长度限制仅在 ABP 验证层生效。

### 9.2 密码策略

```csharp
options.Password.RequiredLength = 6;
options.Password.RequireDigit = true;
options.Password.RequireUppercase = true;
options.Password.RequireLowercase = true;
options.Password.RequireNonAlphanumeric = true;
options.Password.RequiredUniqueChars = 1;
```

### 9.3 用户名规则

```csharp
options.User.AllowedUserNameCharacters = 
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@+";
options.User.RequireUniqueEmail = true;
```

---

## 10. 错误消息

### 10.1 创建用户错误

| 场景 | HTTP Status | 错误消息 |
|------|-------------|----------|
| 用户名已存在 | 409 | "Username '{username}' is already taken." |
| 邮箱已存在 | 409 | "Email '{email}' is already taken." |
| 密码太弱 | 400 | "Passwords must be at least {0} characters." |
| 密码缺少数字 | 400 | "Passwords must have at least one digit ('0'-'9')." |
| 密码缺少大写 | 400 | "Passwords must have at least one uppercase ('A'-'Z')." |
| 密码缺少小写 | 400 | "Passwords must have at least one lowercase ('a'-'z')." |
| 密码缺少特殊字符 | 400 | "Passwords must have at least one non alphanumeric character." |
| 用户名包含非法字符 | 400 | "User name '{username}' is invalid, can only contain letters or digits." |
| 邮箱格式错误 | 400 | "'{email}' is not a valid email address." |

### 10.2 删除用户错误

| 场景 | HTTP Status | 错误消息 |
|------|-------------|----------|
| 删除自己 | 400 | "You cannot delete yourself." |
| 用户不存在 | 404 | "User not found." |

---

## 11. 功能变更记录

| 日期 | 变更 | 说明 |
|------|------|------|
| 2026-02-04 | "Invite User" 按钮已移除 | 原有邀请用户功能已被移除，仅保留 "Add User" 直接创建用户 |

---

## 12. 权限矩阵

| 操作 | member | admin |
|------|--------|-------|
| 访问 /admin/users | ❌ | ✅ |
| 查看用户列表 | ❌ | ✅ |
| 创建用户 | ❌ | ✅ |
| 编辑用户 | ❌ | ✅ |
| 删除用户 | ❌ | ✅ |
| 分配角色 | ❌ | ✅ (ManageRoles) |
| 设置密码 | ❌ | ✅ |

