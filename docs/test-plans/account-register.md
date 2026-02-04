# Account Register UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `http://localhost:5173/account/register`
- **slug**: `account_register`
- **生成时间**: 2026-01-16 10:00:00
- **是否需要登录态**: 否
- **证据链目录**: `docs/test-plans/artifacts/account_register/`

## 1. 页面概述
- **页面类型**: REGISTER
- **主要功能（用户任务流）**:
  - 进入注册页面并确认关键表单可见
  - 填写必填字段（Full Name / Email / Password / Confirm Password）
  - 同意服务条款
  - 提交注册并观察成功/失败反馈（toast/表单错误/跳转）
- **风险点**:
  - 数据一致性：注册时全名处理逻辑（First Name / Last Name 拆分）
  - 安全性：密码策略验证、防账号枚举、错误提示不泄露敏感信息
  - 稳定性：定位器漂移/异步加载导致 flaky
- **测试优先级**: 高（涉及用户注册流程，影响系统可用性）

## 2. 页面元素映射
### 2.1 关键元素识别

| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |
|---------|----------|----------|----------|--------|----------|----------|
| input | Full Name | 全名输入 | role/name | `page.get_by_role("textbox", name="Full Name")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） | 无 |
| input | Email | 邮箱输入 | role/name | `page.get_by_role("textbox", name="Email")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） | 无 |
| input | Password | 密码输入 | role/name | `page.get_by_role("textbox", name="Password")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） / mask 显示/不回显明文 | 无 |
| input | Confirm Password | 确认密码输入 | role/name | `page.get_by_role("textbox", name="Confirm Password")` | 可输入 / 可清空 / 校验提示（必填/格式/长度） / mask 显示/不回显明文 | 无 |
| checkbox | I agree to the terms | 同意条款 | role/name | `page.get_by_role("checkbox", name="I agree to the terms")` | 可勾选 / 必选校验 | 无 |
| button | Register | 提交/保存 | role/name | `page.get_by_role("button", name="Register")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| link | Login | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Login")` | 可见 / 可交互 / 行为正确 | 无 |

### 2.2 页面对象设计（骨架）
```python
from core.base_page import BasePage

# ============================================================
# 页面对象：AccountRegisterPage
# - 目标：封装稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class AccountRegisterPage(BasePage):
    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）
    # FULL_NAME_INPUT = page.get_by_role("textbox", name="Full Name")
    # EMAIL_INPUT = page.get_by_role("textbox", name="Email")
    # PASSWORD_INPUT = page.get_by_role("textbox", name="Password")
    # CONFIRM_PASSWORD_INPUT = page.get_by_role("textbox", name="Confirm Password")
    # AGREE_TERMS_CHECKBOX = page.get_by_role("checkbox", name="I agree to the terms")
    # REGISTER_BUTTON = page.get_by_role("button", name="Register")
    # LOGIN_LINK = page.get_by_role("link", name="Login")

    def navigate(self) -> None:
        self.goto("http://localhost:5173/account/register")

    def is_loaded(self) -> bool:
        # 以关键元素作为"已加载"判定
        return self.page.get_by_role("button", name="Register").is_visible()

    # --------------------------------------------------------
    # 业务动作（示例）
    # --------------------------------------------------------
    def submit_register(self, full_name: str, email: str, password: str, confirm_password: str, agree_terms: bool = True) -> None:
        # TODO: 填写并提交；失败时保留截图与上下文（证据链）
        self.fill(self.FULL_NAME_INPUT, full_name)
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.fill(self.CONFIRM_PASSWORD_INPUT, confirm_password)
        if agree_terms:
            self.check(self.AGREE_TERMS_CHECKBOX)
        self.click(self.REGISTER_BUTTON)
```

## 3. 测试用例设计
### 3.1 功能测试用例
- **账号建议**:
  - **普通账号 email（示例）**: `testuser@example.com`（用于注册测试）
  - **密码**: 运行期由环境变量/账号池提供；计划与任何落盘文件禁止写入密码

- **TC001**: 页面加载
  - **标签**: [@smoke @p0]
  - **前置条件**: 无
  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见
  - **预期结果**: 页面可用且无阻塞错误
  - **断言层级**: UI 状态
  - **优先级**: 高

- **TC002**: 注册页字段可输入 + 提交按钮可用性
  - **标签**: [@p0]
  - **测试步骤**: 填写必填项（以页面可见标识为准）→ 提交
  - **预期结果**: 成功注册或得到可诊断的校验提示（不出现 5xx）
  - **优先级**: 高

- **TC003**: Email 格式校验
  - **标签**: [@p1 @validation]
  - **测试步骤**: 输入非法 email（如缺少 @）→ 提交
  - **预期结果**: 前端或后端拒绝并展示错误证据（字段 invalid/提示/4xx）
  - **优先级**: 中

- **TC004**: 密码策略矩阵（以后端 ABP 为真理源）
  - **标签**: [@p1 @validation]
  - **测试步骤**: 使用不满足策略的密码（缺数字/缺大写/太短等）→ 提交
  - **预期结果**: 被拒绝；提示可观测；不落盘任何密码样例
  - **优先级**: 中

- **TC005**: 确认密码不匹配
  - **标签**: [@p0 @validation]
  - **测试步骤**: 填写密码和确认密码不一致 → 提交
  - **预期结果**: 显示错误提示 "New passwords do not match" 或类似；阻止提交
  - **优先级**: 高

- **TC006**: 重复注册验证
  - **标签**: [@p0 @negative]
  - **测试步骤**: 使用已存在的邮箱注册 → 提交
  - **预期结果**: 显示错误提示（用户名和邮箱已存在）；不创建新账号
  - **优先级**: 高

- **TC007**: 同意条款必选
  - **标签**: [@p0 @validation]
  - **测试步骤**: 填写所有字段但不勾选同意条款 → 提交
  - **预期结果**: 显示必选提示；阻止提交
  - **优先级**: 高

- **TC-SEC-001**: 注册失败不泄露敏感信息（错误体/提示不包含密码明文）
  - **标签**: [@p1 @security]
  - **优先级**: 中

### 3.2 边界测试用例
- **TC-BOUNDARY-001**: Full Name 边界值测试
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 测试最小长度、最大长度、特殊字符
  - **预期结果**: 正确处理边界值；显示相应提示

- **TC-BOUNDARY-002**: Email 边界值测试
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 测试超长邮箱、特殊字符邮箱
  - **预期结果**: 正确处理边界值

- **TC-BOUNDARY-003**: 密码长度边界测试
  - **标签**: [@p1 @boundary]
  - **测试步骤**: 测试最小长度-1、最小长度、最大长度、最大长度+1
  - **预期结果**: 最小长度-1 被拒绝；最小长度和最大长度接受；最大长度+1 被拒绝

### 3.3 异常测试用例
- **TC-EXCEPTION-001**: 网络异常处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟网络中断后提交
  - **预期结果**: 显示网络错误提示；允许重试

- **TC-EXCEPTION-002**: 服务器错误处理
  - **标签**: [@p2 @exception]
  - **测试步骤**: 模拟 5xx 错误
  - **预期结果**: 显示友好错误提示；不暴露服务器内部信息

## 4. 测试数据设计（JSON）
```json
{
  "valid": [
    {
      "fullName": "Test User",
      "email": "testuser@example.com",
      "passwordEnv": "TEST_PASSWORD_VALID",
      "confirmPasswordEnv": "TEST_PASSWORD_VALID",
      "agreeTerms": true
    }
  ],
  "invalid": [
    {
      "case": "missing_full_name",
      "fullName": "",
      "email": "test@example.com",
      "passwordEnv": "TEST_PASSWORD_VALID",
      "confirmPasswordEnv": "TEST_PASSWORD_VALID",
      "agreeTerms": true
    },
    {
      "case": "invalid_email",
      "fullName": "Test User",
      "email": "invalid-email",
      "passwordEnv": "TEST_PASSWORD_VALID",
      "confirmPasswordEnv": "TEST_PASSWORD_VALID",
      "agreeTerms": true
    },
    {
      "case": "password_mismatch",
      "fullName": "Test User",
      "email": "test@example.com",
      "passwordEnv": "TEST_PASSWORD_VALID",
      "confirmPasswordLiteral": "__DIFFERENT_FROM_PASSWORD__",
      "agreeTerms": true
    },
    {
      "case": "weak_password",
      "fullName": "Test User",
      "email": "test@example.com",
      "passwordLiteral": "weak",
      "confirmPasswordLiteral": "weak",
      "agreeTerms": true
    },
    {
      "case": "duplicate_email",
      "fullName": "Test User",
      "email": "existing@example.com",
      "passwordEnv": "TEST_PASSWORD_VALID",
      "confirmPasswordEnv": "TEST_PASSWORD_VALID",
      "agreeTerms": true
    }
  ],
  "boundary": [
    {
      "case": "password_min_minus_1",
      "fullName": "Test User",
      "email": "test@example.com",
      "passwordLiteral": "__TBD_BY_ABP_POLICY_MIN_MINUS_1__",
      "confirmPasswordLiteral": "__TBD_BY_ABP_POLICY_MIN_MINUS_1__",
      "agreeTerms": true
    },
    {
      "case": "password_max_plus_1",
      "fullName": "Test User",
      "email": "test@example.com",
      "passwordLiteral": "__TBD_BY_ABP_POLICY_MAX_PLUS_1__",
      "confirmPasswordLiteral": "__TBD_BY_ABP_POLICY_MAX_PLUS_1__",
      "agreeTerms": true
    }
  ]
}
```

## 5. 自动化实现建议（对齐本仓库）
### 5.1 页面类实现
- 建议 PageObject：`pages/account_register_page.py`（类名 `AccountRegisterPage`，继承 `core/base_page.py:BasePage`）
- 把"业务动作"封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/account/register/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）

