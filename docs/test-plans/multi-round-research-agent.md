# 多轮 AI 研究助手系统 - 测试计划

> 基于需求文档生成，详见 [需求文档](../requirements/multi-round-research-agent-requirements.md)

---

## 1. 系统概述

### 1.1 核心流程

```
用户输入方向 → 研究简报 → Round N 并行调研 → 执行计划卡(可选) → 结果回填 → 交付中心 → Round N+1
```

### 1.2 关键角色

| 角色 | 职责 |
|-----|------|
| 研究总控 (RA) | 单入口协调者，接收用户输入，调度所有 Agent |
| Planner | 生成计划与里程碑 |
| Librarian | 自主检索与证据收集 |
| Reasoner | 综合推理，产出结论卡 |
| Verifier | 复核结论，判断是否需要程序运算 |
| Compute | 执行程序运算任务 |
| 交付物中心 | 论文稿、结论清单、证据对照 |

---

## 2. 测试范围

### 2.1 P0 - 核心流程（8 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P0-001 | 用户输入研究方向 | 系统返回研究简报（1页） |
| P0-002 | 研究简报包含必要元素 | 包含：问题改写、假设清单、风险清单、里程碑 |
| P0-003 | 用户点击「继续」 | 进入 Round 1 |
| P0-004 | Round N 启动后 Agent 并行工作 | Planner/Librarian/Reasoner 同时产出 |
| P0-005 | 结论卡生成 | 包含：结论内容、可信度、证据链接 |
| P0-006 | 需要程序运算时弹出执行计划卡 | 显示：运算描述、成本级别、风险点、三选一按钮 |
| P0-007 | 每轮结束更新交付物中心 | 论文草稿、结论清单、未决问题更新 |
| P0-008 | 多轮迭代直至收敛 | 用户可选择继续/停止 |

### 2.2 P1 - 重要功能（24 个用例）

#### 2.2.1 输入阶段（4 个）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P1-001 | 输入空方向 | 提示必填 |
| P1-002 | 输入超长方向（>1000字） | 正常处理或提示截断 |
| P1-003 | 设置可选边界（预算/速度/严谨度） | 边界参数生效 |
| P1-004 | 设置禁止项 | 系统遵守禁止项约束 |

#### 2.2.2 研究简报阶段（4 个）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P1-005 | 用户点击「纠偏」 | 可修改假设/范围 |
| P1-006 | 修改假设后重新生成简报 | 简报内容更新 |
| P1-007 | 默认假设清单可编辑 | 支持勾选/取消勾选 |
| P1-008 | 风险清单分级显示 | 高/中/低风险有区分 |

#### 2.2.3 并行调研阶段（6 个）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P1-009 | 进度面板实时更新 | 显示当前阶段和下一产物 |
| P1-010 | Agent 状态可见 | 各 Agent 运行/空闲/完成状态 |
| P1-011 | 用户随时中断 | 系统安全停止 |
| P1-012 | 用户改方向 | 系统切换研究方向 |
| P1-013 | 用户降预算 | 系统调整策略 |
| P1-014 | 用户切换保守路线 | 系统降低风险偏好 |

#### 2.2.4 执行计划卡阶段（5 个）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P1-015 | 低成本低风险运算自动执行 | 不弹出确认卡 |
| P1-016 | 高成本运算弹出确认 | 显示执行计划卡 |
| P1-017 | 用户选择「执行」 | 提交运算任务 |
| P1-018 | 用户选择「降级」 | 切换为低成本方案 |
| P1-019 | 用户选择「暂不执行」 | 说明影响，切换替代路径 |

#### 2.2.5 运算监控阶段（5 个）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P1-020 | 运算期间显示状态时间线 | 阶段进度可见 |
| P1-021 | 异常预警 | 及时通知用户 |
| P1-022 | 中间结果快照 | 用户可提前判断方向 |
| P1-023 | 运算期间系统并行推进 | Librarian 继续补证据 |
| P1-024 | 运算失败 | 显示原因分类和补救选项 |

### 2.3 P2 - 增强功能（5 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| P2-001 | 论文草稿导出 MD 格式 | 下载成功 |
| P2-002 | 论文草稿导出 PDF 格式 | 下载成功 |
| P2-003 | 结论卡点评功能 | 用户可标记重要性 |
| P2-004 | 证据对照表展开/折叠 | 交互正常 |
| P2-005 | 历史 Round 记录查看 | 可回溯每轮产出 |

### 2.4 Security - 安全测试（5 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| SEC-001 | 研究方向注入攻击 | 输入过滤，无执行 |
| SEC-002 | 运算任务权限校验 | 仅授权用户可触发 |
| SEC-003 | 敏感数据脱敏 | 日志不含敏感信息 |
| SEC-004 | 会话隔离 | 不同用户数据隔离 |
| SEC-005 | 运算资源限制 | 防止资源耗尽攻击 |

---

## 3. 元素定位器映射

```json
{
  "input_section": {
    "direction_input": "[data-testid='research-direction']",
    "constraints_group": "[data-testid='constraints']",
    "start_button": "button:has-text('开始研究')"
  },
  "briefing_section": {
    "question_rewrite": "[data-testid='question-rewrite']",
    "assumptions_list": "[data-testid='assumptions']",
    "risks_list": "[data-testid='risks']",
    "roadmap": "[data-testid='roadmap']",
    "continue_button": "button:has-text('继续')",
    "adjust_button": "button:has-text('纠偏')"
  },
  "progress_panel": {
    "current_round": "[data-testid='current-round']",
    "progress_bar": "[role='progressbar']",
    "agent_status": "[data-testid='agent-status']",
    "interrupt_button": "button:has-text('中断')"
  },
  "execution_plan_dialog": {
    "container": "[role='dialog'][data-testid='execution-plan']",
    "execute_button": "button:has-text('执行')",
    "downgrade_button": "button:has-text('降级')",
    "skip_button": "button:has-text('暂不执行')"
  },
  "compute_status": {
    "timeline": "[data-testid='status-timeline']",
    "current_stage": "[data-testid='current-stage']",
    "alert": "[role='alert']",
    "snapshot": "[data-testid='intermediate-snapshot']"
  },
  "conclusion_card": {
    "list": "[data-testid='conclusions']",
    "content": "[data-testid='conclusion-content']",
    "confidence": "[data-testid='confidence-level']",
    "evidence_link": "[data-testid='evidence-link']"
  },
  "delivery_center": {
    "paper_draft": "[data-testid='paper-draft']",
    "conclusion_list": "[data-testid='conclusion-list']",
    "next_steps": "[data-testid='next-steps']"
  }
}
```

---

## 4. 测试数据设计

### 4.1 有效数据

```json
{
  "valid_direction": "研究大语言模型在代码生成领域的最新进展，重点关注 Prompt Engineering",
  "valid_constraints": {
    "budget": "medium",
    "speed": "normal",
    "rigor": "high",
    "forbidden": ["多模态", "图像生成"]
  }
}
```

### 4.2 边界数据

```json
{
  "empty_direction": "",
  "long_direction": "A".repeat(1001),
  "special_chars": "<script>alert('xss')</script>",
  "unicode_direction": "研究 🤖 AI 在 émoji 领域的应用"
}
```

---

## 5. 自动化建议

### 5.1 Page Object 结构

```
pages/
├── research_input_page.py      # 输入方向页面
├── briefing_page.py            # 研究简报页面
├── progress_panel.py           # 进度面板组件
├── execution_plan_dialog.py    # 执行计划卡弹窗
├── compute_monitor_page.py     # 运算监控页面
└── delivery_center_page.py     # 交付物中心页面
```

### 5.2 Fixture 设计

```python
@pytest.fixture
def research_session(page, test_account):
    """创建并返回一个已登录的研究会话"""
    pass

@pytest.fixture
def mock_agent_responses():
    """模拟 Agent 响应数据"""
    pass

@pytest.fixture
def cleanup_research_data(request):
    """测试后清理研究数据"""
    pass
```

---

## 6. 测试统计

| 优先级 | 数量 | 占比 |
|-------|------|------|
| P0 | 8 | 19% |
| P1 | 24 | 57% |
| P2 | 5 | 12% |
| Security | 5 | 12% |
| **Total** | **42** | 100% |

---

## 7. 注意事项

1. **元素定位器需验证**：本计划基于需求文档生成，实际定位器需在页面开发完成后验证
2. **长时间运行测试**：运算监控相关测试建议单独执行，避免阻塞 CI
3. **并行任务测试**：需要 WebSocket 支持实时状态更新
4. **数据隔离**：每个测试用例应使用独立的研究会话

---

## 8. 性能测试（6 个用例）

| ID | 场景 | 指标 | 阈值 |
|----|------|------|------|
| PERF-001 | 研究简报生成时间 | 响应时间 | < 5s |
| PERF-002 | 单 Round 完成时间 | 端到端耗时 | < 60s |
| PERF-003 | 结论卡渲染性能 | 首屏时间 | < 1s |
| PERF-004 | 100+ 结论卡列表滚动 | 帧率 | > 30fps |
| PERF-005 | 论文导出 PDF（50页） | 生成时间 | < 10s |
| PERF-006 | WebSocket 消息延迟 | P99 延迟 | < 200ms |

---

## 9. 并发测试（4 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| CONC-001 | 10 用户同时创建研究会话 | 全部成功，无资源争用 |
| CONC-002 | 同一用户多标签页操作 | 数据同步一致 |
| CONC-003 | 多 Agent 并发写入结论卡 | 无数据丢失/覆盖 |
| CONC-004 | 运算任务队列并发提交 | FIFO 顺序执行 |

---

## 10. 容错测试（6 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| FAULT-001 | Agent 响应超时（>30s） | 自动重试，最多 3 次 |
| FAULT-002 | Agent 返回错误 | 降级处理，不中断流程 |
| FAULT-003 | 网络断开 5s 后恢复 | 自动重连，状态恢复 |
| FAULT-004 | 浏览器刷新/关闭 | 会话状态可恢复 |
| FAULT-005 | 运算任务失败 | 显示错误原因，提供重试选项 |
| FAULT-006 | 存储写入失败 | 本地缓存兜底，后台重试 |

---

## 11. 稳定性测试（3 个用例）

| ID | 场景 | 预期结果 |
|----|------|---------|
| STAB-001 | 连续运行 10 Round | 内存无泄漏，性能无衰减 |
| STAB-002 | 24 小时无操作后恢复 | 会话仍可继续 |
| STAB-003 | 累计 1000+ 结论卡 | 系统响应正常 |

---

## 12. 兼容性测试（4 个用例）

| ID | 场景 | 覆盖范围 |
|----|------|---------|
| COMPAT-001 | 浏览器兼容 | Chrome/Firefox/Safari/Edge 最新版 |
| COMPAT-002 | 分辨率适配 | 1280x720, 1920x1080, 2560x1440 |
| COMPAT-003 | 移动端响应式 | iOS Safari, Android Chrome |
| COMPAT-004 | 深色/浅色主题 | 两种主题下 UI 正常 |

---

## 13. 测试环境要求

### 13.1 环境配置

| 环境 | 用途 | 配置要求 |
|-----|------|---------|
| DEV | 开发自测 | 单机，Mock Agent |
| QA | 集成测试 | 真实 Agent，隔离数据 |
| STAGING | 预发布验证 | 生产同配置 |
| PROD | 线上 | 高可用部署 |

### 13.2 前置条件

- [ ] 所有 Agent 服务已部署并健康
- [ ] WebSocket 服务已启动
- [ ] 测试账号已创建（至少 10 个）
- [ ] 测试数据已初始化
- [ ] 外部依赖（LLM API）可用

---

## 14. 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| LLM API 不稳定 | 高 | 中 | Mock 降级方案 |
| Agent 响应时间长 | 中 | 高 | 设置超时 + 进度反馈 |
| 多 Agent 数据冲突 | 高 | 低 | 乐观锁 + 冲突检测 |
| 长会话内存泄漏 | 高 | 中 | 定期内存快照监控 |

---

## 15. 验收标准

### 15.1 功能验收

- [ ] P0 用例 100% 通过
- [ ] P1 用例 ≥ 95% 通过
- [ ] P2 用例 ≥ 90% 通过
- [ ] Security 用例 100% 通过

### 15.2 性能验收

- [ ] 研究简报生成 P95 < 5s
- [ ] 单 Round P95 < 60s
- [ ] WebSocket 延迟 P99 < 200ms

### 15.3 稳定性验收

- [ ] 连续 10 Round 无崩溃
- [ ] 24 小时无内存泄漏

---

## 16. 测试排期建议

| 阶段 | 测试类型 | 预估工时 |
|-----|---------|---------|
| Sprint 1 | P0 功能 + 冒烟 | 3 人天 |
| Sprint 2 | P1 功能 + 安全 | 5 人天 |
| Sprint 3 | P2 + 性能 + 并发 | 4 人天 |
| Sprint 4 | 容错 + 稳定性 + 回归 | 4 人天 |
| **Total** | - | **16 人天** |

---

## 17. 更新后的测试统计

| 优先级 | 数量 | 占比 |
|-------|------|------|
| P0 | 8 | 12% |
| P1 | 24 | 36% |
| P2 | 5 | 8% |
| Security | 5 | 8% |
| Performance | 6 | 9% |
| Concurrency | 4 | 6% |
| Fault Tolerance | 6 | 9% |
| Stability | 3 | 5% |
| Compatibility | 4 | 6% |
| **Total** | **65** | 100% |

---

*Generated: 2026-01-09*
*Updated: 2026-01-09 (增加性能/并发/容错/稳定性/兼容性测试)*

