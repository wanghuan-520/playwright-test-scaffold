## Profile Validation Matrix 结构（拆分版）

### 目标
- **按字段拆分便于加速**：矩阵按字段拆成 5 个文件，便于按字段挑选运行/并发分摊。
- **保持统一套路**：场景表驱动 + 关键步骤截图 + “无效不能静默成功”的断言。
- **截图不啰嗦但可检证**：每个场景默认只保留 2 张关键截图（填完/结果态）。
- **回滚策略**：不做“逐场景回滚保存”，交给 `profile_settings` fixture teardown 在 test 结束时按需回滚一次（仅当确实写成功过）。

### 目录结构

```
tests/admin/profile/
  _matrix_helpers.py
  test_profile_settings_p1_username_matrix.py
  test_profile_settings_p1_email_matrix.py
  test_profile_settings_p1_name_matrix.py
  test_profile_settings_p1_surname_matrix.py
  test_profile_settings_p1_phone_matrix.py
```

### 依赖与复用
- **规则常量**：`tests/admin/profile/_helpers.py::AbpUserConsts`
- **公共逻辑**：`tests/admin/profile/_matrix_helpers.py`

### 运行建议
- 仅跑矩阵：
  - `pytest tests/admin/profile -m matrix`
- 只跑某个字段矩阵（示例）：
  - `pytest tests/admin/profile/test_profile_settings_p1_email_matrix.py`
- 排除矩阵跑回归：
  - `pytest tests/admin/profile -m "not matrix"`

