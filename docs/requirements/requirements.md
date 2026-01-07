# 项目特定规则 - Aevatar Agent Station（最简）

## 核心原则（必须）

**页面输入框的校验规则，以后端 ABP 框架限制为真理源。**

- **后端 ABP 是权威**：Required / MaxLength / Regex / PasswordPolicy 等以后端为准
- **前端可以更宽松**：但后端必须拦截所有不合规输入
- **用例必须覆盖 ABP 规则**：即使前端没有做相同限制

## 规则来源优先级（生成用例时）

1. **需求文档明确说明** → 按需求
2. **前端代码已有验证逻辑** → 参考前端表现（错误提示/按钮禁用/字段 invalid）
3. **后端 ABP 有限制** → **以后端为准（必须覆盖）**
4. 都不明确 → 最小集：必填 + maxLength（再补 1 条代表性边界）

## 用例策略（最小可落地）

- **P0**：页面可加载 + 主流程成功（不要堆每字段必填）
- **P1（字段矩阵为主）**：
  - 边界：min-1 / min / max / max+1
  - 格式：ABP 明确要求的格式/字符集
  - 密码策略：按 policy 拆用例（missing_digit / missing_uppercase ...）
- **P2**：UI/可访问性/键盘导航（按需）

## 断言分层（必须）

- **前端断言（可观测）**：错误提示/字段 invalid/按钮不可提交/请求未发送
- **后端断言（权威）**：同一非法输入后端必须拒绝（4xx + 可诊断错误体）

## （可选）页面别名 → 路由（给人/AI 作为备忘）

| 别名（alias） | path（相对前端 base url） | 说明 |
|---|---|---|
| 修改密码页面, Change Password | /admin/profile/change-password | 个人设置-修改密码 |
| 个人设置页面, Personal Settings | /admin/profile | 个人设置-基本信息 |

---

## 后端 ABP 字段/策略约束（按页面汇总）

说明：
- **来源**：以运行时 Swagger/ABP ApplicationConfiguration 为准（本仓库证据链：`docs/test-plans/artifacts/*/{backend_swagger.json,abp_app_config.json}`）。
- **前端页面**与**后端接口**存在跨域：`/admin/*`（前端站点）会调用后端 ABP API（`/api/*`）；`/Account/*` 则是 **AuthServer 的后端页面**（`https://localhost:44320`）。
- **注意**：部分字段在 Swagger 中标记为 `nullable`，但在 ABP/Identity 业务规则下仍可能“逻辑必填”（例如用户必须有 `userName/email`）。测试用例应同时覆盖 **前端可观测** + **后端 4xx 拒绝** 两层断言。

### 0) 全局 Identity/Account 开关（来自 ABP setting.values）

- **自注册**：`Abp.Account.IsSelfRegistrationEnabled = true`
- **本地登录**：`Abp.Account.EnableLocalLogin = true`
- **允许用户修改用户名**：`Abp.Identity.User.IsUserNameUpdateEnabled = True`
- **允许用户修改邮箱**：`Abp.Identity.User.IsEmailUpdateEnabled = True`

### 1) 登录（Login /Account/Login → /api/account/login）

接口：`POST /api/account/login`  
请求体：`Volo.Abp.Account.Web.Areas.Account.Controllers.Models.UserLoginInfo`

- **userNameOrEmailAddress**
  - required
  - maxLength: **255**
- **password**
  - required
  - maxLength: **32**
  - format: `password`
- **rememberMe**
  - boolean

登录失败/锁定策略（ABP setting.values）：
- **最大失败次数**：`Abp.Identity.Lockout.MaxFailedAccessAttempts = 5`
- **锁定时长（秒）**：`Abp.Identity.Lockout.LockoutDuration = 300`
- **新用户允许被锁定**：`Abp.Identity.Lockout.AllowedForNewUsers = True`
- **RequireConfirmedEmail**：`Abp.Identity.SignIn.RequireConfirmedEmail = False`
- **RequireConfirmedPhoneNumber**：`Abp.Identity.SignIn.RequireConfirmedPhoneNumber = False`
- **EnablePhoneNumberConfirmation**：`Abp.Identity.SignIn.EnablePhoneNumberConfirmation = True`

#### 1.x 前端输入限制现状（可观测证据）

说明：
- `/Account/Login` 是 AuthServer 后端页面（Razor/ABP）。其输入框是否带 `maxlength` 由 ABP/后端注解生成。
- 本仓库已对 `/Account/Login` 做 DOM `maxlength` 取证（见下方证据链）。

证据链（本仓库）：
- `tests/Account/Login/test_Login_p1_frontend_maxlength_evidence.py`
  - 读取 `input.getAttribute('maxlength')`
  - 写入超长字符串后读取 `page.input_value(...)` 的实际长度
  - Allure 附件：`*_maxlength_evidence`（maxlength_attr/typed_len/actual_len/expected_max）+ 截图

### 2) 注册（Register /Account/Register → /api/account/register）

接口：`POST /api/account/register`  
请求体：`Volo.Abp.Account.RegisterDto`

- **appName**
  - required
  - minLength: **1**
- **userName**
  - required
  - maxLength: **256**
- **emailAddress**
  - required
  - maxLength: **256**
  - format: `email`
- **password**
  - required
  - maxLength: **128**
  - format: `password`

#### 2.x 前端输入限制现状（可观测证据）

AuthServer `/Account/Register`（后端页面）已通过 UI 自动化取证确认存在输入层限制：
- Username：存在 `maxlength`，超长输入后实际 `input_value` 长度会被限制在 **≤ 256**
- Email address：存在 `maxlength`，超长输入后实际 `input_value` 长度会被限制在 **≤ 256**
- Password：存在 `maxlength`，超长输入后实际 `input_value` 长度会被限制在 **≤ 128**

证据链（本仓库）：
- `tests/Account/Register/test_Register_p1_frontend_maxlength_evidence.py`
  - 读取 `input.getAttribute('maxlength')`
  - 写入超长字符串后读取 `page.input_value(...)` 的实际长度
  - Allure 附件：`*_maxlength_evidence`（maxlength_attr/typed_len/actual_len/expected_max）+ 截图

### 3) 忘记密码（Forgot Password /Account/ForgotPassword）

#### 3.1 发送重置验证码

接口：`POST /api/account/send-password-reset-code`  
请求体：`Volo.Abp.Account.SendPasswordResetCodeDto`

- **appName**
  - required
  - minLength: **1**
- **email**
  - required
  - maxLength: **256**
  - format: `email`
- **returnUrl / returnUrlHash**
  - optional

#### 3.2 验证 token

接口：`POST /api/account/verify-password-reset-token`  
请求体：`Volo.Abp.Account.VerifyPasswordResetTokenInput`

- **userId**: uuid（可选）
- **resetToken**
  - required
  - minLength: **1**

#### 3.3 重置密码

接口：`POST /api/account/reset-password`  
请求体：`Volo.Abp.Account.ResetPasswordDto`

- **resetToken**
  - required
  - minLength: **1**
- **password**
  - required
  - minLength: **1**
  - （密码策略仍以 Identity PasswordPolicy 为准，见“修改密码/密码策略”）

#### 3.x 前端输入限制现状（可观测证据）

说明：
- `/Account/ForgotPassword` 是 AuthServer 后端页面（Razor/ABP），其输入层限制（如 `maxlength`）通常由 ABP/后端注解生成。
- 本仓库已对 `/Account/ForgotPassword` 做 DOM `maxlength` 取证（见下方证据链）。

证据链（本仓库）：
- `tests/Account/ForgotPassword/test_ForgotPassword_p1_frontend_maxlength_evidence.py`
  - 读取 `input.getAttribute('maxlength')`
  - 写入超长字符串后读取 `page.input_value(...)` 的实际长度
  - Allure 附件：`email_maxlength_evidence`（maxlength_attr/typed_len/actual_len/expected_max）+ 截图

### 4) Personal Settings（/admin/profile → /api/account/my-profile）

#### 4.1 读取 Profile

接口：`GET /api/account/my-profile`  
响应体：`Volo.Abp.Account.ProfileDto`

字段包含：`userName/email/name/surname/phoneNumber/isExternal/hasPassword/concurrencyStamp`

#### 4.2 更新 Profile

接口：`PUT /api/account/my-profile`  
请求体：`Volo.Abp.Account.UpdateProfileDto`

- **userName**
  - maxLength: **256**
  - nullable: true（但业务上通常要求用户必须有 username）
- **email**
  - maxLength: **256**
  - nullable: true（但业务上通常要求用户必须有 email）
- **name**
  - maxLength: **64**
  - nullable: true
- **surname**
  - maxLength: **64**
  - nullable: true
- **phoneNumber**
  - maxLength: **16**
  - nullable: true
- **concurrencyStamp**
  - nullable: true（用于并发控制，建议随 ProfileDto 回传）

#### 4.x 前端输入限制现状（来自前端代码）

来源：`aevatar-agent-station-frontend/src/components/profile/ProfileSettings.tsx`（react-hook-form）
- **userName**
  - required（`required: 'User name is required'`）
  - maxLength: 256（提示：`User name must be less than 256 characters`）
- **email**
  - required
  - pattern：email 正则（提示：`Invalid email address`）
  - maxLength: 256（提示：`Email must be less than 256 characters`）
- **name**：maxLength 64
- **surname**：maxLength 64
- **phoneNumber**：maxLength 16

### 5) Change Password（/admin/profile/change-password → /api/account/my-profile/change-password）

接口：`POST /api/account/my-profile/change-password`  
请求体：`Volo.Abp.Account.ChangePasswordInput`

- **currentPassword**
  - maxLength: **128**
  - nullable: true（但“已有密码用户”通常需要提供；错误会触发 `PasswordMismatch`）
- **newPassword**
  - required
  - maxLength: **128**

密码策略（ABP setting.values）：
- **最小长度**：`Abp.Identity.Password.RequiredLength = 6`
- **唯一字符数**：`Abp.Identity.Password.RequiredUniqueChars = 1`
- **必须包含数字**：`Abp.Identity.Password.RequireDigit = True`
- **必须包含小写**：`Abp.Identity.Password.RequireLowercase = True`
- **必须包含大写**：`Abp.Identity.Password.RequireUppercase = True`
- **必须包含特殊字符**：`Abp.Identity.Password.RequireNonAlphanumeric = True`
- **强制定期改密**：`Abp.Identity.Password.ForceUsersToPeriodicallyChangePassword = False`
- **改密周期（天）**：`Abp.Identity.Password.PasswordChangePeriodDays = 0`

#### 5.x 前端输入限制现状（来自前端代码）

来源：`aevatar-agent-station-frontend/src/components/profile/ChangePassword.tsx`
- 输入层：
  - `currentPassword`：`<Input required ... />`（HTML required）
  - `newPassword` / `confirmNewPassword`：无 maxLength/pattern；主要做“非空 + 两次一致”门禁（不一致会 toast）
- 注意：前端未实现 ABP 密码策略（digit/upper/lower/special 等）逐条校验；应由后端权威校验负责（4xx + 错误体）

### 6) Emailing（/admin/settings → /api/setting-management/emailing）

#### 6.1 读取 Emailing 设置

接口：`GET /api/setting-management/emailing`  
响应体：`Volo.Abp.SettingManagement.EmailSettingsDto`

- `smtpHost`: string?
- `smtpPort`: int32
- `smtpUserName`: string?
- `smtpPassword`: string?
- `smtpDomain`: string?
- `smtpEnableSsl`: boolean
- `smtpUseDefaultCredentials`: boolean
- `defaultFromAddress`: string?
- `defaultFromDisplayName`: string?

#### 6.2 更新 Emailing 设置

接口：`PUT /api/setting-management/emailing`  
请求体：`Volo.Abp.SettingManagement.UpdateEmailSettingsDto`

- **smtpHost**
  - maxLength: **256**
  - nullable: true
- **smtpPort**
  - type: int32
  - min: **1**
  - max: **65535**
- **smtpUserName / smtpPassword / smtpDomain**
  - maxLength: **1024**
  - nullable: true
  - `smtpPassword` format: `password`
- **defaultFromAddress**
  - required
  - minLength: **1**
  - maxLength: **1024**
- **defaultFromDisplayName**
  - required
  - minLength: **1**
  - maxLength: **1024**

#### 6.3 发送测试邮件

接口：`POST /api/setting-management/emailing/send-test-email`  
请求体：`Volo.Abp.SettingManagement.SendTestEmailInput`

- **senderEmailAddress**: required, minLength **1**
- **targetEmailAddress**: required, minLength **1**
- **subject**: required, minLength **1**
- **body**: optional

#### 6.x 前端输入限制现状（来自前端代码）

来源：`aevatar-agent-station-frontend/src/components/settings/Emailing.tsx`
- `defaultFromDisplayName`：required（HTML required）
- `defaultFromAddress`：required + `type="email"`（HTML5 email validity）
- `smtpPort`：required + `type="number"`（未做 min/max 校验）
- 其余字段（smtpHost/smtpDomain/smtpUserName/smtpPassword）：未做 maxLength 校验

### 7) Feature Management（/admin/settings/feature-management → /api/feature-management/features）

#### 7.1 读取 Feature 列表

接口：`GET /api/feature-management/features`

响应体：`Volo.Abp.FeatureManagement.GetFeatureListResultDto`：
- `groups[].features[].name/displayName/description/value`
- `valueType`：`IStringValueType`（决定该 feature 允许的值形态，例如 boolean/number/selection 等）

#### 7.2 更新 Feature

接口：`PUT /api/feature-management/features`  
请求体：`Volo.Abp.FeatureManagement.UpdateFeaturesDto`

- `features[]`：
  - `name`: string
  - `value`: string

备注：
- Swagger 对 `value` 没有限制，但**服务端会按 feature definition 的 `valueType` 进行校验/转换**（例如 boolean feature 只接受 `"true"/"false"`）。

#### 7.x 前端输入限制现状（来自前端代码）

来源：
- `aevatar-agent-station-frontend/src/components/settings/FeatureManagement.tsx`
- `aevatar-agent-station-frontend/src/components/settings/Features.tsx`

当前 UI 只展示弹窗与按钮，无实际 feature value 输入框，因此无字段级 maxLength/pattern 限制可补充。
