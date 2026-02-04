# 登录页面字段限制说明

> 本文档说明登录页面各字段在后端 ABP Framework 中的限制。
> 基于后端代码 `AuthEndpoints.cs` 和 ABP Framework 默认配置分析。

---

## 字段映射关系

登录页面的字段与后端 API 的映射关系：

| 前端字段 | 后端字段 | 说明 |
|---------|---------|------|
| Username or Email | `UserNameOrEmail` | 支持用户名或邮箱登录 |
| Password | `Password` | 密码 |
| Remember Me | `RememberMe` | 是否记住登录状态（持久 cookie） |

---

## 1. Username or Email（用户名或邮箱）

### 前端处理
- **输入**：用户输入用户名或邮箱地址
- **验证**：`required` 属性要求必填
- **无 maxLength 限制**：前端未设置最大长度

### 后端限制（ABP Identity 默认）

| 属性 | 值 | 说明 |
|------|------|------|
| **必填** | ✅ 是 | 不能为空或空白 |
| **最大长度（用户名）** | 256 字符 | `MaxUserNameLength` |
| **最大长度（邮箱）** | 256 字符 | `MaxEmailLength` |
| **格式验证** | 邮箱需符合格式 | `EmailAddressAttribute`（仅当输入为邮箱时） |

### 后端代码验证

```csharp
// AuthEndpoints.cs
if (string.IsNullOrWhiteSpace(request.UserNameOrEmail) ||
    string.IsNullOrWhiteSpace(request.Password))
{
    return Results.BadRequest(new { error = "Username and password are required." });
}

// 支持用户名或邮箱登录
var user = await userManager.FindByEmailAsync(request.UserNameOrEmail)
           ?? await userManager.FindByNameAsync(request.UserNameOrEmail);
```

### 注意事项
- 前端未设置 `maxLength`，但后端最大 256 字符
- 输入可以是用户名也可以是邮箱，后端会依次尝试匹配

---

## 2. Password（密码）

### 前端处理
- **输入**：用户输入密码
- **验证**：`required` 属性要求必填
- **无 maxLength 限制**：前端未设置最大长度

### 后端限制（ABP Identity 默认）

| 属性 | 值 | 说明 |
|------|------|------|
| **必填** | ✅ 是 | 不能为空或空白 |
| **最小长度** | 6 字符 | `RequiredLength` |
| **最大长度** | 128 字符 | `MaxPasswordLength` |
| **需要数字** | ✅ 是 | `RequireDigit: true` |
| **需要小写字母** | ✅ 是 | `RequireLowercase: true` |
| **需要大写字母** | ✅ 是 | `RequireUppercase: true` |
| **需要特殊字符** | ✅ 是 | `RequireNonAlphanumeric: true` |
| **最少唯一字符** | 1 | `RequiredUniqueChars` |

### 注意事项
- 登录时不校验密码复杂度（仅注册时校验）
- 前端未设置 `maxLength`，但后端最大 128 字符

---

## 3. Remember Me（记住我）

### 前端处理
- **输入**：复选框，可选
- **默认值**：`false`（不记住）

### 后端处理

```csharp
// AuthEndpoints.cs
var result = await signInManager.PasswordSignInAsync(
    user,
    request.Password,
    isPersistent: request.RememberMe,  // 控制 cookie 持久化
    lockoutOnFailure: true);
```

| 属性 | 值 | 说明 |
|------|------|------|
| **类型** | `bool` | 布尔值 |
| **默认值** | `false` | 可选，默认不记住 |
| **作用** | Cookie 持久化 | `true` 时创建持久 cookie |

### 注意事项
- 不影响登录验证结果
- 仅影响 cookie 的过期策略

---

## 4. 账号锁定机制

### ABP Identity 默认配置

| 参数 | 值 | 说明 |
|------|------|------|
| **最大失败次数** | 5 次 | `MaxFailedAccessAttempts` |
| **锁定时长** | 5 分钟 | `DefaultLockoutTimeSpan` |
| **启用锁定** | ✅ 是 | `lockoutOnFailure: true` |

### 后端代码

```csharp
// AuthEndpoints.cs
var result = await signInManager.PasswordSignInAsync(
    user,
    request.Password,
    isPersistent: request.RememberMe,
    lockoutOnFailure: true);  // 启用锁定机制

if (result.IsLockedOut)
{
    return Results.Json(new { error = "Account is locked. Please try again later." }, statusCode: 423);
}
```

### 锁定触发条件
1. 连续 5 次登录失败
2. 账号被锁定 5 分钟
3. 锁定期间返回 HTTP 423（Locked）

---

## 5. 登录结果状态码

| 状态码 | 说明 | 错误消息 |
|--------|------|----------|
| **200** | 登录成功 | `{ success: true }` |
| **400** | 缺少必填字段 | `"Username and password are required."` |
| **401** | 用户名/密码错误 | `"Invalid username or password."` |
| **403** | 邮箱未验证 | `"Login not allowed. Please verify your email."` |
| **423** | 账号已锁定 | `"Account is locked. Please try again later."` |

---

## 总结表格

| 字段 | 前端限制 | 后端限制 | 说明 |
|------|---------|---------|------|
| **Username or Email** | 必填 | 必填<br>最大 256 字符 | 支持用户名或邮箱 |
| **Password** | 必填 | 必填<br>6-128 字符 | 登录时不校验复杂度 |
| **Remember Me** | 可选 | 可选<br>默认 false | 控制 cookie 持久化 |

---

## 安全注意事项

### 错误消息安全性
- **不泄露账号存在性**：无论用户名不存在还是密码错误，都返回相同的错误消息
  ```csharp
  return Results.Json(new { error = "Invalid username or password." }, statusCode: 401);
  ```

### 锁定机制
- **防止暴力破解**：5 次失败后锁定 5 分钟
- **测试风险**：自动化测试时需注意避免触发锁定

---

## 测试建议

### 功能测试
| 测试场景 | 优先级 | 说明 |
|----------|--------|------|
| 用户名登录 | P1 | 使用用户名成功登录 |
| 邮箱登录 | P1 | 使用邮箱成功登录 |
| Remember Me | P2 | 验证 cookie 持久化 |

### 边界测试
| 测试场景 | 优先级 | 说明 |
|----------|--------|------|
| 用户名/邮箱最大长度 | P2 | 256 字符边界 |
| 密码最大长度 | P2 | 128 字符边界 |

### 安全测试
| 测试场景 | 优先级 | 说明 |
|----------|--------|------|
| 错误消息安全性 | P1 | 不泄露账号存在性 |
| 账号锁定机制 | P2 | 5 次失败后锁定（谨慎测试） |
| XSS/SQLi 注入 | P1 | 输入恶意 payload |

---

## 参考文档

- [ABP Framework - Identity Module](https://docs.abp.io/en/abp/latest/Modules/Identity)
- [ASP.NET Core Identity - Lockout Options](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/identity-configuration#lockout)
- 后端代码：`apps/Aevatar.VibeResearching/src/host/HttpApi.Host/MinimalApis/AuthEndpoints.cs`

---

*文档版本: 1.0*  
*创建日期: 2026-02-02*  
*最后更新: 2026-02-02*

