---
alwaysApply: true
---

# 📸 Allure 报告增强规范

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

**⚠️ 重要：所有截图必须使用 `full_page=True` 参数，确保截取完整页面**

## Toast/动态消息截图规范

```python
# ✅ 正确：点击按钮后，等待 toast 出现再截图
page_obj.click_save()

# 等待 toast/错误消息出现后再截图（确保截全）
page.wait_for_timeout(500)  # 初始等待响应
toast_selectors = [".toast", ".Toastify__toast", "[role='alert']", ...]
toast_appeared = False
for selector in toast_selectors:
    try:
        page.wait_for_selector(selector, state="visible", timeout=2000)
        page.wait_for_timeout(300)  # toast 出现后等待完全显示
        toast_appeared = True
        break
    except:
        continue
if not toast_appeared:
    page.wait_for_timeout(1000)  # 如果没 toast，至少等待页面稳定

with allure.step("点击保存按钮"):
    page_obj.take_screenshot("step_click_save", full_page=True)
```

## 截图命名规范

- 使用有意义的名称：`step_navigate`, `step_fill_form`, `step_click_save`
- 避免重复：每个测试用例中的截图名称应该唯一
- 使用下划线分隔：`step_verify_error` 而不是 `stepVerifyError`

## ❌ 常见错误

**1. 缺少截图**
```python
# ❌ 错误：只有操作，没有截图
change_password_page.navigate()

# ✅ 正确：使用 allure.step 包装并截图
change_password_page.navigate()
with allure.step("导航到修改密码页面"):
    change_password_page.take_screenshot("step_navigate", full_page=True)
```

**2. 截图不在步骤中**
```python
# ❌ 错误：截图没有包装在 allure.step 中
change_password_page.take_screenshot("step_navigate")

# ✅ 正确：截图必须在 allure.step 中
with allure.step("导航到修改密码页面"):
    change_password_page.take_screenshot("step_navigate", full_page=True)
```

**3. 缺少 allure 导入**
```python
# ❌ 错误：没有导入 allure
import pytest

# ✅ 正确：必须导入 allure
import pytest
import allure
```
