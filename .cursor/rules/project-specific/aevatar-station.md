---
alwaysApply: true
---

# 项目特定规则 - Aevatar Agent Station

## 📋 项目框架性质

### 项目名称
**Aevatar Agent Station** - AI 驱动的智能代理管理平台

### 技术栈架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Aevatar Agent Station                     │
├─────────────────────────────────────────────────────────────┤
│  前端层                                                      │
│  • Next.js / React                                          │
│  • TypeScript                                               │
│  • 路径: aevatar-agent-station-frontend                     │
├─────────────────────────────────────────────────────────────┤
│  后端层                                                      │
│  • ABP Framework (ASP.NET Core Identity)                    │
│  • .NET Aspire (Aevatar.BusinessServer)                     │
│  • 路径: aevatar-agent-framework                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心原则（Critical）⚠️

**前端输入框的校验规则必须严格参照后端 ABP 框架限制进行测试。**

```
前端校验 ≤ 后端 ABP 限制（后端是权威来源）
```

### 测试策略

1. ✅ **后端 ABP 限制是权威** - 前端显示的错误必须与后端 ABP 规则一致
2. ✅ **前端校验可以更宽松** - 但后端必须拦截所有不合规数据
3. ✅ **测试用例必须覆盖所有 ABP 规则** - 即使前端未显示某些限制
4. ✅ **当需求不明确时** - 以后端 ABP 框架限制为准生成测试用例

---

## 📝 测试用例补充指南

### 输入框验证优先级

当生成**任何输入框**的测试用例时，按照以下优先级确定校验规则：

```
1. 需求文档明确说明 → 按需求生成测试
2. 前端代码有验证逻辑 → 参考前端逻辑
3. 后端 ABP 框架有限制 → **以后端为准**（权威）⭐
4. 都没有明确限制 → 生成基础测试（必填、最大长度）
```

### ABP 常见验证规则参考

当分析到后端使用 ABP 框架时，常见的验证规则包括：

| 输入类型 | ABP 验证方向 | 测试重点 |
|---------|-------------|---------|
| **密码** | `RequiredLength`, `RequireDigit`, `RequireLowercase`, `RequireUppercase`, `RequireNonAlphanumeric` | 长度、大小写、数字、特殊字符 |
| **用户名** | `MaxLength`, `MinLength`, 特殊字符限制 | 边界值、允许的字符集 |
| **邮箱** | `Email` 格式验证 | 格式正确性、唯一性 |
| **电话号码** | `PhoneNumber` 格式验证 | 格式、长度 |
| **字符串字段** | `MaxLength`, `MinLength` | 边界值测试 |
| **数值字段** | `Range` 验证 | 最小值、最大值、边界值 |
| **必填字段** | `Required` 验证 | 空值、空白字符 |

### 测试用例生成策略

#### P0 - 核心功能（必须覆盖）
- ✅ 页面加载
- ✅ 主流程成功场景
- ✅ **所有必填字段验证**（每个必填字段一个测试用例）

#### P1 - 重要功能（必须覆盖）
- ✅ **边界值测试**（基于 ABP 限制：min-1, min, max, max+1）
- ✅ **格式验证测试**（基于 ABP 验证规则）
- ✅ **业务逻辑验证**（基于需求）
- ✅ **API 错误处理**

#### P2 - 一般功能（可选）
- UI 交互测试
- 可访问性测试

### 测试用例命名规范

```python
# 基于 ABP 规则的测试用例命名
test_p1_password_too_short           # ABP: RequiredLength
test_p1_password_missing_digit       # ABP: RequireDigit
test_p1_password_missing_uppercase   # ABP: RequireUppercase
test_p1_username_too_long            # ABP: MaxLength
test_p0_email_required               # ABP: Required
```

---

## ✅ 测试验证分层策略

### 前端 vs 后端验证测试

```
测试层级            测试目标                           断言方式
─────────────────────────────────────────────────────────────
前端验证          验证前端是否正确显示错误消息          软断言（记录）
后端 ABP 验证     验证后端是否正确拦截不合规数据        硬断言（必须）⭐
```

### 测试用例必须包含

当验证 ABP 规则时，测试用例必须包含：

1. ✅ **完整的错误检测逻辑**（多种选择器）
2. ✅ **Toast 等待机制**（确保截图完整）
3. ✅ **全屏截图**（`full_page=True`）
4. ✅ **详细的 Allure 描述**（说明对应的 ABP 规则）

### 测试用例示例

```python
@pytest.mark.P1
@allure.story("输入验证")
@allure.title("test_p1_password_too_short")
@allure.description("""
**测试目的**: 验证密码长度不足时的处理
**ABP 规则**: RequiredLength（最小 8 字符）
**前置条件**: 用户已登录
""")
def test_p1_password_too_short(self, page, test_account):
    """P1: 密码太短 - 验证 ABP RequiredLength 规则"""
    # 测试逻辑...
    # 验证后端是否正确拦截
```

---

## 🎯 核心理念

**后端 ABP 是数据合规的最后一道防线，测试必须确保其正确性。**

- 前端校验是用户体验优化
- 后端 ABP 校验是安全保障
- 测试用例应同时覆盖两者，但以后端为准

---

**✨ 当不确定如何补充测试用例时，始终参照后端 ABP 框架的限制。**
