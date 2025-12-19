---
alwaysApply: true
---

# ⚠️ 测试用例生成规范（Critical）

## 测试用例完整性检查清单

**生成测试用例时，必须确保覆盖以下场景：**

### P0 - 核心功能（必须覆盖）
- ✅ 页面加载测试
- ✅ 主流程成功场景
- ✅ **所有必填字段的验证**（每个必填字段都要有单独的测试用例）
  - 示例：表单有3个必填字段 → 需要3个P0测试用例分别验证

### P1 - 重要功能（必须覆盖）
- ✅ **边界值测试**（最小值、最大值、边界值）
  - 长度限制：必须测试 min-1, min, min+1, max-1, max, max+1
- ✅ **格式验证测试**（根据验证规则生成）
  - 正则表达式规则 → 生成对应的格式验证测试
  - 密码相关：必须覆盖所有 ABP 标准规则
- ✅ **业务逻辑验证**（规范中明确要求的场景）
- ✅ **API错误处理**（网络错误、服务器错误、超时）

### P2 - 一般功能（可选）
- UI交互测试（显示/隐藏、键盘导航等）
- 可访问性测试

## ❌ 常见错误（禁止）

### 1. 缺少断言
```python
# ❌ 错误：只有 logger.checkpoint，没有实际断言
logger.checkpoint("验证错误", True)

# ✅ 正确：必须有实际断言
assert change_password_page.has_validation_error(), "应该显示错误"
errors = change_password_page.get_validation_errors()
assert len(errors) > 0, "应该至少有一个验证错误"
```

### 2. 必填字段验证不完整
```python
# ❌ 错误：只验证了部分必填字段

# ✅ 正确：每个必填字段都要有单独的测试用例
def test_p0_current_password_required(...)
def test_p0_new_password_required(...)
def test_p0_confirm_password_required(...)
```

### 3. 边界值测试缺失
```python
# ❌ 错误：只测试了"太短"

# ✅ 正确：完整的边界值测试
def test_p1_password_too_short(...)      # 小于最小值
def test_p1_password_too_long(...)       # 大于最大值
def test_p1_password_boundary_values(...)  # 正好等于 min 和 max
```

### 4. 格式验证不完整
```python
# ❌ 错误：只测试了长度，没有测试格式要求

# ✅ 正确：根据验证规则生成所有格式验证测试
def test_p1_password_missing_uppercase(...)
def test_p1_password_missing_lowercase(...)
def test_p1_password_missing_digit(...)         # ABP RequireDigit
def test_p1_password_missing_special_char(...)  # ABP RequireNonAlphanumeric
```

## ✅ 测试用例生成流程

1. **分析表单字段**
   - 列出所有字段
   - 标记必填/可选
   - 提取验证规则
   - **如果验证规则不明确，以后端 ABP 框架限制为准**

2. **生成P0测试用例**
   - 页面加载
   - 主流程成功
   - **每个必填字段一个验证测试**

3. **生成P1测试用例**
   - **边界值测试**（min-1, min, max, max+1）
   - **格式验证测试**（根据验证规则）
   - **ABP 标准密码验证规则必须全部覆盖**
   - **业务逻辑测试**
   - **API错误处理**

4. **生成P2测试用例**（可选）
   - UI交互
   - 可访问性

5. **验证完整性**
   - 检查是否有断言（禁止只有注释）
   - 检查必填字段是否全部覆盖
   - 检查边界值是否完整
   - **检查 ABP 密码验证规则是否全部覆盖**（6 个规则）
   - **检查关键步骤是否有截图**（必须）
