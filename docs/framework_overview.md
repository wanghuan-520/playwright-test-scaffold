# 框架讲解：Playwright Test Scaffold（从跑起来到可扩展）

> 目标：用**最少的入口**把“分析 → 生成 → 执行 → 证据（Allure）”跑通，并且在 `pytest-xdist` 并发下仍然稳定、可复现、可审计。

---

## 1) 先给一个心智模型（你只需要记住 3 条线）

### **执行线（pytest 视角）**

```
pytest 启动
  ├─ conftest.py：聚合 fixtures + 统计每个测试文件耗时
  └─ core/fixtures.py：唯一对外 fixtures 门面（内部拆到 core/fixture/*.py）

每个用例运行
  ├─（可选）申请账号：test_account（按需，不是 autouse）
  ├─（可选）拿登录态页面：auth_page（REUSE_LOGIN 模式更推荐）
  └─ 失败证据链：截图/console/requestfailed/trace → Allure
```

### **配置线（ConfigManager 单例）**

```
config/project.yaml + 环境变量覆盖
  ├─ environments.<env>.frontend/backend.url
  ├─ test_data.accounts.path
  └─ browser / health_check 等
```

### **报告线（Allure + suite cache）**

```
make test      → 生成 allure-results/ → sync 到 .allure-cache/<suite>/allure-results
make report    → 从所有 suite 的“最新结果”合并生成 allure-report/
make serve     → 生成报告并用 http.server 打开
```

---

## 2) 目录分层（“谁负责什么”）

### **入口层**

- `conftest.py`
  - `from core.fixtures import *`：只负责把 fixtures 暴露给 pytest
  - 额外提供一个**小插件**：按“测试文件维度”统计耗时并在结束时打印
- `pytest.ini`
  - 默认排除：`example` 和 `mutate`（破坏性用例需显式跑）

### **核心框架层（core/）**

- `core/fixtures.py`
  - **门面**：把 `core/fixture/*.py` 里的 fixtures 统一 re-export，避免上帝文件
- `core/base_page.py`
  - Page Object 基类：组合 `PageActions + PageWaits`
  - 关键点：`goto()` 默认 `wait_until=domcontentloaded`，对 SPA/长连接页面更稳
  - 内置登录页兜底判断，避免 security 场景卡死等待

### **页面对象层（pages/）**

- `pages/*_page.py`
  - 每个页面一个 Page Object，封装页面元素与业务操作

### **测试层（tests/）**

- `tests/**/test_*.py`
  - 推荐按业务域/页面分目录
  - 用 `@pytest.mark.P0/P1/P2/security/matrix/mutate` 管控执行面

### **配置与工具层（utils/ + config/）**

- `utils/config.py`
  - `ConfigManager` 单例：配置优先级 **环境变量 > project.yaml > 默认值**
- `utils/allure_cache.py`
  - **每个 suite 只保留最新一次结果**，再合并生成“全量最新汇总报告”
- `utils/account_precheck.py`
  - 账号池预检（可选）：用后端接口快速验证登录与 roles，避免并发盲撞
- `utils/account_pool_regen.py`
  - 通过后端注册接口批量生成账号池（重建 `test_account_pool.json`）

---

## 3) pytest fixtures：稳定性的来源（按职责拆分）

### **环境初始化：并发安全的清理 + fail-fast**

`core/fixture/service_env.py` 提供 `setup_test_environment`（session + autouse）：

- **并发安全清理**
  - 只让 `gw0`（或非 xdist 时 master）清理 `allure-results/`、`allure-report/`、`screenshots/`
  - 其它 worker 等待 `.tmp_env_ready`，避免互删/踩踏
- **服务可达性 fail-fast（默认启用）**
  - 只在 primary worker 预检 TCP 可达；不可达直接 `pytest.exit(...)`
  - 可用 `PRECHECK_SERVICES=0` 关闭
- **账号池预检（可选）**
  - `PRECHECK_ACCOUNTS=1` + `REUSE_LOGIN=1` 时启用
  - 可用 `PRECHECK_NEED` 配置“最少可用账号数”，不足直接 fail-fast
- **追加模式**
  - `APPEND_ALLURE_RESULTS=1`：不清空历史结果，适合分段跑后汇总
  - `KEEP_ALLURE_HISTORY=1`：清理时保留 Allure history 趋势数据

### **浏览器参数：统一下沉到 config**

`core/fixture/browser.py`：

- `browser_context_args`：视口、忽略 https 错误等
- `browser_type_launch_args`：headless/slow_mo/启动参数

### **登录态：两条路（建议优先用 storage_state 复用）**

`core/fixture/auth.py`：

- `logged_in_page`（function 级，UI 登录）
  - 适合少量用例/调试
- `auth_page`（function 级，**用 session 级 storage_state**）
  - `ensure_auth_storage_state` 会为每个 xdist worker 生成独立 `storage_state.gwX.json`
  - 目的：减少 ABP 登录频率，降低 lockout 风险，提高 P1/P2/security 速度
  - 开关：`REUSE_LOGIN=1`（并发模式默认倾向启用）

### **账号池：只在用例“确实需要账号”时才分配**

`core/fixture/artifacts_and_accounts.py` 的 `test_account`：

- **非 autouse**：只有显式依赖 `test_account` 的用例才会消耗账号池
- 分配后可选做后端预检（避免 UI 登录阶段才爆掉）
- 失败后自动 `cleanup_after_test`

### **失败证据链：让失败“可复盘”**

`core/fixture/artifacts_and_accounts.py` 的 `artifacts_on_failure`（autouse）：

- 失败时收集：
  - screenshot（全页）
  - console logs
  - requestfailed 列表
  - trace（如果该 context 开启了 tracing）
- 尽量附加到 Allure，形成“可检证”的失败现场

---

## 4) 手动工作流（推荐入口）：Makefile 统一口径

`Makefile` 提供最短、最稳的 3 步：

- `make test TEST_TARGET=tests/...`
  - 跑完后自动：`python -m utils.allure_cache sync ...`
- `make report`
  - 从 `.allure-cache/*/allure-results` 合并生成 `allure-report/`
- `make serve`
  - 生成报告并用 `python -m http.server 59717 ...` 打开

补充：
- `make test-p0`：只跑 `-m "P0"`
- `make test-mutate`：只跑 `-m "mutate"`
- `make clean-cache`：清空 `.allure-cache/`

---

## 5) 如何新增/扩展一个页面的自动化（最小闭环）

建议按这个顺序做，确保每一步都“可跑、可证据化”：

1. **新增 Page Object**
   - 在 `pages/` 下新增 `xxx_page.py`
   - 继承 `BasePage`，把页面的关键操作封装成方法（不要在测试里写一堆 selector）
2. **新增测试目录与用例**
   - 在 `tests/<domain>/<page>/` 下新增 `test_<page>_p0.py` 起步
   - P0 只做“主流程 + 必填校验 + 关键导航”，让回归有稳定地基
3. **按需选择登录与账号**
   - 需要登录态：优先用 `auth_page`
   - 需要用户名/密码链路：显式依赖 `test_account`
4. **用 marker 管控执行面**
   - 高风险写操作用例打 `@pytest.mark.mutate`，默认回归会排除
5. **跑通并检查报告**
   - `make test TEST_TARGET=...`
   - `make serve` 看 Allure 是否有步骤、截图、trace（失败时）

---

## 6) 高频开关（环境变量速查）

- `TEST_ENV=dev`: 选择运行环境（默认读取 `environments.default`）
- `REUSE_LOGIN=1`: 使用 worker 级 `storage_state` 复用登录态（并发强烈建议）
- `PRECHECK_SERVICES=0`: 关闭服务可达性 fail-fast
- `PRECHECK_ACCOUNTS=1`: 启用账号池预检（建议配合 `REUSE_LOGIN=1`）
- `PRECHECK_NEED=4`: 预检至少需要多少可用账号（不足 fail-fast）
- `PERSONAL_SETTINGS_PATH=/admin/profile`: 登录态可用性验证路径
- `APPEND_ALLURE_RESULTS=1`: 追加模式（不清空 allure-results 等）
- `KEEP_ALLURE_HISTORY=1`: 清理时保留 Allure 趋势 history


