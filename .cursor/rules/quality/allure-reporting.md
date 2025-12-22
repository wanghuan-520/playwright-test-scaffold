---
alwaysApply: true
---

# 📸 Allure 报告增强规范

> 这是一个“完整可复制”的 tmp 版本：用于手动覆盖 `.cursor/rules/quality/allure-reporting.md`。

## 必须使用 Allure 功能

1. **@allure.feature()** - 功能模块
2. **@allure.story()** - 功能故事
3. **@allure.title()** - 测试用例标题（只写方法名）
4. **@allure.description()** - 测试描述（目的、前置条件、步骤）
5. **allure.step()** - 关键步骤（必须包含截图）
6. **take_screenshot()** - 截图功能（自动附加到 Allure）

## 截图要求

**所有关键步骤必须添加截图：**
- ✅ 页面导航后
- ✅ 填写表单后
- ✅ 点击按钮后
- ✅ 验证操作后
- ✅ 错误验证后
- ✅ 成功验证后

**截图范围策略（强制）**

- 默认：**视口截图**（更快，通常足够覆盖输入区 + toast 区）
- 需要全页审计/复杂布局时：使用环境变量开启全页截图：`FULL_PAGE_SHOT=1`

> 原则：证据可检证优先，但不要为“全页”牺牲 4 worker 并发稳定性。


---

## Toast/动态消息截图规范（强制）

Toast 是 UI 副作用，**网络响应 OK ≠ toast 已渲染**。因此必须：

1) **成功步骤截图**：必须等成功提示出现后再截图（避免截图没抓到 Success）。  
2) **步骤间清理**：进入下一步前必须等待上一条 toast 消失（避免“错误 toast + 成功 toast 同框污染”）。  
3) **可读性兜底**：当提示挤在输入框附近、全页截图看不清时，除 full-page 外，再补一张“输入框局部截图”（高亮边框/元素截图）。

推荐模式（示意）：

```python
# 1) 触发保存并等待网络响应（更可靠）
resp = page_obj.save_and_wait_profile_update()
assert resp.ok

# 2) 再等待成功提示出现（避免截图漏 toast）
page_obj.wait_for_save_success()
page_obj.take_screenshot("step_after_save_success", full_page=True)

# 3) 下一步前清理 toast（避免同框）
page_obj.wait_for_toasts_to_disappear()
```

---

## 截图命名规范

- 使用有意义的名称：`step_navigate`, `step_fill_form`, `step_click_save`
- 避免重复：每个测试用例中的截图名称应该唯一
- 使用下划线分隔：`step_verify_error` 而不是 `stepVerifyError`

---



## 🔇 报告降噪（强制，老兵口味）

目标：Allure 只展示“前端可检证证据”，不要被基础设施过程淹没。

### 1) 不展示的内容（默认）

- baseline 修正过程
- teardown 回滚过程
- 纯断言步骤（assert-only steps）
- 后端接口/回滚诊断的长文本

### 2) 通过开关按需打开（默认关闭）

- `ALLURE_SHOW_BACKEND=1`：展示后端/回滚诊断附件（默认不展示）
- `ALLURE_SHOW_META=1`：展示规则来源/规则快照等元信息（默认不展示）
- `ALLURE_SHOW_DEBUG=1`：展示 debug 截图/提示（例如 baseline/teardown 截图）

> 实现建议：区分 `step_shot()`（证据截图，默认展示）与 `debug_shot()`（debug 截图，仅在 ALLURE_SHOW_DEBUG=1 展示）。

### 3) Description 必须写清测试点

每条 case 必须有 `@allure.description()`：用 5~10 行把“测试点/证据/回滚策略”说明白。

## ✅ Allure 闭环质量门槛（强制）

> 目标：Allure 报告不仅“好看”，更要“可诊断”。失败必须带证据，否则等同于没报错。

### 1) 报告卫生（必须）

- 每次运行前默认必须清理旧的：`allure-results/`、`allure-report/`、`screenshots/`
- 仅当需要趋势图时允许保留 `allure-results/history/`（通过 `KEEP_ALLURE_HISTORY=1`）

### 2) 失败附件标准（必须）

任意失败用例，在 Allure 中必须至少看到：

- **failure_screenshot**（PNG）
- **console**（TEXT）
- **requestfailed**（TEXT）
- **playwright_trace**（ZIP，适用于 `auth_page` 路径）

缺失任意一项，视为“不可诊断失败”，必须先补采集链路，再讨论业务断言。

### 3) Suites 层级（必须）

- 生成的测试用例默认使用**函数式**（不生成 `class Test*`）
- 目标：Allure Suites 目录结构压扁，避免出现冗余第三层 class 维度