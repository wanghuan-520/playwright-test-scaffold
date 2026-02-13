# Admin Permissions i18n 修复方案

## 问题描述

ABP Identity 权限显示为中文（身份标识管理、角色管理、创建、编辑等），但 UI 界面是英文，导致 i18n 不一致。

## 原因分析

ABP Framework 的权限本地化资源通过以下方式配置：

1. **ABP 内置本地化资源**：ABP Identity 模块自带多语言资源文件（包含在 NuGet 包中）
   - ABP Framework 内置了中文（`zh-Hans`）和英文（`en`）的本地化资源
   - "身份标识管理"、"角色管理"、"创建"、"编辑" 等中文翻译来自 ABP 内置资源
2. **项目自定义本地化资源**：可以覆盖或扩展默认资源
   - 项目中有 `zh-Hans.json` 文件，但只包含应用级别的翻译
3. **语言环境配置**：通过 `AbpLocalizationOptions` 配置默认语言
   - 如果默认语言设置为 `zh-Hans` 或 `zh-CN`，ABP 会使用中文资源

**当前问题**：
- ABP Identity 权限显示为中文，说明后端默认语言可能是中文
- 或者前端/API 请求时指定了中文语言环境

## 修复方案

### 方案 1：修改默认语言为英文（推荐）

在后端的 `HttpApi.Host` 项目的 `ConfigureServices` 方法中：

```csharp
// 文件路径：apps/Aevatar.VibeResearching/src/host/HttpApi.Host/VibeResearchingHttpApiHostModule.cs

using Volo.Abp.Localization;  // 添加 using

public override void ConfigureServices(ServiceConfigurationContext context)
{
    // ... 其他配置 ...
    
    // 设置默认语言为英文
    Configure<AbpLocalizationOptions>(options =>
    {
        // 设置默认语言为英文
        options.DefaultLanguageName = "en";
        
        // 配置支持的语言（可选，如果需要多语言支持）
        options.Languages.Clear();
        options.Languages.Add(new LanguageInfo("en", "en", "English", "gb"));
        options.Languages.Add(new LanguageInfo("zh-Hans", "zh-Hans", "简体中文", "cn"));
    });
    
    // ... 其他配置 ...
}
```

**注意**：
- 如果项目中已经有 `Configure<AbpLocalizationOptions>` 的配置，只需要修改 `DefaultLanguageName = "en"`
- 如果没有，需要添加上述配置

### 方案 2：移除或重命名中文本地化资源文件

如果项目中有自定义的中文本地化资源文件，可以：

1. **移除中文资源文件**（如果不需要中文支持）：
   ```bash
   # 查找并删除 zh-CN.json 文件
   find . -name "zh-CN.json" -path "*/Localization/*"
   ```

2. **保留中文资源但设置默认语言为英文**（如果需要多语言支持）：
   - 使用方案 1 设置默认语言为 `en`
   - 保留中文资源文件，用户可以通过语言切换功能选择中文

### 方案 3：修改 ABP Identity 本地化资源

如果项目中有覆盖 ABP Identity 本地化资源的文件，需要修改：

1. **查找本地化资源文件**：
   ```bash
   # 查找包含 "身份标识管理" 的资源文件
   find . -name "*.json" -exec grep -l "身份标识管理" {} \;
   ```

2. **修改资源文件**：
   - 将中文翻译改为英文
   - 或者删除中文资源，使用 ABP 默认的英文资源

## 后端代码路径

根据项目结构，需要修改的文件：

```
/Users/wanghuan/aelf/Cursor/viberesearch/aevatar-agent-framework/
├── apps/Aevatar.VibeResearching/src/
│   └── host/HttpApi.Host/
│       └── VibeResearchingHttpApiHostModule.cs  # 主配置模块（需要修改）
└── apps/Aevatar.App/src/
    └── Aevatar.App.Domain.Shared/Localization/
        └── App/zh-Hans.json  # 应用级中文本地化（不影响 ABP Identity）
```

**关键文件**：
- `VibeResearchingHttpApiHostModule.cs` - 需要在这里配置默认语言为英文

## 验证步骤

修复后，验证以下内容：

1. **API 返回的权限名称**：
   ```bash
   curl 'http://localhost:5173/api/permission-management/permissions?providerName=R&providerKey=test_role4' \
     -H 'Accept: application/json' \
     -H 'Cookie: ...'
   ```
   - 检查 `displayName` 字段是否为英文

2. **前端页面显示**：
   - 访问 `/admin/permissions` 页面
   - 检查权限名称是否显示为英文

3. **语言一致性**：
   - 确保所有权限组（ABP Identity、SettingManagement、Sessions 等）都使用英文
   - 确保 UI 界面和权限名称语言一致

## 注意事项

1. **多语言支持**：如果项目需要支持多语言，建议：
   - 设置默认语言为英文
   - 保留中文资源文件
   - 通过前端语言切换功能让用户选择语言

2. **ABP 内置资源**：ABP Framework 内置了多语言资源，如果项目没有覆盖，会使用 ABP 默认的英文资源。

3. **自定义权限**：除了修复 ABP Identity 的中文显示，还需要为自定义权限（Sessions、Knowledge、Platform、Agents）添加英文本地化资源（见 Bug #8）。

## 相关 Bug

- **Bug #3**：权限名称显示中文，但界面是英文，i18n 不一致
- **Bug #8**：自定义权限未翻译，显示为 `Permission:xxx` 格式
- **Bug #9**：权限混用中英文

修复后，这三个 bug 都应该得到解决。

