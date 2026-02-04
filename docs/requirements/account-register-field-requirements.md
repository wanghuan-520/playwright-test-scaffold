# 注册页面字段限制说明

> 本文档说明注册页面各字段在后端 ABP Framework 中的限制。

---

## 字段映射关系

注册页面的字段与后端 ABP Identity 的映射关系：

| 前端字段 | 后端字段 | 说明 |
|---------|---------|------|
| Full Name | `name` + `surname` | 前端拆分为 firstName 和 lastName |
| Email | `email` | 同时用于生成 `userName`（取 @ 前面的部分） |
| Password | `password` | 直接传递 |

---

## 1. Full Name（全名）

### 前端处理
- **输入**：用户输入完整姓名（如 "John Doe"）
- **处理**：自动拆分为 `firstName` 和 `lastName`
  ```typescript
  const nameParts = formData.name.trim().split(/\s+/)
  const firstName = nameParts[0] || ""      // 第一部分作为 firstName
  const lastName = nameParts.slice(1).join(" ") || ""  // 剩余部分作为 lastName
  ```

### 后端 ABP Identity 限制
- **`name` (firstName)**：
  - 类型：`string?`（可选）
  - 最大长度：**64 字符**（ABP Identity 默认）
  - 验证：无特殊格式要求

- **`surname` (lastName)**：
  - 类型：`string?`（可选）
  - 最大长度：**64 字符**（ABP Identity 默认）
  - 验证：无特殊格式要求

### 注意事项
- 如果用户只输入一个词（如 "John"），`lastName` 将为空字符串
- 如果用户输入多个词（如 "John Michael Doe"），`firstName = "John"`，`lastName = "Michael Doe"`

---

## 2. Email（邮箱）

### 前端处理
- **输入**：用户输入邮箱地址
- **处理**：
  - 直接作为 `email` 传递
  - 同时用于生成 `userName`：`formData.email.split("@")[0]`
    - 例如：`user@example.com` → `userName = "user"`

### 后端 ABP Identity 限制
- **`email`**：
  - 类型：`string`（必需）
  - 最大长度：**256 字符**（ABP Identity 默认）
  - 验证：
    - 必须是有效的邮箱格式（ABP 使用 `EmailAddressAttribute`）
    - 必须唯一（不能与已存在的用户邮箱重复）
    - 不能为空

- **`userName`**（从邮箱生成）：
  - 类型：`string`（必需）
  - 最大长度：**256 字符**（ABP Identity 默认）
  - 验证：
    - 必须唯一（不能与已存在的用户名重复）
    - 不能为空
    - 允许的字符：字母、数字、下划线、连字符等（ABP Identity 默认规则）

### 注意事项
- 如果邮箱的 @ 前面部分超过 256 字符，生成的 `userName` 可能会被截断
- 如果生成的 `userName` 已存在，注册会失败（需要后端处理冲突）

---

## 3. Password（密码）

### 前端验证
前端使用正则表达式进行预验证：
```typescript
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{6,}$/
```

**要求**：
- ✅ 至少 **6 个字符**
- ✅ 必须包含**小写字母** (a-z)
- ✅ 必须包含**大写字母** (A-Z)
- ✅ 必须包含**数字** (0-9)
- ✅ 必须包含**特殊字符** (`!@#$%^&*()_+-=[]{};':"\\|,.<>/?`)

### 后端 ABP Identity 限制
ABP Identity 使用 ASP.NET Core Identity 的默认密码策略：

- **最小长度**：**6 字符**（默认，可配置）
- **要求大写字母**：**是**（默认，可配置 `RequireUppercase = true`）
- **要求小写字母**：**是**（默认，可配置 `RequireLowercase = true`）
- **要求数字**：**是**（默认，可配置 `RequireDigit = true`）
- **要求特殊字符**：**是**（默认，可配置 `RequireNonAlphanumeric = true`）
- **最大长度**：**无限制**（但建议不超过 128 字符）

### 配置位置
密码策略可以在 `VibeResearchingHttpApiHostModule.cs` 中通过 `IdentityOptions` 配置：

```csharp
services.Configure<IdentityOptions>(options =>
{
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;
    options.Password.RequiredLength = 6;
    options.Password.RequiredUniqueChars = 1;
});
```

**当前状态**：使用 ABP Identity 默认配置，与前端验证规则一致。

---

## 总结表格

| 字段 | 前端限制 | 后端限制 | 说明 |
|------|---------|---------|------|
| **Full Name** | 无 | `name`: 64 字符<br>`surname`: 64 字符 | 可选字段，自动拆分 |
| **Email** | 邮箱格式 | 256 字符<br>唯一性<br>邮箱格式 | 同时用于生成 userName |
| **Password** | 6+ 字符<br>大小写+数字+特殊字符 | 6+ 字符<br>大小写+数字+特殊字符 | 前后端验证规则一致 |

---

## 常见错误场景

### 1. Email 已存在
- **错误信息**：`"An account with this email or username already exists."`
- **原因**：邮箱或生成的用户名已被使用

### 2. 密码不符合要求
- **错误信息**：`"Password must be at least 6 characters with uppercase, lowercase, number & special character"`
- **原因**：密码不满足复杂度要求

### 3. 邮箱格式无效
- **错误信息**：由后端 ABP 返回的邮箱验证错误
- **原因**：邮箱格式不符合标准

---

## 参考文档

- [ABP Framework - Identity Module](https://docs.abp.io/en/abp/latest/Modules/Identity)
- [ASP.NET Core Identity - Password Options](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/identity-configuration)

---

*文档版本: 1.0*  
*创建日期: 2026-01-30*  
*最后更新: 2026-01-30*

