# My Account Test Suite Architecture

> 依据需求文档：`docs/requirements/account-profile-field-requirements.md`

---

## 目录结构

```
tests/myaccount/
├── __init__.py
├── _helpers.py              # 通用工具：截图、账户数据、ABP 常量
├── _matrix_helpers.py       # 矩阵测试通用逻辑
├── conftest.py              # Pytest fixtures
├── docs/
│   └── architecture.md      # 本文档
│
├── profile/                 # Profile 页面（查看模式）
│   ├── test_profile_p0.py          # P0：页面加载、控件可见、导航
│   ├── test_profile_p1_uploadimage.py  # P1：头像上传/格式/大小验证
│   └── test_profile_p2.py          # P2：UI 元素可见性
│
├── profile_settings/        # Profile 编辑模式
│   ├── test_profile_settings_p0.py          # P0：编辑/保存/取消/只读字段
│   ├── test_profile_settings_p1_name_matrix.py     # P1：Name 验证矩阵
│   ├── test_profile_settings_p1_surname_matrix.py  # P1：Surname 验证矩阵
│   ├── test_profile_settings_p1_phone_matrix.py    # P1：PhoneNumber 验证矩阵
│   ├── test_profile_settings_p1_security.py        # P1：安全相关
│   └── test_profile_settings_p2.py          # P2：UI 元素
│
└── change_password/         # 修改密码页面
    ├── _helpers.py                    # 密码策略、生成器
    ├── test_change_password_p0.py     # P0：修改密码 happy path
    ├── test_change_password_p1.py     # P1：密码策略验证矩阵
    ├── test_change_password_p1_ui.py  # P1：UI 验证
    ├── test_change_password_security.py # 安全测试
    └── TEST_COVERAGE.md               # 测试覆盖矩阵
```

---

## 字段约束（来自需求文档）

### 只读字段（不可编辑）
| 字段 | 说明 |
|------|------|
| **UserName** | 用户名，注册时确定 |
| **Email** | 邮箱，注册时确定 |
| **Id** | 系统生成的 GUID |

### 可编辑字段
| 字段 | 最大长度 | 必填 |
|------|----------|------|
| **Name** | ABP 默认（64） | 否 |
| **Surname** | ABP 默认（64） | 否 |
| **PhoneNumber** | ABP 默认（16） | 否 |
| **DisplayName** | 无限制 | 否 |
| **Bio** | 无限制 | 否 |

### 头像上传约束
| 限制项 | 值 |
|--------|-----|
| **最大文件大小** | **2MB** |
| **允许格式** | JPG, PNG, WebP |
| **Magic Bytes 验证** | 后端验证 |

### 修改密码约束
| 规则 | 值 |
|------|-----|
| **最小长度** | 6 字符 |
| **最大长度** | 128 字符 |
| **需要小写字母** | ✅ |
| **需要大写字母** | ✅ |
| **需要数字** | ✅ |
| **需要特殊字符** | ✅ |

---

## 测试策略

### Profile 模块拆分
- **profile/** - 查看模式：验证只读展示、导航、头像上传
- **profile_settings/** - 编辑模式：验证可编辑字段的保存、只读字段的 disabled 状态

### 删除的测试
以下测试已删除，因为对应字段是只读的：
- ~~test_profile_settings_p1_email_matrix.py~~ - Email 不可修改
- ~~test_profile_settings_p1_username_matrix.py~~ - Username 不可修改
- ~~test_profile_settings_p1_avatar.py~~ - 移至 profile/ 目录

### 测试用例设计原则
1. **P0**：关键路径 - 页面加载、保存成功、取消编辑
2. **P1**：核心验证 - 字段验证矩阵、边界值、策略校验
3. **P2**：UI 可见性 - 元素展示、布局
4. **Security**：安全测试 - XSS、注入、权限

---

## API 端点

| 功能 | 端点 | 方法 |
|------|------|------|
| 获取个人资料 | `/api/vibe/my-profile` | GET |
| 更新个人资料 | `/api/vibe/my-profile` | PUT |
| 上传头像 | `/api/account/profile-picture` | PUT |
| 获取头像 | `/api/account/profile-picture/{userId}` | GET |
| 删除头像 | `/api/account/profile-picture` | DELETE |
| 修改密码 | `/api/vibe/change-password` | POST |

---

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-02-03 | 根据需求文档重构，删除 email/username 矩阵测试 |
| 2026-02-03 | 头像测试调整为 2MB + JPG/PNG/WebP |
| 2026-02-03 | 增强只读字段验证（disabled 状态检查） |

