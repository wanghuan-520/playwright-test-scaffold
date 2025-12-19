---
alwaysApply: true
---

# 📊 测试数据管理规范

## ⚠️ 核心原则

**1. 数据分离 - 每个测试用例使用独立的测试数据**
- 每个测试用例必须使用独立的测试账号
- 禁止多个测试用例共享同一个测试账号
- 使用 `test_account` fixture 自动分配账号

**2. 数据清洗 - 测试前后自动清理数据状态**
- 测试前: 自动解锁账号、重置状态
- 测试后: 自动释放账号、恢复状态
- 确保测试之间不会相互影响

## ✅ 正确实现方式

```python
import pytest
import allure
from pages.change_password_page import ChangePasswordPage

@allure.feature("修改密码")
class TestChangePassword:
    
    def _login(self, page, test_account):
        """登录辅助函数 - 使用独立的测试账号"""
        from pages.login_page import LoginPage
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(
            test_account.get("username") or test_account.get("email"), 
            test_account.get("password")
        )
        page.wait_for_timeout(3000)
    
    def test_p0_change_password_success(self, page, test_account):
        """P0: 正常修改密码 - 使用独立测试账号"""
        # ✅ 使用test_account fixture
        self._login(page, test_account)
        
        # ✅ 使用test_account中的密码
        current_password = test_account["password"]
        # ...测试逻辑
```

## ❌ 常见错误

**1. 硬编码测试账号**
```python
# ❌ 错误：硬编码账号
def test_xxx(self, page):
    account = {"username": "testuser", "password": "Test123456!"}

# ✅ 正确：使用test_account fixture
def test_xxx(self, page, test_account):
    self._login(page, test_account)
```

**2. 缺少test_account参数**
```python
# ❌ 错误：没有使用test_account fixture
def test_xxx(self, page):
    self._login(page)

# ✅ 正确：必须添加test_account参数
def test_xxx(self, page, test_account):
    self._login(page, test_account)
```

## 📋 数据清洗流程

**测试前（自动执行）:**
1. 解锁账号（如果被锁定）
2. 重置账号状态（`in_use=False`）
3. 清除锁定原因
4. 分配账号给测试用例（`in_use=True`）

**测试后（自动执行）:**
1. 释放账号（`in_use=False`）
2. 恢复账号密码到初始值（如果被修改）
3. 清除所有状态标记
4. 更新最后使用时间
5. **确保账号完全恢复到初始状态**
