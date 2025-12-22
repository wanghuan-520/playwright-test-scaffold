## Profile 测试结构（tests/admin/profile）

### 设计目标
- **按“职责”拆分文件**：避免 800+ 行巨型文件，降低维护成本。
- **按“优先级”命名**：文件名以 `p0/p1/p2` 开头；领域用后缀（`_security/_matrix/_rules/_validation/_consistency`）。
- **截图不啰嗦但可检证**：默认只截关键证据；回滚只在异常时补证据。

### 目录结构

```
tests/admin/profile/
  test_profile_settings_p0.py
  test_profile_settings_p1_username_matrix.py
  test_profile_settings_p1_email_matrix.py
  test_profile_settings_p1_name_matrix.py
  test_profile_settings_p1_surname_matrix.py
  test_profile_settings_p1_phone_matrix.py
  test_profile_settings_p1_security.py
  test_profile_settings_p2.py
  conftest.py
  _helpers.py
  _matrix_helpers.py
  docs/
    validation-matrix-structure.md
    profile-tests-structure.md
```

### 相关页面：Change Password（生成套件）

本仓库支持对 `/admin/profile/change-password` 单独生成并运行全量套件（P0/P1/P2/security），并且**与 `tests/admin/profile/` 完全隔离**，避免互相覆盖：

```
tests/admin/profile_change_password/
  _helpers.py
  test_profile_change_password_settings_p0.py
  test_profile_change_password_settings_p1.py
  test_profile_change_password_settings_p2.py
  test_profile_change_password_settings_security.py
```

运行建议：
- 跑 change-password 全量：`pytest tests/admin/profile_change_password`
- 只跑 P0：`pytest tests/admin/profile_change_password -m P0`
- 只跑安全：`pytest tests/admin/profile_change_password -m security`

### 文件职责（一句话）
- **`test_profile_settings_p0.py`**：主链路 + 必填字段的“硬断言”。
- **`test_profile_settings_p1_matrix_*.py`**：重场景字段矩阵（标记 `matrix`），按字段拆分便于挑选/并发分摊；包含关键一致性硬断言（如 required 空白必须前端拦截，非法 email 前后端都拒绝）。
- **`test_profile_settings_p1_security.py`**：安全输入（XSS/SQLi）最小载荷集，不崩溃、不执行。
- **`test_profile_settings_p2.py`**：UI 可用性/交互（tab、键盘导航等）。

### 运行建议
- 跑 profile 全量：`pytest tests/admin/profile`
- 只跑 P0：`pytest tests/admin/profile -m P0`
- 排除重矩阵：`pytest tests/admin/profile -m "not matrix"`
- 只跑安全：`pytest tests/admin/profile -m security`

### 账号池预检（强烈建议并发跑前开启）

**目标**：跑前用后端接口快速验证账号池（可登录、roles、是否满足 `/admin/*` 的 admin 要求），把明确不可用账号标记为 `is_locked`，避免 `pytest -n 4` 在 setup 阶段盲撞。

**当前实现**（不需要 OIDC client）：
- `POST /api/account/login`（JSON 登录，拿 cookie）
- `GET /api/abp/application-configuration`（复用 cookie 读取 `currentUser.roles`）

#### 手动运行（后端 token 接口，推荐）

示例：

```bash
PERSONAL_SETTINGS_PATH=/admin/profile \
python3 -m utils.account_precheck --need 4
```

#### 在 pytest 中自动开启

在并发 + 复用登录时，建议打开：

```bash
PRECHECK_ACCOUNTS=1 REUSE_LOGIN=1 \
pytest -n 4 tests/admin/profile
```

