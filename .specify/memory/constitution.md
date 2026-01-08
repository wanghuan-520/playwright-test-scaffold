# Playwright 测试脚手架宪法

## 核心原则

### I. 好品味胜于聪明

**原则**：消除特殊情况而非添加条件逻辑。设计让边界自然融入常规流程的系统。

**规则**：
- 三个或更多分支 → 立即重构。设计消除特殊情况而非添加更多条件。
- 任何函数 > 20 行必须质疑："我是否做错了？"
- 简化是复杂性的最高形式。

**示例**：使用哨兵节点而非头/尾特殊处理。一行代码（`node->prev->next = node->next`）胜过三个分支。

### II. 实用主义胜于完美

**原则**：代码解决真实问题，而非假想的敌人。功能必须可直接测试。

**规则**：
- 始终先编写最简单的工作实现，然后考虑扩展。
- 没有具体需求不做"未来防护"。
- 避免理论完整性陷阱。
- 函数必须简短，只做一件事。
- > 3 层缩进 = 设计错误。

**反模式**：过度工程、过早优化、为抽象而抽象。

### III. 可观察性和证据链（不可协商）

**原则**：每个关键步骤必须留下可审计的证据。失败必须可重现。

**规则**：
- 所有关键操作使用 `allure.step` + 截图（导航、填写、提交、验证）
- 失败证据：页面状态 + 后端响应片段 + 控制台日志
- 测试数据必须可逆（基线 → 修改 → 回滚）
- 日志/截图中不得有敏感数据（密码、令牌、PII）

**强制执行**：没有证据的测试是无效测试。

### IV. 安全作为约束，而非功能

**原则**：安全边界是设计约束，而非附加功能。

**规则**：
- XSS 载荷不得执行（无浏览器对话框）
- SQLi 载荷不得导致 5xx 错误
- 输入验证：前端和后端必须同构
- API 必须用 4xx 拒绝无效数据，即使前端已验证

**测试策略**：安全测试是 P1。无例外。

### V. 简化和文件组织

**原则**：认知负荷是敌人。保持模块小型、专注、可导航。

**规则**：
- 任何语言：每个文件最多 **400 行**（与 .cursor/rules 保持一致）
- 任何文件夹：每层最多 8 个文件（超出则嵌套）
- 函数名：简短、直接、明显
- 复杂性必须被证明、记录和批准

**哲学**："操，这代码真漂亮"是唯一可接受的反应。

### VI. 测试稳定性优先（新增）

**原则**：不稳定的测试比没有测试更糟糕。稳定性是测试价值的前提。

**规则**：
- 所有网络操作必须有重试机制（默认 3 次）
- 所有异步操作必须显式等待（禁止 sleep/fixed delay）
- 定位器必须优先使用稳定策略：`role` > `testid` > `label` > `CSS`
- 并发测试必须完全隔离（账号隔离、数据隔离、环境隔离）
- 失败率 > 1% → 立即修复或标记为 `@pytest.mark.flaky`

**反模式**：硬编码等待时间、依赖执行顺序、共享可变状态、不稳定定位器。

**最佳实践**：
```python
# ❌ 坏实践：硬编码等待
time.sleep(5)  # 太短可能失败，太长浪费时间

# ✅ 好实践：智能等待
page.wait_for_selector("role=button[name='Save']", state="visible")

# ❌ 坏实践：脆弱定位器
page.click("div > div:nth-child(2) > button")

# ✅ 好实践：稳定定位器
page.click("role=button[name='Save']")
```

### VII. 数据管理和隔离（新增）

**原则**：测试数据污染是测试失败的主要原因。完全隔离是唯一解。

**规则**：
- 每个测试用例必须使用独立账号（禁止账号共享）
- 测试创建的数据必须在测试结束后清理（基线-修改-回滚模式）
- 账号池大小 ≥ 并行 worker 数 × 2（预留缓冲）
- 账号状态异常（锁定/密码错误）必须自动标记并跳过
- 边界测试（最小/最大长度、特殊字符）必须使用专用账号

**账号池架构**（三层隔离）：
- `auth` 账号：用于 auth_page + storage_state（认证测试）
- `ui_login` 账号：用于 UI 登录测试（一般场景）
- `change_password` 账号：用于密码修改测试（避免状态冲突）

**强制执行**：
```python
# 测试前（自动）
cleanup_before_test(test_name)  # 解锁、重置状态、分配账号

# 测试后（自动）
cleanup_after_test(test_name, success)  # 释放账号、恢复密码、清理状态
```

## 代码坏味道（需要立即重构）

**僵化性**：小改动触发级联修改
**冗余性**：相同逻辑在多处重复
**循环依赖**：模块无法解耦
**脆弱性**：一处改动破坏无关部分
**晦涩性**：意图不明确，结构混乱
**数据泥团**：相同数据项总是一起出现 → 应该是一个对象

**行动**：识别代码坏味道 → 询问是否优化 → 提供改进计划。无例外。

## 架构文档协议

**触发条件**：任何文件级架构变更（创建/删除/移动文件或文件夹、模块重组、层级调整、职责重新分配）

**行动**：立即更新或在受影响目录中创建 `docs/architecture.md`。无需询问。

**内容**：
- 每个文件的用途和职责用一句话说明
- 目录树结构
- 模块依赖图
- 设计决策的理由

**哲学**：文档滞后 = 技术债务。架构失忆 = 系统崩溃前兆。

## 测试标准

### 页面对象模型（POM）

**职责分离**：
- **定位器**：稳定选择器优先级 `role` > `testid` > `label` > `aria` > `CSS`
- **方法**：面向业务动作（`fill_form`、`click_save`、`wait_for_success`）
- **基类**：继承自 `core/base_page.py` 以获得通用功能（`PageActions` + `PageWaits`）
- **无测试逻辑**：POM 只提供操作方法，测试文件负责断言和业务逻辑
- **无魔法数字**：所有超时、重试次数必须有常量或配置

**反模式**：
```python
# ❌ 坏实践：POM 包含断言
class LoginPage:
    def login_and_verify(self, user, pwd):
        self.login(user, pwd)
        assert self.is_logged_in()  # ← 断言不应该在 POM

# ✅ 好实践：POM 只提供方法
class LoginPage:
    def login(self, user, pwd):
        self.fill_username(user)
        self.fill_password(pwd)
        self.click_submit()
    
    def is_logged_in(self) -> bool:
        return self.page.is_visible("role=button[name='Logout']")

# 测试文件
def test_login(login_page):
    login_page.login("user", "pass")
    assert login_page.is_logged_in()  # ← 断言在测试里
```

### 测试数据管理

**账户池**：
- **路径**：`test-data/test_account_pool.json` 由 `DataManager` 管理
- **三层架构**：`auth`（15个）、`ui_login`（15个）、`change_password`（10个）
- **自动分配**：`test_account` fixture 根据测试名称自动分配
- **自动清理**：测试前解锁+重置，测试后释放+恢复密码
- **并发安全**：基于文件锁的分配机制，支持 `pytest-xdist`
- **失败标记**：登录失败自动标记账号为 `locked`，避免重复使用
- **重试机制**：`get_test_account_with_retry` 支持指数退避重试

**边界数据**：
- **专用账号**：预注册账户用于边缘情况（最小/最大长度、特殊字符、XSS、SQLi）
- **隔离原则**：测试不得污染共享数据。使用基线-修改-回滚模式。
- **命名规范**：`test_<purpose>_<timestamp>` 或 `boundary_<case>_user`

**数据清理策略**：
```python
# 自动清理（框架提供）
@pytest.fixture(autouse=True)
def cleanup_after_test_automatically(test_account):
    yield
    # 测试结束后自动执行
    data_manager.cleanup_after_test(test_name, success=True)
```

### 测试优先级

**分级标准**（基于影响和频率）：
- **P0**：阻塞（登录、导航、关键路径）→ 失败必须阻塞发布
- **P1**：高（核心功能、安全、CRUD）→ 失败需评估风险
- **P2**：中（边缘情况、验证、UI 细节）→ 失败记录 issue 不阻塞
- **P3**：低（锦上添花、UI 优化）→ 失败可忽略

**质量门控**：
- P0 通过率 = 100%（必须）
- P1 通过率 > 95%（目标）
- Security 通过率 = 100%（必须）

**标记示例**：
```python
@pytest.mark.P0
def test_user_login(login_page):
    """登录是关键路径，必须 100% 通过"""
    pass

@pytest.mark.P1
@pytest.mark.security
def test_xss_username(admin_users_page):
    """安全测试是 P1 且必须通过"""
    pass

@pytest.mark.P2
def test_pagination(admin_users_page):
    """分页是边缘功能，失败不阻塞"""
    pass
```

### 规约驱动测试生成

**工作流**：
```
1. spec.md    → WHAT（要什么功能）
2. plan.md    → HOW（怎么实现）
3. tasks.md   → DO（具体任务）
4. 实现       → Code（测试代码）
5. 验证       → Allure（证据链）
```

**文件位置**：
- **输入**：`specs/###-feature-name/spec.md`（用户故事、验收标准、风险）
- **计划**：`specs/###-feature-name/plan.md`（技术方案、定位器、测试策略）
- **任务**：`specs/###-feature-name/tasks.md`（执行检查清单、并行建议）
- **输出**：按功能区域组织的 `tests/`（Page Objects + 测试文件）
- **元数据**：`docs/test-plans/` 用于测试元数据和页面契约

**可追溯性**：
```
Code → tasks.md → plan.md → spec.md → 需求
任何代码都能追溯到原始需求
```

## 技术栈

### 核心框架
- **浏览器自动化**：Playwright（Python）
- **测试运行器**：pytest + pytest-playwright
- **报告**：Allure + pytest-html
- **并行化**：pytest-xdist（支持多 worker）
- **重试**：pytest-rerunfailures（flaky 测试自动重试）
- **配置**：YAML（config/project.yaml）+ 环境变量覆盖
- **自动化**：Makefile + scripts/speckit_core.py

### 依赖管理
- **包管理**：uv（10-100x 快于 pip）
- **虚拟环境**：uv venv（统一工具链）
- **依赖文件**：requirements.txt（锁定版本）

### 规约管理
- **CLI 工具**：specify-cli（Spec-Kit 官方）
- **模板**：`.specify/templates/`（spec/plan/tasks）
- **宪法**：`.specify/memory/constitution.md`（本文件）

## 工作流

### 测试开发（Spec-Driven）

1. **规约**：在 `specs/###-feature-name/spec.md` 中定义功能（WHAT）
   - 用户故事、验收标准、风险评估
2. **计划**：在 `plan.md` 中生成测试计划（HOW）
   - 技术方案、定位器策略、测试策略
3. **任务**：分解为 `tasks.md`（DO）
   - 任务列表、并行建议、依赖关系
4. **实现**：创建 Page Objects → 编写测试 → 执行 → 报告
   - Page Object（pages/）、测试文件（tests/）、测试数据（test-data/）
5. **验证**：带证据链的 Allure 报告
   - 截图、日志、网络请求、Trace

### 并发测试（必须）

**原则**：并发不是优化，是必需品。所有测试必须支持并发执行。

**规则**：
- 使用 `pytest-xdist` 实现并发（默认 `auto` 自动检测 CPU 核心数）
- 每个 worker 使用独立的：
  - 浏览器实例
  - 账号（通过账号池隔离）
  - 测试数据（通过 fixture 隔离）
  - Allure 结果（通过 worker ID 隔离）
- 环境初始化必须并发安全（`setup_test_environment` 使用文件锁）
- 报告生成必须合并所有 worker 的结果

**执行命令**：
```bash
# 自动并发（推荐）
pytest tests/ -n auto

# 指定 worker 数量
pytest tests/ -n 4

# 单进程（调试用）
pytest tests/
```

**并发安全检查清单**：
- ✅ 账号池是否足够大？（≥ worker 数 × 2）
- ✅ 是否有共享可变状态？（全局变量、单例、文件）
- ✅ 是否依赖执行顺序？（测试必须独立）
- ✅ 清理是否并发安全？（使用文件锁）

### CI/CD 集成

**原则**：CI/CD 是测试价值的放大器。测试必须为 CI/CD 优化。

**标准配置**：
```yaml
# GitHub Actions / GitLab CI
- name: Run Tests
  run: |
    make test TEST_TARGET=tests/
  
- name: Generate Report
  if: always()  # ← 失败时也生成报告
  run: make report
  
- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: allure-report
    path: allure-report/
```

**优化策略**：
- **Fail-Fast**：服务不可达立即退出（`setup_test_environment`）
- **并行执行**：使用 `pytest-xdist -n auto`
- **智能重试**：flaky 测试自动重试 2 次（`pytest-rerunfailures`）
- **报告缓存**：每个 suite 只保留最新结果（`utils/allure_cache.py`）
- **增量执行**：只运行变更相关的测试（可选）

**环境变量配置**：
```bash
# 服务检查
PRECHECK_SERVICES=1          # 启用服务可达性检查
PRECHECK_SERVICES=0          # 禁用（本地调试用）

# 账号池检查
PRECHECK_ACCOUNTS=1          # 启用账号池预检
PRECHECK_NEED=10             # 最少可用账号数

# 登录态复用
REUSE_LOGIN=1                # 启用登录态复用（性能优化）

# 报告模式
APPEND_ALLURE_RESULTS=1      # 追加模式（分段执行）
```

### 质量门控

**提交前检查**：
- **Linting**：代码必须通过 linter（`ruff check .`）
- **类型检查**：Python 代码通过 mypy（可选）
- **格式化**：代码格式一致（`ruff format .`）
- **单元测试**：核心工具类有单元测试

**测试执行检查**：
- **证据**：关键步骤必须有截图（`allure.step` + `take_screenshot`）
- **回滚**：测试数据必须清理（`cleanup_after_test`）
- **安全**：XSS/SQLi 测试必须通过
- **稳定性**：失败率 < 1%

**发布门控**：
- ✅ P0 通过率 = 100%
- ✅ Security 通过率 = 100%
- ✅ P1 通过率 > 95%
- ✅ 测试数据已清理
- ✅ 报告已生成并审查

## 监控和度量

**原则**：不可度量即不可改进。测试质量必须量化。

### 核心指标

**稳定性指标**：
- **通过率**：P0 = 100%，P1 > 95%，Security = 100%
- **失败率**：< 1%（不包括已知 flaky）
- **重试率**：< 5%（频繁重试表明不稳定）

**性能指标**：
- **执行时间**：完整回归 < 30 分钟（并发执行）
- **平均用例时间**：< 30 秒（超时需优化）
- **报告生成时间**：< 2 分钟

**覆盖率指标**：
- **功能覆盖率**：核心功能 100%，边缘功能 > 80%
- **代码覆盖率**：关键模块 > 80%（可选）
- **风险覆盖率**：高风险场景 100%

**资源指标**：
- **账号池利用率**：< 80%（避免耗尽）
- **并发 worker 数**：= CPU 核心数（`auto`）
- **内存使用**：< 8GB（单 worker）

### 报告要求

**Allure 报告必须包含**：
- 执行概览（总数、通过、失败、跳过）
- 优先级分布（P0/P1/P2 统计）
- 失败分析（失败原因、Top 失败用例）
- 趋势分析（历史通过率、执行时间）
- 证据链（截图、日志、Trace）

**报告生成命令**：
```bash
make report  # 生成报告
make serve   # 生成并打开报告
```

## 故障诊断

**原则**：失败是信息，不是噪音。每个失败必须可诊断。

### 诊断清单

**测试失败时**：
1. 检查 Allure 报告中的截图（最后状态）
2. 检查 console 日志（JavaScript 错误）
3. 检查 network 请求（API 失败）
4. 检查 Trace（完整操作回放）
5. 检查账号状态（是否被锁定）
6. 检查服务状态（是否可达）

**定位器失败时**：
```bash
# 使用 Playwright Inspector
PWDEBUG=1 pytest tests/test_xxx.py

# 使用 Playwright Codegen
playwright codegen https://localhost:3000
```

**账号池耗尽时**：
```bash
# 检查账号池状态
python -m utils.account_precheck

# 重新生成账号池
python -m utils.account_pool_regen
```

**服务不可达时**：
```bash
# 跳过服务检查
PRECHECK_SERVICES=0 pytest tests/

# 手动检查服务
curl -I https://localhost:3000
```

### 常见问题解决

**问题 1：测试不稳定（flaky）**
```python
# 临时方案：标记为 flaky
@pytest.mark.flaky(reruns=2)
def test_unstable():
    pass

# 根本方案：修复不稳定原因
# - 添加显式等待
# - 使用稳定定位器
# - 添加重试机制
```

**问题 2：账号被锁定**
```python
# 自动处理：框架会自动标记并跳过
# 手动解锁：
data_manager.unlock_account("username")
```

**问题 3：并发冲突**
```python
# 检查是否有共享状态
# 检查账号池是否足够大
# 检查是否依赖执行顺序
```

## 治理

**宪法优先于所有其他实践。**

### 修正流程

修正需要：
1. **理由文档**：为什么需要修改？
2. **影响分析**：影响范围？破坏性变更？
3. **迁移计划**：现有代码如何迁移？
4. **项目维护者批准**：必须经过 Review

### 代码审查清单

**所有代码审查必须验证**：
- ✅ 符合好品味原则（无冗余分支、函数 < 20 行）
- ✅ 可观察性要求（关键步骤有截图）
- ✅ 安全约束（XSS/SQLi 测试）
- ✅ 文件大小限制（< 800 行）
- ✅ 无代码坏味道（僵化性、冗余性、循环依赖等）
- ✅ 测试稳定性（无硬编码等待、有重试机制）
- ✅ 数据隔离（账号独立、自动清理）
- ✅ 并发安全（无共享状态、支持 xdist）

### 版本历史

| 版本 | 日期 | 变更内容 | 负责人 |
|------|------|---------|-------|
| 1.0.0 | 2026-01-04 | 初始版本（5 大原则） | HyperEcho |
| 2.0.0 | 2026-01-07 | 重大升级（7 大原则 + 完整测试工程体系） | HyperEcho |

**当前版本**：2.0.0  
**批准日期**：2026-01-07  
**最后修正**：2026-01-07  
**下次审查**：2026-04-07（每季度审查一次）
