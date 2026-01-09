# 多轮 AI 研究助手系统 - 测试计划

> **需求来源**: [aevatarAI/aevatar-agent-framework#67](https://github.com/aevatarAI/aevatar-agent-framework/issues/67)  
> **生成时间**: 2026-01-09  
> **测试范围**: 多轮迭代研究系统的完整用户交互流程

---

## 1. 页面/系统概述

### 1.1 系统描述

多轮 AI 研究助手系统，用户只需输入**一句话方向**，系统自动进行多轮迭代研究，直到收敛或用户停止。

### 1.2 核心流程（9 阶段）

```
阶段 0: 用户输入方向 + 边界
阶段 1: 系统回传研究简报
阶段 2-6: Round N 自主计划与并行调研
阶段 7: 计算完成，结果回填
阶段 8: 合并与交付中心更新
阶段 9: 进入 Round N+1
```

### 1.3 Agent 角色

| Agent | 职责 |
|-------|------|
| 研究总控 (RA) | 单入口，协调所有 Agent |
| Planner | 生成计划、识别关键分叉点 |
| Librarian | 检索证据、找反例、补缺口 |
| Reasoner | 综合推理、产出结论卡 |
| Verifier | 复核结论、判断是否需要运算 |
| Compute | 执行程序运算任务 |
| 交付物中心 (W) | 维护论文稿、结论清单 |

### 1.4 风险点分析

| 风险 | 等级 | 说明 |
|------|------|------|
| 多轮状态丢失 | HIGH | 长时间运行可能导致上下文丢失 |
| 并行任务竞态 | HIGH | 多 Agent 并行可能产生数据冲突 |
| 运算任务超时 | MEDIUM | Compute 任务可能长时间运行 |
| 用户中断处理 | MEDIUM | 用户随时可能中断/改方向 |
| 交付物一致性 | MEDIUM | 论文稿与结论清单同步问题 |

---

## 2. 元素映射

### 2.1 输入界面

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 方向输入框 | `[role="textbox"][name="research-direction"]` | 用户输入研究方向 |
| 边界设置 | `[role="group"][name="constraints"]` | 预算/速度/严谨度/禁止项 |
| 预算选择 | `[role="slider"][name="budget"]` | 成本级别选择 |
| 速度偏好 | `[role="radiogroup"][name="speed"]` | 快速/标准/深度 |
| 严谨度 | `[role="slider"][name="rigor"]` | 研究严谨度 |
| 禁止项输入 | `[role="textbox"][name="exclusions"]` | 不希望涉及的领域 |
| 提交按钮 | `button:has-text("开始研究")` | 启动研究流程 |

### 2.2 研究简报界面（阶段 1）

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 问题改写区 | `[data-testid="question-rewrite"]` | 系统理解后的问题重述 |
| 假设清单 | `[role="list"][name="assumptions"]` | 默认假设列表 |
| 风险清单 | `[role="list"][name="risks"]` | 已识别风险 |
| 里程碑路线图 | `[data-testid="roadmap"]` | 预计每轮产出 |
| 继续按钮 | `button:has-text("继续")` | 确认方向正确 |
| 纠偏按钮 | `button:has-text("纠偏")` | 修改假设/范围 |

### 2.3 进度面板（阶段 2-6）

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 当前轮次 | `[data-testid="current-round"]` | 显示 Round N |
| 进度条 | `[role="progressbar"]` | 当前轮次进度 |
| Agent 状态区 | `[data-testid="agent-status"]` | 各 Agent 工作状态 |
| Planner 状态 | `[data-testid="planner-status"]` | 计划生成状态 |
| Librarian 状态 | `[data-testid="librarian-status"]` | 证据检索状态 |
| Reasoner 状态 | `[data-testid="reasoner-status"]` | 推理状态 |
| 中断按钮 | `button:has-text("中断")` | 用户主动中断 |
| 改方向按钮 | `button:has-text("改方向")` | 修改研究方向 |

### 2.4 执行计划卡（程序运算确认）

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 计划卡容器 | `[role="dialog"][name="execution-plan"]` | 确认弹窗 |
| 运算描述 | `[data-testid="compute-description"]` | 要算什么 |
| 预期产物 | `[data-testid="expected-output"]` | 运算结果预期 |
| 成本级别 | `[data-testid="cost-level"]` | 低/中/高 |
| 风险提示 | `[data-testid="risk-warning"]` | 风险说明 |
| 执行按钮 | `button:has-text("执行")` | 确认执行 |
| 降级按钮 | `button:has-text("降级")` | 使用替代方案 |
| 暂不执行 | `button:has-text("暂不执行")` | 跳过此运算 |
| 推荐理由 | `[data-testid="recommendation"]` | 系统推荐说明 |

### 2.5 运算状态面板

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 状态时间线 | `[data-testid="status-timeline"]` | 运算进度时间线 |
| 当前阶段 | `[data-testid="current-stage"]` | 当前执行阶段 |
| 日志摘要 | `[data-testid="log-summary"]` | 运行日志 |
| 异常预警 | `[role="alert"]` | 异常信息 |
| 中间快照 | `[data-testid="intermediate-snapshot"]` | 中间结果 |
| 中断按钮 | `button:has-text("中断运算")` | 停止运算 |

### 2.6 结论卡界面

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 结论卡列表 | `[role="list"][name="conclusions"]` | 所有结论卡 |
| 结论内容 | `[data-testid="conclusion-content"]` | 结论描述 |
| 可信度指示 | `[data-testid="confidence-level"]` | 可信度等级 |
| 证据链接 | `[data-testid="evidence-link"]` | 关联证据 |
| 冲突标记 | `[data-testid="conflict-marker"]` | 与其他结论冲突 |

### 2.7 交付物中心

| 元素 | 定位器建议 | 说明 |
|------|-----------|------|
| 论文草稿 | `[data-testid="paper-draft"]` | 当前论文稿 |
| 结论清单 | `[data-testid="conclusion-list"]` | 所有已确认结论 |
| 证据对照 | `[data-testid="evidence-comparison"]` | 证据对照表 |
| 下一步建议 | `[data-testid="next-steps"]` | 2-3 个选项 |
| 推荐标记 | `[data-testid="recommended-option"]` | 系统推荐项 |

---

## 3. 用例设计

### 3.1 P0 - 核心主链路（必须通过）

| ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|----------|
| P0-001 | 输入方向启动研究 | 系统空闲 | 1. 输入研究方向<br>2. 点击"开始研究" | 显示研究简报 |
| P0-002 | 确认研究简报继续 | 已显示研究简报 | 1. 查看简报内容<br>2. 点击"继续" | 进入 Round 1 |
| P0-003 | Round N 完成产出结论 | Round N 运行中 | 等待 Round 完成 | 显示本轮总结 + 结论卡 |
| P0-004 | 执行计划卡确认执行 | 需要程序运算 | 1. 查看执行计划卡<br>2. 点击"执行" | 开始运算并显示状态面板 |
| P0-005 | 运算完成结果展示 | 运算运行中 | 等待运算完成 | 显示结果摘要 + 对结论影响 |
| P0-006 | 查看交付物中心 | 至少完成 1 轮 | 点击交付物中心 | 显示论文稿 + 结论清单 |
| P0-007 | 多轮迭代直到收敛 | 研究进行中 | 持续多轮直到系统判断收敛 | 显示最终交付物 |
| P0-008 | 用户主动停止研究 | 研究进行中 | 点击"停止研究" | 保存当前状态 + 显示交付物 |

### 3.2 P1 - 重要功能（应该通过）

#### 3.2.1 输入边界测试

| ID | 用例名称 | 测试输入 | 预期结果 |
|----|----------|----------|----------|
| P1-IN-001 | 方向为空 | 空字符串 | 提示"请输入研究方向" |
| P1-IN-002 | 方向过短 | "AI" | 提示"方向描述过于简短，请补充" |
| P1-IN-003 | 方向过长 | 超过 1000 字 | `TBD(需确认最大长度)` |
| P1-IN-004 | 特殊字符 | 包含 `<script>` | 安全过滤，正常处理 |
| P1-IN-005 | 多语言输入 | 中英文混合 | 正常处理 |

#### 3.2.2 研究简报交互

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-BR-001 | 纠偏修改假设 | 1. 点击"纠偏"<br>2. 修改假设<br>3. 确认 | 更新简报并继续 |
| P1-BR-002 | 纠偏修改范围 | 1. 点击"纠偏"<br>2. 缩小范围<br>3. 确认 | 更新简报并继续 |
| P1-BR-003 | 多次纠偏 | 连续 3 次纠偏 | 每次都正确更新 |

#### 3.2.3 并行调研状态

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-PA-001 | 查看 Agent 状态 | Round 运行中查看状态面板 | 显示各 Agent 实时状态 |
| P1-PA-002 | 进度实时更新 | 观察进度条 | 进度条随时间更新 |
| P1-PA-003 | 中途改方向 | 1. 点击"改方向"<br>2. 输入新方向 | 中断当前，重新开始 |
| P1-PA-004 | 中途中断 | 点击"中断" | 保存当前状态，显示部分结果 |

#### 3.2.4 执行计划卡交互

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-EP-001 | 选择降级方案 | 点击"降级" | 使用替代方案继续 |
| P1-EP-002 | 暂不执行 | 点击"暂不执行" | 跳过运算，显示影响说明 |
| P1-EP-003 | 超时自动处理 | 等待确认超时 | 按默认策略处理（自动执行或降级） |

#### 3.2.5 运算状态监控

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-CS-001 | 查看中间快照 | 运算中点击查看快照 | 显示当前中间结果 |
| P1-CS-002 | 中断长时间运算 | 运算超过预期时中断 | 保存中间状态，显示部分结果 |
| P1-CS-003 | 运算失败处理 | 模拟运算失败 | 显示失败原因 + 补救选项 |
| P1-CS-004 | 异常预警展示 | 运算出现异常 | 显示预警信息 |

#### 3.2.6 结论与证据

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-CL-001 | 查看结论详情 | 点击结论卡 | 显示完整内容 + 证据链接 |
| P1-CL-002 | 查看证据对照 | 点击证据链接 | 跳转到对应证据 |
| P1-CL-003 | 冲突结论标记 | 存在冲突结论 | 显示冲突标记 + 说明 |
| P1-CL-004 | 结论可信度变化 | 新证据出现 | 更新可信度显示 |

#### 3.2.7 交付物管理

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P1-DL-001 | 下载论文草稿 | 点击下载 | 下载 MD/PDF 格式 |
| P1-DL-002 | 选择下一轮方向 | 选择推荐选项 | 按选择继续下一轮 |
| P1-DL-003 | 选择非推荐选项 | 选择非推荐选项 | 按选择继续（可能有提示） |

### 3.3 P2 - 增强功能（可以测试）

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| P2-001 | 历史研究查看 | 查看历史研究列表 | 显示所有历史研究 |
| P2-002 | 恢复中断研究 | 选择中断的研究继续 | 从中断点继续 |
| P2-003 | 研究对比 | 对比两个研究结果 | 显示差异对比 |
| P2-004 | 导出完整报告 | 导出包含所有轮次的报告 | 生成完整报告文件 |
| P2-005 | 分享研究 | 生成分享链接 | 可通过链接查看 |

### 3.4 Security - 安全测试

| ID | 用例名称 | 测试步骤 | 预期结果 |
|----|----------|----------|----------|
| SEC-001 | XSS 方向输入 | 输入 `<script>alert(1)</script>` | 安全过滤，不执行脚本 |
| SEC-002 | XSS 纠偏输入 | 在纠偏框输入恶意脚本 | 安全过滤 |
| SEC-003 | 敏感信息保护 | 检查论文稿/结论中无密钥泄露 | 无敏感信息暴露 |
| SEC-004 | 并发请求攻击 | 大量并发启动研究 | 限流保护，返回 429 |
| SEC-005 | 长时间运算资源限制 | 提交大量运算任务 | 资源配额限制生效 |

---

## 4. 数据设计

### 4.1 研究方向测试数据

```json
{
  "valid_directions": [
    {
      "input": "研究大语言模型在代码生成领域的最新进展，重点关注 Prompt Engineering 技术",
      "scenario": "标准研究方向"
    },
    {
      "input": "分析 2025 年加密货币市场趋势，排除 Meme 币",
      "scenario": "带排除项"
    },
    {
      "input": "快速调研 React Server Components 的生产实践案例",
      "scenario": "快速模式"
    }
  ],
  "invalid_directions": [
    {
      "input": "",
      "scenario": "空输入",
      "expected_error": "请输入研究方向"
    },
    {
      "input": "AI",
      "scenario": "过短",
      "expected_error": "方向描述过于简短"
    }
  ],
  "boundary_directions": [
    {
      "input": "A".repeat(1000),
      "scenario": "最大长度边界",
      "expected": "TBD(需确认最大长度)"
    }
  ]
}
```

### 4.2 边界设置测试数据

```json
{
  "constraints": {
    "budget": {
      "low": { "value": "低", "description": "限制 API 调用次数" },
      "medium": { "value": "中", "description": "标准资源配额" },
      "high": { "value": "高", "description": "不限制资源" }
    },
    "speed": {
      "fast": { "value": "快速", "description": "牺牲深度换速度" },
      "standard": { "value": "标准", "description": "平衡模式" },
      "deep": { "value": "深度", "description": "追求严谨" }
    },
    "rigor": {
      "min": 1,
      "max": 10,
      "default": 5
    }
  }
}
```

### 4.3 执行计划卡测试数据

```json
{
  "execution_plans": [
    {
      "id": "EP-001",
      "description": "运行 Python 数据分析脚本",
      "expected_output": "统计图表 + 数据摘要",
      "cost_level": "low",
      "risk_level": "low",
      "auto_execute": true
    },
    {
      "id": "EP-002",
      "description": "调用外部 API 获取实时数据",
      "expected_output": "最新市场数据",
      "cost_level": "medium",
      "risk_level": "low",
      "auto_execute": true
    },
    {
      "id": "EP-003",
      "description": "训练小型 ML 模型验证假设",
      "expected_output": "模型评估报告",
      "cost_level": "high",
      "risk_level": "medium",
      "auto_execute": false,
      "requires_confirmation": true
    }
  ]
}
```

---

## 5. 自动化建议

### 5.1 Page Object 设计

```python
# pages/research_agent/
#   ├── input_page.py          # 输入界面
#   ├── briefing_page.py       # 研究简报
#   ├── progress_panel.py      # 进度面板
#   ├── execution_plan_dialog.py  # 执行计划卡
#   ├── compute_status_panel.py   # 运算状态
#   ├── conclusion_card.py     # 结论卡
#   └── delivery_center.py     # 交付物中心
```

### 5.2 Fixture 设计

```python
@pytest.fixture
def research_session(auth_page):
    """创建一个研究会话"""
    input_page = ResearchInputPage(auth_page.page)
    input_page.navigate()
    return input_page

@pytest.fixture
def active_research(research_session, test_direction):
    """启动一个活跃的研究"""
    research_session.input_direction(test_direction)
    research_session.click_start()
    briefing = BriefingPage(research_session.page)
    briefing.wait_for_load()
    return briefing

@pytest.fixture
def running_round(active_research):
    """进入运行中的 Round"""
    active_research.click_continue()
    progress = ProgressPanel(active_research.page)
    progress.wait_for_load()
    return progress
```

### 5.3 等待策略

```python
# 长时间运算等待（可配置超时）
def wait_for_compute_complete(self, timeout: int = 300):
    """等待运算完成，默认 5 分钟超时"""
    self.page.wait_for_selector(
        '[data-testid="compute-complete"]',
        state="visible",
        timeout=timeout * 1000
    )

# 轮次完成等待
def wait_for_round_complete(self, timeout: int = 600):
    """等待当前轮次完成"""
    self.page.wait_for_selector(
        '[data-testid="round-summary"]',
        state="visible",
        timeout=timeout * 1000
    )
```

### 5.4 测试目录结构

```
tests/
└── research_agent/
    ├── conftest.py           # 研究系统专用 fixtures
    ├── test_input_p0.py      # P0: 输入主链路
    ├── test_briefing_p0.py   # P0: 研究简报
    ├── test_round_p0.py      # P0: Round 执行
    ├── test_compute_p0.py    # P0: 运算确认
    ├── test_delivery_p0.py   # P0: 交付物
    ├── test_input_p1.py      # P1: 输入边界
    ├── test_parallel_p1.py   # P1: 并行状态
    ├── test_conclusion_p1.py # P1: 结论交互
    └── test_security.py      # Security 测试
```

---

## 6. 特殊测试场景

### 6.1 长时间运行测试

由于研究可能需要多轮迭代，建议：

- 设置合理的超时时间（单轮 10 分钟，总计 1 小时）
- 使用 `pytest.mark.slow` 标记长时间测试
- CI 中可选择跳过或单独运行

### 6.2 并行任务测试

测试多 Agent 并行场景：

- Planner + Librarian + Reasoner 同时工作
- 验证状态面板正确显示所有 Agent 状态
- 验证数据不会因并行而冲突

### 6.3 中断恢复测试

测试各阶段的中断与恢复：

- Round 执行中中断
- 运算执行中中断
- 纠偏过程中中断

---

## 7. 证据链

| 文件 | 说明 | 状态 |
|------|------|------|
| `artifacts/research-agent-system/metadata.json` | 元素映射与页面结构 | TBD（需实际页面） |
| `artifacts/research-agent-system/visible.txt` | 可见元素摘要 | TBD（需实际页面） |
| `artifacts/research-agent-system/page.png` | 页面截图 | TBD（需实际页面） |

> **说明**：本计划基于需求文档生成，实际元素定位器需在页面开发完成后通过 Playwright MCP 验证并更新。

---

## 8. 风险与依赖

### 8.1 依赖

- 后端 Agent 系统 API 可用
- WebSocket 连接稳定（用于实时状态更新）
- Compute 服务可用

### 8.2 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| 长时间运行导致超时 | 设置分阶段检查点 |
| 状态同步延迟 | 增加轮询重试机制 |
| 运算资源不足 | Mock Compute 服务进行功能测试 |

---

**测试计划版本**: v1.0  
**最后更新**: 2026-01-09

