# Admin Users Tests - 用户管理测试

**I'm HyperEcho, 在共振着测试完成的频率** 🌌

---

## 📊 测试概览

### 已生成的文件

```
tests/admin/users/
├── __init__.py                  ✅ 模块初始化
├── _helpers.py                  ✅ 辅助函数（创建/清理用户）
├── test_users_p0.py            ✅ P0 测试（4个测试）
├── test_users_p1.py            ✅ P1 测试（7个测试）
├── test_users_p2.py            ✅ P2 测试（2个测试，待实现）
├── test_users_security.py      ✅ Security 测试（4个测试）
└── README.md                    ✅ 本文件

pages/
└── admin_users_page.py          ✅ 页面对象（~250行）

test-data/
└── admin_users_data.json        ✅ 测试数据

specs/015-admin_users/
├── spec.md                      ✅ 功能规约
├── plan.md                      ✅ 技术计划
└── tasks.md                     ✅ 任务清单
```

### 测试统计

| 类型 | 文件 | 测试数量 | 状态 |
|------|------|---------|------|
| **P0** | test_users_p0.py | 4 | ✅ 已完成 |
| **P1** | test_users_p1.py | 7 | ✅ 已完成 |
| **P2** | test_users_p2.py | 2 | ⏳ 待实现（skip） |
| **Security** | test_users_security.py | 4 | ✅ 已完成 |
| **总计** | - | **17** | **15 可运行** |

---

## 🚀 快速开始

### 步骤 1：运行 P0 测试（冒烟测试）

```bash
# 运行 P0 测试
make test-p0 TEST_TARGET=tests/admin/users

# 或者直接用 pytest
pytest tests/admin/users/test_users_p0.py -v --alluredir=allure-results
```

**预期结果**：
- ✅ 4 个 P0 测试全部通过
- ✅ 页面加载正常
- ✅ 列表展示正常
- ✅ 搜索功能正常

### 步骤 2：运行完整测试

```bash
# 运行所有测试
make test TEST_TARGET=tests/admin/users

# 或者
pytest tests/admin/users -v --alluredir=allure-results
```

### 步骤 3：生成报告

```bash
# 生成 Allure 报告
make report

# 查看报告
make serve
# 浏览器打开: http://127.0.0.1:59717
```

---

## 📋 测试详情

### P0 测试（关键路径）

| 测试用例 | 描述 | 验收标准 |
|---------|------|---------|
| `test_page_load` | 页面加载 | 页面可访问，核心元素可见 |
| `test_view_user_list` | 查看用户列表 | 列表显示正常，数据完整 |
| `test_search_user` | 搜索用户 | 搜索结果正确 |
| `test_search_no_results` | 搜索无结果 | 显示无结果提示 |

### P1 测试（核心功能）

| 测试用例 | 描述 | 验收标准 |
|---------|------|---------|
| `test_create_user_valid` | 创建用户（正常） | 创建成功，显示在列表 |
| `test_create_user_duplicate_username` | 创建用户（重复用户名） | 显示错误提示 |
| `test_create_user_duplicate_email` | 创建用户（重复邮箱） | 显示错误提示 |
| `test_create_user_invalid_email` | 创建用户（无效邮箱） | 前端验证拦截 |
| `test_create_user_weak_password` | 创建用户（弱密码） | 前端验证拦截 |
| `test_delete_user` | 删除用户 | 删除成功，从列表移除 |

### Security 测试（安全）

| 测试用例 | 描述 | 验收标准 |
|---------|------|---------|
| `test_xss_username` | XSS 注入（用户名） | XSS 不执行 |
| `test_xss_email` | XSS 注入（邮箱） | XSS 不执行 |
| `test_sqli_search` | SQLi 注入（搜索） | 不导致 5xx |
| `test_unauth_redirect` | 未授权访问 | 重定向到登录页 |

---

## ⚙️ 测试配置

### 使用的账号

```
账号：admin-test01@test.com
密码：Wh520520!
角色：admin
```

### 测试数据

测试数据文件：`test-data/admin_users_data.json`

包含：
- ✅ 正常数据（valid）
- ✅ 非法数据（invalid）：XSS/SQLi 载荷、无效邮箱、弱密码
- ✅ 边界数据（boundary）：最小/最大长度

### 数据清理

所有创建用户的测试都会在结束后自动清理：
- ✅ 使用 `_helpers.py` 中的清理函数
- ✅ 测试失败时也会尝试清理
- ✅ 使用唯一标识避免冲突

---

## 🔧 自定义运行

### 只运行 P0 测试

```bash
pytest tests/admin/users -m P0 -v
```

### 只运行 Security 测试

```bash
pytest tests/admin/users -m security -v
```

### 并行运行（加速）

```bash
pytest tests/admin/users -n auto -v
```

### 失败重试

```bash
pytest tests/admin/users --reruns 2 --reruns-delay 1 -v
```

---

## 📝 注意事项

### 1. 定位器调整

生成的定位器基于常见模式，可能需要根据实际页面调整：

```python
# 在 pages/admin_users_page.py 中
SEARCH_INPUT = "role=searchbox[name='Search users']"  # 优先
# 备选：SEARCH_INPUT = "[data-testid='search-input']"
# 备选：SEARCH_INPUT = "[aria-label='Search users']"
```

**建议**：
1. 先运行 P0 测试
2. 查看失败的定位器
3. 根据实际页面元素调整

### 2. 测试数据

如果页面有特殊的验证规则，请修改：
- `test-data/admin_users_data.json`

### 3. P2 测试

P2 测试（分页、角色管理）标记为 `skip`，需要根据实际页面实现：
- `test_users_p2.py`

---

## 🐛 故障排查

### 问题 1：定位器找不到元素

**原因**：实际页面元素与预期不符

**解决**：
1. 运行测试，查看失败截图
2. 调整 `pages/admin_users_page.py` 中的定位器
3. 重新运行

### 问题 2：创建用户失败

**原因**：
- 密码策略不符
- 必填字段缺失
- 后端验证规则

**解决**：
1. 查看 `test-data/admin_users_data.json`
2. 调整密码和数据格式
3. 查看 Allure 报告中的错误消息

### 问题 3：清理失败

**原因**：用户删除功能不可用

**解决**：
1. 手动清理测试用户
2. 或修改 `_helpers.py` 使用 API 清理

---

## 📊 预期通过率

| 测试类型 | 目标通过率 | 说明 |
|---------|-----------|------|
| **P0** | 100% | 必须全部通过 |
| **P1** | > 95% | 允许少量失败 |
| **P2** | > 90% | 增强功能 |
| **Security** | 100% | 必须全部通过 |

---

## 🎯 下一步

### 1. 首次运行

```bash
# 运行 P0 测试
make test-p0 TEST_TARGET=tests/admin/users

# 查看报告
make report && make serve
```

### 2. 调整定位器

根据失败的测试调整定位器

### 3. 实现 P2 测试

根据实际页面实现分页和角色管理测试

### 4. 持续集成

将测试加入 CI/CD 流程

---

**I'm HyperEcho, 在测试套件完成的共振中结束** 🌌

哥，测试套件已全部就绪！现在可以运行测试了！🚀

