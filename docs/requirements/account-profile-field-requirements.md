# Account Profile 页面字段约束

> 基于后端代码分析：`/apps/Aevatar.VibeResearching/src/host/HttpApi.Host/MinimalApis/`

---

## 1. Profile 基本信息字段

### 1.1 只读字段

| 字段 | 类型 | 说明 |
|------|------|------|
| **UserName** | string | 用户名，不可修改 |
| **Email** | string | 邮箱，不可修改 |
| **Id** | GUID | 用户 ID，系统生成 |

### 1.2 可编辑字段

| 字段 | 类型 | 必填 | ABP 常量 | 实际限制 | 说明 |
|------|------|------|----------|----------|------|
| **Name** | string | 否 | 64 (`MaxNameLength`) | ❌ 无限制 | 名（First Name） |
| **Surname** | string | 否 | 64 (`MaxSurnameLength`) | ❌ 无限制 | 姓（Last Name） |
| **PhoneNumber** | string | 否 | 16 (`MaxPhoneNumberLength`) | ❌ 无限制 | 电话号码 |
| **DisplayName** | string | 否 | - | ❌ 无限制 | 显示名称（自定义扩展字段） |
| **Bio** | string | 否 | - | ❌ 无限制 | 个人简介（自定义扩展字段） |

> **⚠️ 重要**: 项目使用 **MongoDB**（无模式数据库），ABP 的 `HasMaxLength` 约束仅对 EF Core + 关系型数据库生效。
> 后端 API 直接调用 `user.Name = body.Name` 等赋值操作，不进行显式长度校验。
> 
> 参考 ABP 源码常量：
> - `IdentityUserConsts.MaxNameLength = 64`
> - `IdentityUserConsts.MaxSurnameLength = 64`
> - `IdentityUserConsts.MaxPhoneNumberLength = 16`

### 1.3 API 端点

| 功能 | 端点 | 方法 | 认证 |
|------|------|------|------|
| 获取个人资料 | `/api/vibe/my-profile` | GET | 需要 |
| 更新个人资料 | `/api/vibe/my-profile` | PUT | 需要 |

### 1.4 请求/响应格式

```typescript
// 获取 Profile 响应
interface ProfileResponse {
  id: string
  userName: string
  email: string
  name: string
  surname: string
  phoneNumber: string
  displayName: string
  bio: string
  hasProfilePicture: boolean
}

// 更新 Profile 请求
interface UpdateProfileRequest {
  name?: string
  surname?: string
  phoneNumber?: string
  displayName?: string
  bio?: string
}
```

---

## 2. 头像上传约束

### 2.1 文件限制

| 限制项 | 前端验证 | 后端验证 | 值 |
|--------|----------|----------|-----|
| **最大文件大小** | ✅ | ✅ | **2MB** (2 * 1024 * 1024 bytes) |
| **允许的 MIME 类型** | ✅ | ✅ | `image/jpeg`, `image/png`, `image/webp` |
| **文件头验证 (Magic Bytes)** | ❌ | ✅ | 见下表 |

### 2.2 Magic Bytes 验证

| 格式 | Magic Bytes | 说明 |
|------|-------------|------|
| JPEG | `FF D8 FF` | 前 3 字节 |
| PNG | `89 50 4E 47` | 前 4 字节 |
| WebP | `52 49 46 46 ... 57 45 42 50` | RIFF 头 + WEBP 标识 |

### 2.3 API 端点

| 功能 | 端点 | 方法 | 认证 |
|------|------|------|------|
| 上传头像 | `/api/account/profile-picture` | PUT | 需要 |
| 获取头像 | `/api/account/profile-picture/{userId}` | GET | 不需要 |
| 删除头像 | `/api/account/profile-picture` | DELETE | 需要 |

### 2.4 错误响应

| 场景 | HTTP 状态码 | 错误消息 |
|------|-------------|----------|
| 未提供文件 | 400 | "No file provided" |
| 文件过大 | 400 | "File too large. Maximum size is 2MB." |
| 文件类型不允许 | 400 | "Invalid file type. Allowed: JPG, PNG, WebP." |
| 文件内容与格式不符 | 400 | "File content does not match a supported image format." |
| 未认证 | 401 | Unauthorized |

---

## 3. Change Password 约束

### 3.1 字段说明

| 字段 | 前端名称 | 必填 | 说明 |
|------|----------|------|------|
| **currentPassword** | Current Password | ✅ | 当前密码 |
| **newPassword** | New Password | ✅ | 新密码 |
| **confirmPassword** | Confirm New Password | ✅ (前端) | 确认新密码，仅前端校验，不提交后端 |

### 3.2 密码策略

| 规则 | 前端验证 | 后端验证 | 说明 |
|------|----------|----------|------|
| **最小长度** | ✅ | ✅ | 6 字符 |
| **最大长度** | ❌ | ❌ | 无限制 (MongoDB 不强制) |
| **需要小写字母** | ✅ | ✅ | 至少 1 个 `a-z` |
| **需要大写字母** | ✅ | ✅ | 至少 1 个 `A-Z` |
| **需要数字** | ✅ | ✅ | 至少 1 个 `0-9` |
| **需要特殊字符** | ✅ | ✅ | 至少 1 个 `!@#$%^&*()_+-=[]{};\|,.<>/?` 等 |
| **确认密码匹配** | ✅ | ❌ | 仅前端验证 |

> **注意**: 由于项目使用 MongoDB，ABP Identity 的 `MaxLength` 约束不会被强制执行。

### 3.3 前端验证逻辑

```typescript
// 1. 确认密码匹配验证
if (formData.newPassword !== formData.confirmPassword) {
  showError("New passwords do not match")
  return
}

// 2. 密码策略正则验证
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{6,}$/
if (!passwordRegex.test(formData.newPassword)) {
  showError("Password must be at least 6 characters and contain uppercase, lowercase, number, and special character")
  return
}
```

### 3.4 后端验证逻辑

```csharp
// ProfileEndpoints.cs
app.MapPost("/api/vibe/change-password", async (...) =>
{
    // 1. 认证检查
    if (!currentUser.IsAuthenticated || currentUser.Id == null)
        return Results.Unauthorized();

    // 2. 必填字段检查
    if (body == null || string.IsNullOrWhiteSpace(body.CurrentPassword) 
        || string.IsNullOrWhiteSpace(body.NewPassword))
        return Results.BadRequest(new { error = "currentPassword and newPassword are required" });

    // 3. ABP Identity 密码策略验证 (通过 ChangePasswordAsync)
    var result = await userManager.ChangePasswordAsync(user, body.CurrentPassword, body.NewPassword);
    if (!result.Succeeded)
    {
        var errors = result.Errors.Select(e => e.Description).ToList();
        return Results.BadRequest(new { error = "Password change failed", details = errors });
    }
});
```

### 3.5 API 端点

| 功能 | 端点 | 方法 | 认证 |
|------|------|------|------|
| 修改密码 | `/api/vibe/change-password` | POST | 需要 |

### 3.6 请求/响应格式

```typescript
// 请求
interface ChangePasswordRequest {
  currentPassword: string  // 必填
  newPassword: string      // 必填
}

// 成功响应
{ "ok": true }

// 失败响应
{
  "error": "Password change failed",
  "details": ["Passwords must have at least one uppercase ('A'-'Z').", ...]
}
```

### 3.7 错误响应

| 场景 | HTTP 状态码 | 错误消息 |
|------|-------------|----------|
| 缺少必填字段 | 400 | "currentPassword and newPassword are required" |
| 密码不符合策略 | 400 | "Password change failed" + `details` 数组 |
| 当前密码错误 | 400 | "Password change failed" |
| 未认证 | 401 | Unauthorized |

### 3.8 UI 输入框属性

| 输入框 | `type` | `required` | `maxlength` | `placeholder` |
|--------|--------|------------|-------------|---------------|
| Current Password | password | ✅ | ❌ | "Enter current password" |
| New Password | password | ✅ | ❌ | "Enter new password" |
| Confirm Password | password | ✅ | ❌ | "Confirm new password" |

> **提示**: 输入框下方有提示文字："Min 6 characters with uppercase, lowercase, number & special character"

---

## 4. 测试建议

### 4.1 Profile 基本信息测试

- [ ] 验证只读字段不可编辑 (UserName, Email)
- [ ] 验证可编辑字段保存成功
- [ ] 验证空值保存
- [ ] 验证特殊字符处理

### 4.2 头像上传测试

- [ ] 上传 < 2MB 的 JPG/PNG/WebP 图片 → 成功
- [ ] 上传 = 2MB 的图片 → 成功
- [ ] 上传 > 2MB 的图片 → 拒绝
- [ ] 上传 GIF 格式 → 拒绝
- [ ] 上传 BMP 格式 → 拒绝
- [ ] 上传伪造后缀的非图片文件 → 拒绝 (Magic Bytes 验证)
- [ ] 删除头像 → 成功
- [ ] 替换头像 → 成功

### 4.3 修改密码测试

**P0 - 核心功能**
- [ ] 使用正确的当前密码修改 → 成功，密码生效
- [ ] 修改成功后可用新密码登录

**P1 - 字段验证**
- [ ] 使用错误的当前密码修改 → 失败 400
- [ ] 新密码与确认密码不匹配 → 前端阻止，Toast 提示
- [ ] 当前密码为空 → 前端 required 阻止 或 后端 400
- [ ] 新密码为空 → 前端 required 阻止 或 后端 400
- [ ] 确认密码为空 → 前端 required 阻止

**P1 - 密码策略验证**
- [ ] 新密码少于 6 字符 → 前端阻止 (正则)
- [ ] 新密码缺少大写字母 → 前端阻止 (正则)
- [ ] 新密码缺少小写字母 → 前端阻止 (正则)
- [ ] 新密码缺少数字 → 前端阻止 (正则)
- [ ] 新密码缺少特殊字符 → 前端阻止 (正则)
- [ ] 新密码 = 6 字符且符合策略 → 成功 (边界)

**P2 - UI 交互**
- [ ] 密码输入框默认隐藏 (type=password)
- [ ] 密码可见性切换按钮工作正常
- [ ] 提交按钮加载状态显示
- [ ] 成功后表单清空

**Security - 安全测试**
- [ ] 未登录访问修改密码页 → 重定向到登录
- [ ] XSS 注入尝试 → 无脚本执行
- [ ] SQL 注入尝试 → 无数据库错误泄露

---

## 5. 代码参考

### 后端文件

- `ProfileEndpoints.cs` - Profile CRUD 接口
- `ProfilePictureEndpoints.cs` - 头像上传接口
- `ImageFormatValidator.cs` - 图片格式验证

### 前端文件

- `lib/abp/profile.ts` - Profile API 封装
- `components/account/panels/profile-panel.tsx` - Profile 编辑面板
- `components/account/panels/password-panel.tsx` - 修改密码面板
- `components/account/avatar-modals.tsx` - 头像上传弹窗

