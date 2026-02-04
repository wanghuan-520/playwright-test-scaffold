# Admin 管理页面需求文档

## 概述

Admin 管理页面包含四个核心模块：
- `/admin/users` - 用户管理
- `/admin/roles` - 角色管理
- `/admin/permissions` - 权限管理
- `/admin/settings` - 平台设置

所有 admin 页面需要 **admin 角色**才能访问，非 admin 用户访问返回 403。

---

## 1. /admin/users - 用户管理

### 1.1 后端约束（ABP Identity）

| 字段 | ABP 常量 | 默认值 | 说明 |
|------|----------|--------|------|
| Username | `MaxUserNameLength` | 256 | 用户名最大长度 |
| Email | `MaxEmailLength` | 256 | 邮箱最大长度 |
| Password | `RequiredLength` | 6 | 密码最小长度 |
| Name | `MaxNameLength` | 64 | 名字最大长度 |
| Surname | `MaxSurnameLength` | 64 | 姓氏最大长度 |
| PhoneNumber | `MaxPhoneNumberLength` | 16 | 电话最大长度 |

**注意**：项目使用 MongoDB，部分长度限制在数据库层面不强制执行。

### 1.2 权限要求

```
Platform.UserManagement - 用户管理基础权限
Platform.UserManagement.ManageRoles - 管理用户角色
Platform.UserManagement.ManagePermissions - 管理用户权限
```

### 1.3 API 端点

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/identity/users` | 获取用户列表 | UserManagement |
| GET | `/api/identity/users/{id}` | 获取用户详情 | UserManagement |
| POST | `/api/identity/users` | 创建用户 | UserManagement |
| PUT | `/api/identity/users/{id}` | 更新用户 | UserManagement |
| DELETE | `/api/identity/users/{id}` | 删除用户 | UserManagement |
| PUT | `/api/identity/users/{id}/roles` | 分配角色 | ManageRoles |

### 1.4 前端字段约束

| 字段 | 是否必填 | maxlength | placeholder | 验证 |
|------|----------|-----------|-------------|------|
| First Name | 否 | - | John | - |
| Last Name | 否 | - | Doe | - |
| Email | 是 | - | john@example.com | 邮箱格式 |
| Username | 是 | - | johndoe | - |
| Password | 是 | - | Enter password | 策略验证 |
| Phone Number | 否 | - | +1 (555) 000-0000 | - |
| Roles | 否 | - | - | 多选 |
| Active | 否 | - | - | Switch |

### 1.5 已知问题

| Bug | 描述 | 优先级 |
|-----|------|--------|
| #1 | 页面初始加载时 Total Users 显示 0，数据异步加载后才显示真实数量 | P2 |
| #5 | HTML DOM 嵌套错误（React 组件结构问题） | P2 |
| #6 | Add User 对话框缺少 DialogTitle 和 aria-describedby（可访问性） | P3 |

---

## 2. /admin/roles - 角色管理

### 2.1 后端约束

| 属性 | 类型 | 说明 |
|------|------|------|
| Name | string | 角色名称（唯一） |
| IsDefault | bool | 是否为默认角色（新用户自动分配） |
| IsPublic | bool | 是否公开可见 |
| IsStatic | bool | 是否为静态角色（不可删除） |

### 2.2 预定义角色

```csharp
// member 角色 - 默认分配给新用户
new IdentityRole(Guid.NewGuid(), "member") {
    IsDefault = true,
    IsPublic = true,
    IsStatic = true
};

// admin 角色 - 管理员
new IdentityRole(Guid.NewGuid(), "admin") {
    IsDefault = false,
    IsPublic = true,
    IsStatic = true
};
```

### 2.3 权限要求

```
Platform.UserManagement.ManageRoles - 管理角色
```

### 2.4 API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/identity/roles` | 获取角色列表 |
| GET | `/api/identity/roles/{id}` | 获取角色详情 |
| POST | `/api/identity/roles` | 创建角色 |
| PUT | `/api/identity/roles/{id}` | 更新角色 |
| DELETE | `/api/identity/roles/{id}` | 删除角色 |

### 2.5 已知问题

| Bug | 描述 | 优先级 |
|-----|------|--------|
| #2 | member 和 admin 角色都显示 547 Users，数据统计不一致 | P1 |

---

## 3. /admin/permissions - 权限管理

### 3.1 权限定义结构

权限采用层级结构定义：

```
Permission:Group
├── Permission:Group.Permission1
│   ├── Permission:Group.Permission1.Child1
│   └── Permission:Group.Permission1.Child2
└── Permission:Group.Permission2
```

### 3.2 系统权限分组

#### ABP Identity 权限（身份标识管理）
```
AbpIdentity
├── Roles - 角色管理
│   ├── Create - 创建
│   ├── Edit - 编辑
│   ├── Delete - 删除
│   └── ManagePermissions - 更改权限
└── Users - 用户管理
    ├── Create - 创建
    ├── Edit - 编辑
    ├── Delete - 删除
    ├── ManageRoles - 管理角色
    └── ManagePermissions - 更改权限
```

#### Settings 权限（设置管理）
```
SettingManagement
├── Emailing - 邮件
├── EmailingTest - 邮件测试
└── TimeZone - 时区
```

#### Sessions 权限（会话管理）
```
VibeResearching.Sessions
├── Create - 创建会话
├── Edit - 编辑会话
├── Delete - 删除会话
├── Admin - 管理员权限
├── View - 查看会话
├── ListAll - 列出所有会话
├── Pause - 暂停会话
├── Resume - 恢复会话
└── Terminate - 终止会话
```

#### Knowledge 权限（知识管理）
```
Knowledge
├── Dag.View - 查看 DAG
├── Dag.Edit - 编辑 DAG
├── Facts.Create - 创建事实
├── Facts.Vote - 投票
├── Facts.Verify - 验证
└── Facts.Promote - 提升
```

#### Platform 权限（平台管理）
```
Platform
├── Settings - 设置管理
│   └── LLM - LLM 配置
└── UserManagement - 用户管理
    ├── ManageRoles - 管理角色
    └── ManagePermissions - 管理权限
```

#### Agents 权限（代理管理）
```
VibeResearching.Agents
├── Orchestration - 编排
│   ├── Execute - 执行
│   └── Cancel - 取消
├── Pivot - 转换
│   └── Execute - 执行
└── ReviewAgent - 审查代理
    └── Trigger - 触发
```

### 3.3 角色默认权限分配

#### member 角色权限
```csharp
var memberPermissions = new[] {
    SessionsPermissions.Sessions.View,
    SessionsPermissions.Sessions.ListAll,
    SessionsPermissions.Sessions.Create,
    SessionsPermissions.Sessions.Edit,
    SessionsPermissions.Sessions.Pause,
    SessionsPermissions.Sessions.Resume,
    SessionsPermissions.Sessions.Terminate,
    "VibeResearching.Agents.Orchestration.Execute",
    "VibeResearching.Agents.Orchestration.Cancel",
};
```

#### admin 角色额外权限
```csharp
var adminExtraPermissions = new[] {
    SessionsPermissions.Sessions.Delete,
    SessionsPermissions.Sessions.Admin,
    "VibeResearching.Agents.ReviewAgent.Trigger",
    PlatformPermissions.Settings.Default,
    PlatformPermissions.Settings.LLM,
    PlatformPermissions.UserManagement.Default,
    PlatformPermissions.UserManagement.ManageRoles,
    PlatformPermissions.UserManagement.ManagePermissions,
};
```

### 3.4 API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/permission-management/permissions` | 获取权限定义 |
| GET | `/api/permission-management/permissions?providerName=R&providerKey={roleName}` | 获取角色权限 |
| PUT | `/api/permission-management/permissions` | 更新权限 |
| GET | `/api/account/my-permissions` | 获取当前用户权限 |

### 3.5 已知问题

| Bug | 描述 | 优先级 |
|-----|------|--------|
| #3 | 权限名称显示中文（身份标识管理、角色管理等），但界面是英文，i18n 不一致 | P2 |

---

## 4. /admin/settings - 平台设置

### 4.1 设置 Tab 结构

| Tab | 功能 | 权限要求 |
|-----|------|----------|
| Tools & MCP | 工具和 MCP 连接管理 | Platform.Settings |
| LLM Providers | LLM 提供商配置 | Platform.Settings.LLM |
| Agents | 代理配置（需要会话连接） | Platform.Settings |
| Advanced | 高级设置（密钥管理） | Platform.Settings |

### 4.2 Tools & MCP Tab

| 功能 | 说明 |
|------|------|
| Reconnect MCP | 重连 MCP 服务 |
| Update Skills | 更新技能 |
| SkillsMP Marketplace | 技能市场 |
| Tool Statistics | 工具统计（Total, MCP, Skills） |

### 4.3 LLM Providers Tab

#### 支持的提供商

| 分类 | 提供商 |
|------|--------|
| Configured | 已配置的提供商（显示 ✓） |
| Popular | Anthropic, Claude, Gemini, Google, OpenAI, OpenRouter |
| Other | Azure OpenAI, DashScope, Groq, Mistral, Together |

#### 配置存储

```
LLMProviders:Default - 默认提供商
LLMProviders:Providers:{name}:ProviderType
LLMProviders:Providers:{name}:Endpoint
LLMProviders:Providers:{name}:Model
LLMProviders:Providers:{name}:ApiKey
```

### 4.4 Advanced Tab

用于直接管理加密的用户密钥。

| 字段 | 说明 |
|------|------|
| Secret Key | 密钥名称，格式：`Provider:Type`（如 `OpenAI:ApiKey`） |
| Secret Value | 密钥值 |

### 4.5 API 端点（仅限 localhost）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/llm/providers` | 获取提供商目录 |
| GET | `/api/llm/instances` | 获取已配置的提供商实例 |
| GET | `/api/llm/default` | 获取默认提供商 |
| POST | `/api/llm/default` | 设置默认提供商 |
| GET | `/api/llm/provider/{name}` | 获取提供商详情 |
| GET | `/api/llm/api-key/{name}` | 获取 API Key 状态 |
| POST | `/api/llm/api-key` | 设置 API Key |
| DELETE | `/api/llm/api-key/{name}` | 删除 API Key |
| POST | `/api/llm/instance` | 创建/更新提供商实例 |
| POST | `/api/secrets/set` | 设置密钥 |
| POST | `/api/secrets/remove` | 删除密钥 |

**安全限制**：所有写入接口仅限 localhost（loopback-only）访问。

### 4.6 已知问题

| Bug | 描述 | 优先级 |
|-----|------|--------|
| #4 | "Reconnect MCP" 按钮禁用，但提示文字让用户点击它，UX 矛盾 | P2 |

---

## 5. 测试建议

### 5.1 Users 测试（/admin/users）

| 优先级 | 测试点 |
|--------|--------|
| P0 | 页面加载、核心控件可见 |
| P0 | 数据加载正常（Total Users 统计） |
| P0 | Add User 对话框打开/关闭 |
| P1 | 创建用户（字段验证） |
| P1 | 编辑用户 |
| P1 | 删除用户 |
| P1 | 分配角色 |
| P2 | 搜索用户 |
| P2 | 过滤（按角色、状态） |

### 5.2 Roles 测试（/admin/roles）

| 优先级 | 测试点 |
|--------|--------|
| P0 | 页面加载、角色卡片可见 |
| P0 | member 和 admin 角色存在 |
| P1 | 创建角色 |
| P1 | 编辑角色 |
| P1 | 删除角色（非静态） |
| P2 | 角色用户统计准确性 |

### 5.3 Permissions 测试（/admin/permissions）

| 优先级 | 测试点 |
|--------|--------|
| P0 | 页面加载、Tab 切换 |
| P0 | 角色选择器正常 |
| P1 | 权限勾选/取消 |
| P1 | Grant All / Revoke All |
| P1 | Save 保存权限 |
| P2 | 权限搜索 |
| P2 | i18n 一致性检查 |

### 5.4 Settings 测试（/admin/settings）

| 优先级 | 测试点 |
|--------|--------|
| P0 | 页面加载、Tab 切换 |
| P0 | LLM Providers 列表显示 |
| P1 | 配置 LLM Provider |
| P1 | 设置默认 Provider |
| P1 | 保存/删除 Secret |
| P2 | 连接测试 |
| P2 | 模型列表获取 |

---

## 6. 权限矩阵

| 功能 | member | admin |
|------|--------|-------|
| 查看 /admin/users | ❌ | ✅ |
| 创建用户 | ❌ | ✅ |
| 编辑用户 | ❌ | ✅ |
| 删除用户 | ❌ | ✅ |
| 管理角色 | ❌ | ✅ |
| 管理权限 | ❌ | ✅ |
| 平台设置 | ❌ | ✅ |
| LLM 配置 | ❌ | ✅ |

