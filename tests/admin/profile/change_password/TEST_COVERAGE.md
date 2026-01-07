# Change Password 模块测试覆盖说明

## 📊 测试全景图（17个测试用例）

### P0 测试（2个）- test_change_password_p0.py
| 测试用例 | 测试点 | 前端限制 | 后端限制 |
|---------|--------|---------|---------|
| test_p0_change_password_page_load | 页面加载+控件可见 | - | 需要认证 |
| test_p0_change_password_success_and_rollback | 主流程成功+回滚 | - | ABP Password Policy验证 |

### P1 功能测试（9个）- test_change_password_p1.py
| 测试用例 | 测试点 | 前端限制 | 后端限制 |
|---------|--------|---------|---------|
| test_p1_confirm_mismatch_should_be_blocked | new≠confirm | JS验证相同 | - |
| test_p1_missing_current_password_should_be_blocked | current为空 | HTML required | 必填 |
| test_p1_missing_new_password_should_be_blocked | new为空 | JS验证非空(trim) | 必填 |
| test_p1_missing_confirm_password_should_be_blocked | confirm为空 | JS验证非空(trim) | 不发送到后端 |
| test_p1_wrong_current_password_should_fail | current错误 | 不验证 | 验证正确性 |
| test_p1_new_password_length_boundaries[max-1/max/max+1] | 长度边界(127/128/129) | 不验证长度 | maxLength=128 |
| test_p1_new_password_min_length_boundaries[min-1/min/min+1] | 长度边界(min) | 不验证长度 | minLength=6 |
| test_p1_password_policy_should_reject_invalid_new_password[digit/upper/lower/special] | 策略违反 | 不验证策略 | RequireDigit/Uppercase/Lowercase/NonAlphanumeric |
| test_p1_new_password_required_unique_chars | 唯一字符数 | 不验证 | RequiredUniqueChars |

### P1 UI测试（2个）- test_change_password_p1_ui.py
| 测试用例 | 测试点 | 测试内容 |
|---------|--------|---------|
| test_p1_password_visibility_toggle_per_field[current/new/confirm] | 密码可见性切换 | 每个输入框独立的eye icon切换 |
| test_p1_password_visibility_toggle_global | 全局切换 | 全局"Show all passwords"按钮（如存在） |

### 安全测试（5个）- test_change_password_security.py
| 测试用例 | 测试点 | 攻击类型 | 断言 |
|---------|--------|---------|-----|
| test_security_unauth_access_should_redirect_to_login | 未登录访问 | 权限绕过 | 重定向到登录页 |
| test_security_xss_payload_should_not_execute[current_password] | XSS注入 | 脚本执行 | 不弹dialog/不崩溃 |
| test_security_xss_payload_should_not_execute[new_and_confirm_password] | XSS注入 | 脚本执行 | 不弹dialog/不崩溃 |
| test_security_sqli_style_input_does_not_crash[current_password] | SQLi注入 | 数据库注入 | 不异常跳转/不崩溃 |
| test_security_sqli_style_input_does_not_crash[new_and_confirm_password] | SQLi注入 | 数据库注入 | 不异常跳转/不崩溃 |

## 🎯 前后端限制总结

### 前端限制（ChangePassword.tsx）
```typescript
const shouldDisabled = () => {
  if (!password.newPassword.trim() || !password.confirmNewPassword.trim()) {
    return true  // 新密码或确认密码为空，禁用提交
  } else if (password.newPassword.trim() !== password.confirmNewPassword.trim()) {
    return true  // 两次密码不一致，禁用提交
  }
  return false
}
```

- **currentPassword**: HTML `required` 属性
- **newPassword**: JS验证非空（trim()）+ 与confirm相同
- **confirmNewPassword**: JS验证非空（trim()）+ 与new相同
- **不验证**: 密码长度、复杂度策略
- **confirmNewPassword不发送到后端**

### 后端限制（ABP Framework）
**API**: `/api/account/my-profile/change-password`

**请求体**:
```json
{
  "currentPassword": "string (maxLength=128)",
  "newPassword": "string (minLength=6, maxLength=128)"
}
```

**ABP Identity Password Policy**:
- `RequiredLength`: 6（最小长度）
- `RequiredUniqueChars`: 1（唯一字符数）
- `RequireDigit`: true（必须包含数字）
- `RequireUppercase`: true（必须包含大写字母）
- `RequireLowercase`: true（必须包含小写字母）
- `RequireNonAlphanumeric`: true（必须包含特殊字符）

**响应**:
- `204 No Content`: 成功
- `400 Bad Request`: 策略违反/字段无效
- `401/403`: currentPassword错误

## ✅ 测试覆盖完整性

### 已覆盖
- ✅ 页面加载
- ✅ 主流程成功+回滚
- ✅ 所有字段的必填验证（current/new/confirm为空）
- ✅ 密码不匹配验证（new≠confirm）
- ✅ current密码错误验证
- ✅ 长度边界（min-1/min/min+1, max-1/max/max+1）
- ✅ 密码策略（digit/upper/lower/special/unique chars）
- ✅ UI功能（密码可见性切换）
- ✅ 安全测试（未登录/XSS/SQLi）

### 未覆盖（可选高级测试）
- ⚠️ new password与old password相同（ABP可能不允许）
- ⚠️ 连续多次改密失败的rate limiting
- ⚠️ 网络异常/超时处理
- ⚠️ 合法的Unicode/emoji密码

## 📝 测试设计原则

### 控制变量法
每个测试只改变一个变量，其他字段填充合法值：
- 测试new password为空 → current填合法值，confirm填dummy值
- 测试XSS注入current → new和confirm填相同的dummy值（绕过match验证）

### 分层断言
```python
if resp is None:
    # 前端拦截：验证前端错误证据
    assert page_obj.wait_for_error_hint() or page_obj.has_validation_error()
else:
    # 后端拦截：验证响应状态码
    assert 400 <= resp.status < 500
```

### 防御性编程
- P0测试必须回滚（避免账号池污染）
- 边界测试成功后立即回滚
- 使用`logged_in_page` fixture获取真实密码

## 🔄 最近更新

### 2025-12-31
1. ✅ 为所有P1测试添加详细的`@allure.description`
2. ✅ 新增2个缺失的测试用例：
   - `test_p1_missing_new_password_should_be_blocked`
   - `test_p1_missing_confirm_password_should_be_blocked`
3. ✅ 完善前后端限制说明
4. ✅ 明确断言依据（前端拦截 vs 后端4xx）

### 测试总数变化
- 修改前: 15个测试
- 修改后: 17个测试（+2个必填验证）

---

**文档维护**: 任何测试用例的增删改都应同步更新本文档
**责任**: 测试开发工程师
**最后更新**: 2025-12-31

