### Change Password（/admin/profile/change-password）

### 目录结构

- `tests/admin/profile/change_password/`
  - `test_change_password_p0.py`: 主链路（成功 + 回滚）
  - `test_change_password_p1.py`: 校验矩阵（confirm mismatch / missing current / wrong current / policy / boundary）
  - `test_change_password_security.py`: 安全最小集（未登录拦截 / XSS 不执行）
  - `_helpers.py`: 运行期从 ABP app-config 读取 PasswordPolicy，并生成密码（不落盘明文）

### 依赖与约束

- **账号来源**: 默认使用账号池（运行期 fixture 分配）；仓库文件中不写入任何真实密码/凭证
- **密码字段填写**: Page Object 使用 `secret_fill`（日志不打印明文）
- **回滚策略**: P0 用例必须执行两次改密（old->new->old），避免污染账号池


