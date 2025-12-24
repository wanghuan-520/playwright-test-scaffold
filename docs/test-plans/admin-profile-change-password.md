# Admin Profile - Change Password（/admin/profile/change-password）

## 页面概述

- **页面路径**：`/admin/profile/change-password`
- **页面目的**：已登录用户修改自己的密码（写操作，高风险且必须可回滚）
- **证据链目录**：`docs/test-plans/artifacts/admin-profile-change-password/`
- **后端规则真理源（ABP）**：输入校验/PasswordPolicy 以后端 ABP 为准（见 `abp_rules_extract.json`）

## 风险点与优先级依据

- **P0 风险**：改密是账户级别写操作，失败会阻断用户继续使用系统；成功路径必须稳定、可重复。
- **P1 风险**：PasswordPolicy/确认密码一致性/错误提示的可观测性；前后端一致性（前端拦截 + 后端也拒绝）。
- **Security 最小集**：鉴权拦截、XSS/SQLi 载荷不执行、不 5xx、不异常跳转。

## 账号与数据来源（必须）

- **Step1 计划允许写明 email**：`hayleetest1@test.com`（用于人工/可读性）
- **Step2 自动化执行必须使用账号池**：默认从 `test-data/test_account_pool.json` 分配账号；**禁止把密码写死到计划/代码/Allure 附件**。
- **回滚策略（强制）**：改密用例必须在用例内或 teardown 把密码恢复到 baseline：
  - 推荐：账号池记录 `initial_password`（或 baseline 密码），用例完成后改回；
  - 或者：使用“交替密码”策略（A→B→A），两组密码均通过账号池/环境变量提供。

## 页面元素映射（Locator 优先级：role/label/testid > aria > 语义 CSS > 结构 CSS）

- **当前密码输入框**：role=`textbox`, name=`Current password`
- **新密码输入框**：role=`textbox`, name=`New password`
- **确认新密码输入框**：role=`textbox`, name=`Confirm new password`
- **保存按钮**：role=`button`, name=`Save`
- **显示/隐藏密码按钮**：role=`button`, name=`Show password`（每个输入框旁各 1 个，需结合父容器或 index 区分）

> 证据：见 `docs/test-plans/artifacts/admin-profile-change-password/visible.txt` 与 `page.png`

## ABP PasswordPolicy（真理源摘要）

证据文件：`docs/test-plans/artifacts/admin-profile-change-password/abp_rules_extract.json`

- **RequiredLength**：6
- **RequiredUniqueChars**：1
- **RequireDigit**：true
- **RequireLowercase**：true
- **RequireUppercase**：true
- **RequireNonAlphanumeric**：true
- **ForceUsersToPeriodicallyChangePassword**：false
- **PasswordChangePeriodDays**：0

> Swagger 未能直接抓取（307/404），本计划以 ABP application-configuration 的 setting.values 为准。

## 前后端代码/契约证据（用于补全用例，避免猜测）

证据文件：`docs/test-plans/artifacts/admin-profile-change-password/code_rules_extract.json`

- **前端（可观测行为）**：
  - `currentPassword` 输入框：HTML5 `required`，可能被浏览器原生校验拦截（不发请求）
  - `newPassword/confirmNewPassword`：前端仅校验“非空且一致”，不做 PasswordPolicy 校验（policy 由后端拒绝）
- **后端契约（swagger）**：
  - `POST /api/account/my-profile/change-password`
  - DTO：`Volo.Abp.Account.ChangePasswordInput`
    - `newPassword` required
    - `currentPassword/newPassword` 最大长度 `maxLength=128`
  - 错误体：`Volo.Abp.Http.RemoteServiceErrorResponse`

## 用例设计

### P0 - 主链路（必须）

#### P0-01 页面可加载（已登录态）

- **前置条件**：
  - 已登录（来自账号池的有效用户）
  - 若环境存在租户选择流程：已完成租户设置（证据：`abp_swagger.json` 307 到 `/auth/set-tenant`）
- **步骤**：
  - 访问 `/admin/profile/change-password`
  - 观察页面显示 `Change Password`，且 3 个密码输入框 + `Save` 按钮可见
- **断言（前端可观测）**：
  - 三个 textbox 均可见且可输入
  - `Save` 按钮可见

#### P0-02 成功修改密码（可回滚、可重复）

- **前置条件**：
  - 账号池提供：`current_password`（baseline）与 `new_password_valid`（满足 policy），两者不同
- **步骤**：
  - 输入 Current password / New password / Confirm new password
  - 点击 `Save`
- **断言（前端可观测）**：
  - 出现成功提示（建议断言“成功 toast/notification 存在”或页面无错误态；避免强绑定具体文案）
  - `Save` 后不会留在“明显错误态”（如字段红框/错误提示）
- **断言（后端权威，建议）**：
  - 重新登录验证（退出后用新密码登录成功；或调用“受保护接口”验证会话有效）
- **回滚（强制）**：
  - 用新密码把密码改回 baseline（或 teardown 兜底）

#### P0-03 必填：Current password 为空

- **步骤**：仅填 New/Confirm，Current 留空，点击 Save
- **断言**：
  - 前端出现可见错误证据（aria-invalid/内联提示/validation message 等）
  - 不发送提交请求（如可拦截网络：提交 API 不应发生）

#### P0-04 必填：New password 为空

- **步骤**：仅填 Current/Confirm，New 留空，点击 Save
- **断言**：同上

#### P0-05 必填：Confirm new password 为空

- **步骤**：仅填 Current/New，Confirm 留空，点击 Save
- **断言**：同上

### P1 - 输入校验矩阵（强制）

> 原则：P1 以“字段矩阵”为主，保证覆盖边界 min-1/min/min+1 以及 policy 分解用例；每条 should_save=False 必须有前端可见错误证据。

#### P1-01 Confirm 不一致（业务规则）

- **数据**：New != Confirm
- **断言**：
  - 前端可见错误（优先断言“确认密码不匹配”的 UI 证据）
  - 后端也应拒绝（若前端未拦截，则需补“后端 4xx + validationErrors”探针）

#### P1-02 Current password 错误（后端错误映射）

- **数据**：Current 填错误值（从账号池生成一条明显不同的字符串），New/Confirm 为合法
- **断言**：
  - 前端展示可诊断错误（可参考 ABP localization：`PasswordMismatch` → “Incorrect password.”）
  - 后端拒绝（4xx）

#### P1-03 PasswordPolicy：长度边界（RequiredLength=6）

- **数据矩阵（New/Confirm 同值）**：
  - len=5（min-1）→ should_save=False（期望拒绝）
  - len=6（min）→ should_save=True（期望通过）
  - len=7（min+1）→ should_save=True（期望通过）
- **断言**：
  - 被拒绝时：前端可见错误证据；若前端放行则后端必须拒绝（4xx）

#### P1-04 PasswordPolicy：缺少 digit（RequireDigit=true）

- **数据**：不含 `0-9`，其余条件满足（含 upper/lower/special 且长度>=6）
- **断言**：
  - 前端错误证据或后端 `PasswordRequiresDigit` 拒绝

#### P1-05 PasswordPolicy：缺少 lowercase（RequireLowercase=true）

- **数据**：不含 `a-z`，其余满足
- **断言**：同上（`PasswordRequiresLower`）

#### P1-06 PasswordPolicy：缺少 uppercase（RequireUppercase=true）

- **数据**：不含 `A-Z`，其余满足
- **断言**：同上（`PasswordRequiresUpper`）

#### P1-07 PasswordPolicy：缺少 non-alphanumeric（RequireNonAlphanumeric=true）

- **数据**：仅字母+数字，不含特殊字符，其余满足
- **断言**：同上（`PasswordRequiresNonAlphanumeric`）

#### P1-08 PasswordPolicy：unique chars（RequiredUniqueChars=1）

- **说明**：该值为 1，基本不会成为拒绝原因；保留 1 条 sanity（例如重复字符很多但至少 1 个 unique）即可。

#### P1-09 交互健壮性：多次点击 Save / 双击

- **步骤**：在合法数据下快速连点 Save
- **断言**：
  - 不出现 5xx
  - 不出现重复 toast/重复请求导致的异常状态（如并发冲突）

#### P1-10 API 异常：超时/500（若可注入或 mock）

- **断言**：
  - 前端提示“可恢复的错误状态”（toast/错误提示）
  - 表单仍可编辑、用户可重试

### Security（建议 P1 + security）

#### S-01 未登录访问拦截

- **步骤**：清理会话后访问 `/admin/profile/change-password`
- **期望**：进入登录流程（或 401/403 + 前端引导）
- **证据**：当前 `curl visible.html` 返回 `/auth/login`，表明未携带会话时会走登录（见 artifacts）

#### S-02 XSS 载荷不执行（字段最小载荷集）

- **数据**：在三个字段分别输入 XSS payload（例如 `<img src=x onerror=alert(1)>`）
- **断言**：
  - 不弹出 dialog
  - 不异常跳转
  - 若触发提交：不应为 5xx

#### S-03 SQLi 风格字符串不导致异常

- **数据**：`' OR 1=1 --` 等
- **断言**：同上（不崩溃、不异常跳转、不 5xx）

## 数据设计（建议 JSON 化，供 Step2 使用）

> 注意：本计划**不写入任何真实密码**；密码数据在 Step2 通过账号池/环境变量注入。

- **valid**：
  - `new_password_valid`：满足 policy（len>=6 + upper + lower + digit + special）
- **invalid（按 policy 分解）**：
  - `too_short_len_5`
  - `missing_digit`
  - `missing_lowercase`
  - `missing_uppercase`
  - `missing_special`
  - `confirm_mismatch`
- **security_payloads**：
  - `xss_min`
  - `sqli_min`

## 自动化实现建议（对齐本仓库）

- Page Object 建议新增：`pages/change_password_page.py`（Step2 生成时做）
- 测试文件建议落位：`tests/admin/profile/`
  - `test_change_password_p0.py`
  - `test_change_password_p1.py`
  - `test_change_password_security.py`
- fixture：
  - 使用账号池分配用户并管理“密码回滚”
  - baseline 进入用例前必须“正常化”（避免超长字符串污染 P0 截图/回滚）


