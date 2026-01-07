# Workflow UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `https://localhost:3000/workflow`
- **slug**: `workflow`
- **生成时间**: 2025-12-24 23:34:24
- **是否需要登录态**: 否
- **证据链目录**: `docs/test-plans/artifacts/workflow/`

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
| button | Toggle navigation menu | 按钮操作 | role/name | `page.get_by_role("button", name="Toggle navigation menu")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | Sign In | 按钮操作 | role/name | `page.get_by_role("button", name="Sign In")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | Get Started | 按钮操作 | role/name | `page.get_by_role("button", name="Get Started")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | Import Workflow | 按钮操作 | role/name | `page.get_by_role("button", name="Import Workflow")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | New Workflow | 按钮操作 | role/name | `page.get_by_role("button", name="New Workflow")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | - | 按钮操作 | css | `page.locator("button[type='button']")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | - | 按钮操作 | css | `page.locator("button[aria-label='Open Next.js Dev Tools']")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | 12 Issues | 按钮操作 | role/name | `page.get_by_role("button", name="12 Issues")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| button | - | 按钮操作 | css | `page.locator("button[aria-label='Collapse issues badge']")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |
| link | Aevatar AI | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Aevatar AI")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Workflow | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Workflow")` | 可见 / 可交互 / 行为正确 | 无 |
| link | GitHub | 导航/跳转 | role/linkText | `page.get_by_role("link", name="GitHub")` | 可见 / 可交互 / 行为正确 | 无 |
| link | Get Started | 导航/跳转 | role/linkText | `page.get_by_role("link", name="Get Started")` | 可见 / 可交互 / 行为正确 | 无 |

### 2.2 页面对象设计（骨架）
```python
from core.base_page import BasePage

# ============================================================
# 页面对象：WorkflowPage
# - 目标：封装稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class WorkflowPage(BasePage):
    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）
    # CURRENT_PASSWORD_INPUT = ...
    # NEW_PASSWORD_INPUT = ...
    # CONFIRM_PASSWORD_INPUT = ...
    # SUBMIT_BUTTON = ...

    def navigate(self) -> None:
        self.goto("https://localhost:3000/workflow")

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

- **TC002**: New Workflow 按钮可用
  - **标签**: [@p0]
  - **测试步骤**: 打开页面 → 点击 New Workflow（若存在）
  - **预期结果**: 弹窗/跳转可观测；可关闭/可回退
  - **优先级**: 高

- **TC003**: Import Workflow 基础校验
  - **标签**: [@p1]
  - **测试步骤**: 点击 Import Workflow → 不选择文件直接提交（或取消）
  - **预期结果**: 不崩溃；提示可观测
  - **优先级**: 中

- **TC-SEC-001**: 未登录可访问性（若页面支持匿名）/或强制登录拦截（以实际为准）
  - **标签**: [@p1 @auth]
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
- 建议 PageObject：`pages/workflow_page.py`（类名 `WorkflowPage`，继承 `core/base_page.py:BasePage`）
- 把“业务动作”封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/workflow/workflow/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）
