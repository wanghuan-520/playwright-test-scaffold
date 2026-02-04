# Account Login UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `http://localhost:5173/account/login`
- **slug**: `account_login`
- **生成时间**: 2026-01-16 10:00:00
- **是否需要登录态**: 否
- **证据链目录**: `docs/test-plans/artifacts/account_login/`

## 1. 页面概述
- **页面类型**: LOGIN
- **主要功能（用户任务流）**:
  - 进入登录页面并确认关键表单可见
  - 输入用户名/邮箱 + 密码
  - 点击登录按钮
  - 等待跳转或错误提示
- **风险点**:
  - 鉴权/权限：未登录或权限不足时的跳转与提示必须正确
  - 安全性：防账号枚举（错误提示不区分"用户不存在/密码错误"）
  - 稳定性：定位器漂移/异步加载导致 flaky
- **测试优先级**: 高（涉及身份认证，影响系统安全性）

## 2. 页面元素映射
### 2.1 关键元素识别

| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |
|---------|----------|----------|----------|--------|----------|----------|
| input | Username or Email | 用户名或邮箱输入 | role/name | `page.get_by_role("textbox", name="Username or Email")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） | 无 |
| input | Password | 密码输入 | role/name | `page.get_by_role("textbox", name="Password")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） / mask 显示/不回显明文 | 无 |
| button | Login | 提交/保存 | role/name | `page.get_by_role("button", name="Login")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| link | Register | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Register")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Forgot Password | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Forgot Password")` | 可见 / 可交互 / 行为正确 | 无 |

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
    # USERNAME_INPUT = page.get_by_role("textbox", name="Username or Email")
    # PASSWORD_INPUT = page.get_by_role("textbox", name="Password")
    # LOGIN_BUTTON = page.get_by_role("button", name="Login")
    # REGISTER_LINK = page.get_by_role("link", name="Register")
    # FORGOT_PASSWORD_LINK = page.get_by_role("link", name="Forgot Password")

    def navigate(self) -> None:
        self.goto("http://localhost:5173/account/login")

    def is_loaded(self) -> bool:
        # 以关键元素作为"已加载"判定
        return self.page.get_by_role("button", name="Login").is_visible()

    # --------------------------------------------------------
    # 业务动作（示例）
    # --------------------------------------------------------
    def submit_login(self, username: str, password: str) -> None:
        # TODO: 填写并提交；失败时保留截图与上下文（证据链）
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
```

## 3. 测试用例设计
### 3.1 功能测试用例
- **账号建议**:
  - **普通账号 email（示例）**: `testuser@example.com`（用于登录测试）
  - **管理员账号 email（示例）**: `admin@example.com`（用于管理员功能测试）
  - **密码**: 运行期由环境变量/账号池提供；计划与任何落盘文件禁止写入密码

- **TC001**: 页面加载
  - **标签**: [@smoke @p0]
  - **前置条件**: 无
  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见
  - **预期结果**: 页面可用且无阻塞错误
  - **断言层级**: UI 状态
  - **优先级**: 高

- **TC002**: 登录成功（有效凭证）
  - **标签**: [@p0 @auth]
  - **前置条件**: 有效账号（通过账号池/环境变量注入）
  - **测试步骤**: 输入用户名/邮箱 + 密码 → 点击 Login → 等待跳转
  - **预期结果**: 登录成功并回跳到前端域（`http://localhost:5173/app`）或进入授权后的目标页
  - **断言层级**: UI 状态 + URL/可观测用户菜单
  - **优先级**: 高

- **TC003**: 登录失败（错误密码）
  - **标签**: [@p0 @negative]
  - **测试步骤**: 输入正确用户名 + 错误密码 → Login
  - **预期结果**: 显示错误提示；不会建立前端登录态
  - **断言层级**: UI 可观测错误 + 仍停留登录页
  - **优先级**: 高

- **TC004**: 登录失败（不存在的用户名）
  - **标签**: [@p0 @negative]
  - **测试步骤**: 输入不存在的用户名 + 任意密码 → Login
  - **预期结果**: 显示错误提示（与错误密码提示风格一致，不泄露账号存在性）；不会建立登录态
  - **断言层级**: UI 可观测错误 + 仍停留登录页
  - **优先级**: 高

- **TC005**: 必填校验（用户名/密码为空）
  - **标签**: [@p1 @validation]
  - **测试步骤**: 清空用户名或密码 → Login
  - **预期结果**: 表单显示必填提示或阻止提交
  - **优先级**: 中

- **TC006**: Email 格式校验（如果支持邮箱登录）
  - **标签**: [@p1 @validation]
  - **测试步骤**: 输入非法 email 格式 → Login
  - **预期结果**: 显示格式错误提示或阻止提交
  - **优先级**: 中

- **TC-SEC-001**: 防账号枚举（错误提示不区分"用户不存在/密码错误"）
  - **标签**: [@p1 @security]
  - **测试步骤**: 分别用不存在账号/存在账号错误密码尝试登录
  - **预期结果**: 错误提示保持同一风格，不泄露账号存在性
  - **优先级**: 中

- **TC-SEC-002**: 密码不回显明文
  - **标签**: [@p1 @security]
  - **测试步骤**: 输入密码 → 检查输入框类型
  - **预期结果**: 密码输入框为 password 类型；截图/日志不出现明文
  - **优先级**: 中

### 3.2 边界测试用例
- **TC-BOUNDARY-001**: 超长用户名/邮箱测试
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 输入超长用户名/邮箱（如 500 字符）
  - **预期结果**: 正确处理；显示长度限制提示或截断

- **TC-BOUNDARY-002**: 特殊字符用户名测试
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 输入包含特殊字符的用户名（如 `<script>`, `' OR 1=1`）
  - **预期结果**: 正确处理；不执行脚本；不出现 SQL 注入

### 3.3 异常测试用例
- **TC-EXCEPTION-001**: 网络异常处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟网络中断后提交
  - **预期结果**: 显示网络错误提示；允许重试

- **TC-EXCEPTION-002**: 服务器错误处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟 5xx 错误
  - **预期结果**: 显示友好错误提示；不暴露服务器内部信息

- **TC-EXCEPTION-003**: 会话超时处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 登录后等待会话超时 → 尝试操作
  - **预期结果**: 提示重新登录；跳转到登录页

## 4. 测试数据设计（JSON）
```json
{
  "valid": [
    {
      "username": "testuser@example.com",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    },
    {
      "username": "admin@example.com",
      "passwordEnv": "TEST_ADMIN_PASSWORD"
    }
  ],
  "invalid": [
    {
      "case": "wrong_password",
      "username": "testuser@example.com",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD_WRONG"
    },
    {
      "case": "non_existent_user",
      "username": "nonexistent@example.com",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    },
    {
      "case": "empty_username",
      "username": "",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    },
    {
      "case": "empty_password",
      "username": "testuser@example.com",
      "password": ""
    },
    {
      "case": "invalid_email_format",
      "username": "invalid-email",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    }
  ],
  "boundary": [
    {
      "case": "very_long_username",
      "username": "__500_CHARS_STRING__",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    },
    {
      "case": "special_chars_username",
      "username": "<script>alert('xss')</script>",
      "passwordEnv": "TEST_ACCOUNT_PASSWORD"
    }
  ]
}
```

## 5. 自动化实现建议（对齐本仓库）
### 5.1 页面类实现
- 建议 PageObject：`pages/account_login_page.py`（类名 `AccountLoginPage`，继承 `core/base_page.py:BasePage`）
- 把"业务动作"封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/account/login/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检
- 登录态复用：使用 `REUSE_LOGIN=1` 启用 storage_state 复用，减少登录频率

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）

