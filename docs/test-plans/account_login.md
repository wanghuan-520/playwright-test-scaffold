# Account Login UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `https://localhost:44320/Account/Login`
- **slug**: `account_login`
- **生成时间**: 2025-12-24 23:34:27
- **是否需要登录态**: 否
- **证据链目录**: `docs/test-plans/artifacts/account_login/`

## 1. 页面概述
- **页面类型**: LOGIN
- **主要功能（用户任务流）**:
  - 进入页面
  - 完成主要交互
  - 验证可观察结果（UI 状态/业务结果）
- **风险点**:
  - 稳定性：定位器漂移/异步加载导致 flaky
- **测试优先级**: 高（涉及权限/敏感操作/不可逆风险的页面默认 P0 覆盖）

## 2. 页面元素映射
### 2.1 关键元素识别
| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |
|---------|----------|----------|----------|--------|----------|----------|
| input | LoginInput.UserNameOrEmailAddress | 表单字段/交互 | css | `page.locator("#LoginInput_UserNameOrEmailAddress")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） | 无 |
| input | LoginInput.Password | 密码输入 | css | `page.locator("#LoginInput_Password")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） / mask 显示/不回显明文 | 无 |
| button | English | 按钮操作 | role/name | `page.get_by_role("button", name="English")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | PasswordVisibilityButton | 按钮操作 | css | `page.locator("#PasswordVisibilityButton")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | Login | 按钮操作 | role/name | `page.get_by_role("button", name="Login")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| link | العربية / AR | 导航/跳转 | role/linkText | `page.get_by_role("link", name="العربية / AR")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Čeština / CS | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Čeština / CS")` | 可见 / 可交互 / 行为正确 | 无 |
| link | English / EN | 导航/跳转 | role/linkText | `page.get_by_role("link", name="English / EN")` | 可见 / 可交互 / 行为正确 | 无 |
| link | English (UK) / EN-GB | 导航/跳转 | role/linkText | `page.get_by_role("link", name="English (UK) / EN-GB")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Magyar / HU | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Magyar / HU")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Finnish / FI | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Finnish / FI")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Français / FR | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Français / FR")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Hindi / HI | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Hindi / HI")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Italiano / IT | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Italiano / IT")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Português / PT | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Português / PT")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Русский / RU | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Русский / RU")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Slovak / SK | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Slovak / SK")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Türkçe / TR | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Türkçe / TR")` | 可见 / 可交互 / 行为正确 | 无 |
| link | 简体中文 / ZH | 导航/跳转 | role/linkText | `page.get_by_role("link", name="简体中文 / ZH")` | 可见 / 可交互 / 行为正确 | 无 |
| link | 繁體中文 / ZH-HANT | 导航/跳转 | role/linkText | `page.get_by_role("link", name="繁體中文 / ZH-HANT")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Deutsch / DE | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Deutsch / DE")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Español / ES | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Español / ES")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Svenska / SV | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Svenska / SV")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Register | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Register")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Forgot password? | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Forgot password?")` | 可见 / 可交互 / 行为正确 | 无 |

### 2.2 页面对象设计（骨架）
```python
from core.base_page import BasePage

# ============================================================
# 页面对象：AccountLoginPage
# - 目标：封装稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class AccountLoginPage(BasePage):
    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）
    # CURRENT_PASSWORD_INPUT = ...
    # NEW_PASSWORD_INPUT = ...
    # CONFIRM_PASSWORD_INPUT = ...
    # SUBMIT_BUTTON = ...

    def navigate(self) -> None:
        self.goto("https://localhost:44320/Account/Login")

    def is_loaded(self) -> bool:
        # 以关键元素作为“已加载”判定
        return True

    # --------------------------------------------------------
    # 业务动作（示例）
    # --------------------------------------------------------
    def submit_change_password(self, current_pwd: str, new_pwd: str, confirm_pwd: str) -> None:
        # TODO: 填写并提交；失败时保留截图与上下文（证据链）
        pass
```

## 3. 测试用例设计
### 3.1 功能测试用例
- **账号建议**:
  - **普通账号 email（示例）**: `hayleetest1@test.com`（用于个人设置/Workflow 等）
  - **管理员账号 email（示例）**: `admin-test01@test.com`（用于 Users/Roles/Settings 等管理页）
  - **密码**: 运行期由环境变量/账号池提供；计划与任何落盘文件禁止写入密码

- **TC001**: 页面加载
  - **标签**: [@smoke @p0]
  - **前置条件**: 已登录（若需要）
  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见
  - **预期结果**: 页面可用且无阻塞错误
  - **断言层级**: UI 状态
  - **优先级**: 高

- **TC002**: 登录成功（有效凭证）
  - **标签**: [@p0 @auth]
  - **前置条件**: 有效账号（通过账号池/环境变量注入）
  - **测试步骤**: 输入用户名/邮箱 + 密码 → 点击 Login → 等待跳转
  - **预期结果**: 登录成功并回跳到前端域（`https://localhost:3000`）或进入授权后的目标页
  - **断言层级**: UI 状态 + URL/可观测用户菜单
  - **优先级**: 高

- **TC003**: 登录失败（错误密码）
  - **标签**: [@p0 @negative]
  - **测试步骤**: 输入正确用户名 + 错误密码 → Login
  - **预期结果**: 显示错误提示；不会建立前端登录态
  - **断言层级**: UI 可观测错误 + 仍停留登录页
  - **优先级**: 高

- **TC004**: 必填校验（用户名/密码为空）
  - **标签**: [@p1 @validation]
  - **测试步骤**: 清空用户名或密码 → Login
  - **预期结果**: 表单显示必填提示或阻止提交
  - **优先级**: 中

- **TC-SEC-001**: 防账号枚举（错误提示不区分“用户不存在/密码错误”）
  - **标签**: [@p1 @security]
  - **测试步骤**: 分别用不存在账号/存在账号错误密码尝试登录
  - **预期结果**: 错误提示保持同一风格，不泄露账号存在性
  - **优先级**: 中

### 3.2 边界测试用例

### 3.3 异常测试用例

## 4. 测试数据设计（JSON）
```json
{
  "valid": [
    {
      "field1": "value1",
      "field2": "value2"
    }
  ],
  "invalid": [
    {
      "field1": "",
      "field2": "invalid"
    }
  ],
  "boundary": [
    {
      "field1": "min",
      "field2": "max"
    }
  ]
}
```

## 5. 自动化实现建议（对齐本仓库）
### 5.1 页面类实现
- 建议 PageObject：`pages/account_login_page.py`（类名 `AccountLoginPage`，继承 `core/base_page.py:BasePage`）
- 把“业务动作”封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/account/account_login/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）
