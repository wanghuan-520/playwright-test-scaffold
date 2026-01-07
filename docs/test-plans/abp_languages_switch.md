# Abp Languages Switch UI 自动化测试计划

## 0. 生成信息（用于可追溯）
- **URL**: `https://localhost:3000/Abp/Languages/Switch`
- **slug**: `abp_languages_switch`
- **生成时间**: 2025-12-24 19:54:44
- **是否需要登录态**: 否
- **证据链目录**: `docs/test-plans/artifacts/abp_languages_switch/`

## 1. 页面概述
- **页面类型**: FORM
- **主要功能（用户任务流）**:
  - 进入页面
  - 完成主要交互
  - 验证可观察结果（UI 状态/业务结果）
- **风险点**:
  - 鉴权/权限：未登录或权限不足时的跳转与提示必须正确
- **测试优先级**: 高（涉及权限/敏感操作/不可逆风险的页面默认 P0 覆盖）

## 2. 页面元素映射
### 2.1 关键元素识别
| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |
|---------|----------|----------|----------|--------|----------|----------|
| button | - | 按钮操作 | css | `page.locator("button[aria-label='Open Next.js Dev Tools']")` | 可点击 / loading/禁用态 / 触发结果（toast/错误提示/跳转） | 无 |

### 2.2 页面对象设计（骨架）
```python
from core.base_page import BasePage

# ============================================================
# 页面对象：AbpLanguagesSwitchPage
# - 目标：封装稳定定位器与业务操作
# - 原则：短小、直白、少分支
# ============================================================
class AbpLanguagesSwitchPage(BasePage):
    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）
    # CURRENT_PASSWORD_INPUT = ...
    # NEW_PASSWORD_INPUT = ...
    # CONFIRM_PASSWORD_INPUT = ...
    # SUBMIT_BUTTON = ...

    def navigate(self) -> None:
        self.goto("https://localhost:3000/Abp/Languages/Switch")

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
- **TC001**: 页面加载
  - **标签**: [@smoke @p0]
  - **前置条件**: 已登录（若需要）
  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见
  - **预期结果**: 页面可用且无阻塞错误
  - **断言层级**: UI 状态
  - **优先级**: 高

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
- 建议 PageObject：`pages/abp_languages_switch_page.py`（类名 `AbpLanguagesSwitchPage`，继承 `core/base_page.py:BasePage`）
- 把“业务动作”封装成方法（不要在测试里散落 click/fill）
- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）

### 5.2 测试类实现
- 建议测试目录：`tests/abp/abp_languages_switch/` 或对齐现有 suite 目录
- 用 pytest 标记分层（@smoke/@p0/@p1/@security）
- 数据驱动（valid/invalid/boundary）减少重复代码

### 5.3 配置建议
- 若需要：在 `config/project.yaml` 补充 base_url/账号策略
- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检

## 6. 执行计划
- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例
- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）
- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）
