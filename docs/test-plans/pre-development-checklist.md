# 多轮研究 Agent 系统 - 开发阶段测试准备清单

> 作为测试开发工程师，在系统开发阶段可以提前准备的工作

---

## 核心原则

**提前介入，而非被动等待**。测试不是开发完成后的验证，而是与开发并行的质量保障。

---

## 一、Mock 与测试数据基础设施（P0）

### 1.1 Agent 响应 Mock 框架

**目标**：在真实 Agent 未完成时，提供可配置的 Mock 响应

**实现路径**：

```python
# tests/research_agent/mocks/agent_mock_factory.py
"""
Agent 响应 Mock 工厂
支持按场景、按 Agent 类型、按轮次生成不同的 Mock 响应
"""

from typing import Dict, List, Optional
from enum import Enum


class AgentType(Enum):
    """Agent 类型枚举"""
    PLANNER = "planner"
    LIBRARIAN = "librarian"
    REASONER = "reasoner"
    VERIFIER = "verifier"
    COMPUTE = "compute"
    RA = "research_controller"


class AgentMockFactory:
    """Agent Mock 工厂"""
    
    def __init__(self):
        self._scenarios: Dict[str, Dict[AgentType, Dict]] = {}
        self._load_default_scenarios()
    
    def _load_default_scenarios(self):
        """加载默认场景"""
        # 正常流程场景
        self._scenarios["normal"] = {
            AgentType.PLANNER: {
                "response_time": 2.0,  # 秒
                "output": {
                    "plan": "本轮计划：1) 收集文献 2) 分析数据 3) 生成结论",
                    "milestones": ["文献收集完成", "数据分析完成", "结论生成完成"],
                    "estimated_time": 300  # 秒
                }
            },
            AgentType.LIBRARIAN: {
                "response_time": 3.0,
                "output": {
                    "evidence_count": 10,
                    "evidence_list": [
                        {"title": "文献A", "relevance": 0.9, "url": "https://..."},
                        # ...
                    ],
                    "conflicts": [],
                    "gaps": ["缺少实验数据"]
                }
            },
            AgentType.REASONER: {
                "response_time": 4.0,
                "output": {
                    "conclusions": [
                        {
                            "id": "C001",
                            "content": "多 Agent 协作提升效率 45%",
                            "confidence": 0.85,
                            "evidence_ids": ["E001", "E002"]
                        }
                    ],
                    "assumptions": ["假设1", "假设2"],
                    "impact_analysis": "..."
                }
            },
            AgentType.VERIFIER: {
                "response_time": 1.0,
                "output": {
                    "needs_compute": False,
                    "verification_result": "通过",
                    "risk_level": "low",
                    "suggestions": []
                }
            }
        }
        
        # 需要程序运算场景
        self._scenarios["needs_compute"] = {
            AgentType.VERIFIER: {
                "response_time": 1.5,
                "output": {
                    "needs_compute": True,
                    "compute_request": {
                        "type": "data_analysis",
                        "description": "需要分析 1000 条数据",
                        "cost_level": "medium",
                        "risk_level": "medium",
                        "estimated_time": 600,
                        "alternative_path": "可以跳过，但结论可信度降低 20%"
                    }
                }
            }
        }
        
        # 错误场景
        self._scenarios["agent_timeout"] = {
            AgentType.PLANNER: {
                "response_time": 35.0,  # 超时
                "error": "timeout",
                "retry_count": 3
            }
        }
    
    def get_mock_response(
        self,
        agent_type: AgentType,
        scenario: str = "normal",
        round_number: int = 1
    ) -> Dict:
        """
        获取 Mock 响应
        
        Args:
            agent_type: Agent 类型
            scenario: 场景名称
            round_number: 轮次（可用于调整响应内容）
        
        Returns:
            Mock 响应数据
        """
        scenario_data = self._scenarios.get(scenario, self._scenarios["normal"])
        agent_data = scenario_data.get(agent_type, {})
        
        # 根据轮次调整响应（例如：后续轮次结论更详细）
        response = agent_data.get("output", {}).copy()
        if round_number > 1:
            response = self._adjust_for_round(response, round_number)
        
        return {
            "agent_type": agent_type.value,
            "round": round_number,
            "response_time": agent_data.get("response_time", 1.0),
            "data": response,
            "error": agent_data.get("error"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _adjust_for_round(self, response: Dict, round_number: int) -> Dict:
        """根据轮次调整响应内容"""
        # 例如：后续轮次结论更详细
        if "conclusions" in response:
            for conclusion in response["conclusions"]:
                conclusion["detail_level"] = min(round_number * 0.2, 1.0)
        return response


# ============================================================
# Fixture 集成
# ============================================================

@pytest.fixture
def agent_mock_factory() -> AgentMockFactory:
    """Agent Mock 工厂 Fixture"""
    return AgentMockFactory()


@pytest.fixture
def mock_agent_responses(agent_mock_factory, request):
    """
    根据测试标记返回不同的 Mock 响应
    
    使用方式：
        @pytest.mark.agent_scenario("needs_compute")
        def test_with_compute(mock_agent_responses):
            ...
    """
    scenario = request.node.get_closest_marker("agent_scenario")
    scenario_name = scenario.args[0] if scenario else "normal"
    
    def _get_response(agent_type: AgentType, round_num: int = 1):
        return agent_mock_factory.get_mock_response(
            agent_type, scenario_name, round_num
        )
    
    return _get_response
```

**使用示例**：

```python
@pytest.mark.agent_scenario("normal")
def test_round_1_parallel_agents(mock_agent_responses):
    """测试 Round 1 并行 Agent 工作"""
    planner_resp = mock_agent_responses(AgentType.PLANNER, round_num=1)
    librarian_resp = mock_agent_responses(AgentType.LIBRARIAN, round_num=1)
    
    assert planner_resp["data"]["plan"] is not None
    assert librarian_resp["data"]["evidence_count"] > 0
```

### 1.2 测试数据生成器

**目标**：生成符合不同场景的测试数据

```python
# tests/research_agent/generators/test_data_generator.py
"""
测试数据生成器
生成研究方向、约束条件、预期输出等测试数据
"""

from dataclasses import dataclass
from typing import List, Optional
import random


@dataclass
class ResearchDirection:
    """研究方向数据类"""
    direction: str
    constraints: Dict[str, any]
    expected_briefing_elements: List[str]
    expected_rounds: int  # 预期轮次


class TestDataGenerator:
    """测试数据生成器"""
    
    # 预定义研究方向模板
    DIRECTION_TEMPLATES = [
        {
            "direction": "研究{domain}在{field}领域的最新进展",
            "domains": ["大语言模型", "多模态AI", "强化学习"],
            "fields": ["代码生成", "科研辅助", "教育应用"],
            "expected_elements": ["问题改写", "假设清单", "风险清单", "里程碑"],
            "expected_rounds": 3
        },
        # ... 更多模板
    ]
    
    def generate_direction(
        self,
        template_id: int = 0,
        custom_domain: Optional[str] = None,
        custom_field: Optional[str] = None
    ) -> ResearchDirection:
        """生成研究方向"""
        template = self.DIRECTION_TEMPLATES[template_id]
        
        domain = custom_domain or random.choice(template["domains"])
        field = custom_field or random.choice(template["fields"])
        direction = template["direction"].format(domain=domain, field=field)
        
        return ResearchDirection(
            direction=direction,
            constraints={
                "budget": random.choice(["low", "medium", "high"]),
                "speed": random.choice(["fast", "normal", "thorough"]),
                "rigor": random.choice(["low", "medium", "high"]),
                "forbidden": []
            },
            expected_briefing_elements=template["expected_elements"],
            expected_rounds=template["expected_rounds"]
        )
    
    def generate_edge_cases(self) -> List[ResearchDirection]:
        """生成边界测试数据"""
        return [
            ResearchDirection(
                direction="",  # 空方向
                constraints={},
                expected_briefing_elements=[],
                expected_rounds=0
            ),
            ResearchDirection(
                direction="A" * 2000,  # 超长方向
                constraints={},
                expected_briefing_elements=[],
                expected_rounds=0
            ),
            # ... 更多边界情况
        ]
```

---

## 二、测试基础设施扩展（P0）

### 2.1 WebSocket 测试支持

**目标**：支持实时状态更新的测试

```python
# tests/research_agent/fixtures/websocket_fixture.py
"""
WebSocket 测试 Fixture
用于测试实时状态更新、Agent 进度推送等
"""

import pytest
from playwright.async_api import Page, WebSocket
from typing import AsyncGenerator, List, Dict
import json


@pytest.fixture
async def websocket_monitor(page: Page) -> AsyncGenerator[Dict, None]:
    """
    WebSocket 消息监控 Fixture
    
    使用方式：
        async def test_agent_progress(websocket_monitor):
            # 触发 Agent 工作
            await page.click("[data-testid='start-research']")
            
            # 等待 WebSocket 消息
            messages = await websocket_monitor.wait_for_messages(
                count=3,  # 等待 3 条消息
                timeout=10.0
            )
            
            # 验证消息内容
            assert messages[0]["type"] == "agent_status"
    """
    messages: List[Dict] = []
    
    async def handle_websocket(ws: WebSocket):
        async for msg in ws:
            if msg.type == "text":
                data = json.loads(msg.text)
                messages.append(data)
    
    # 监听 WebSocket 连接
    async with page.expect_websocket() as ws_info:
        # 这里需要根据实际 WebSocket 连接时机调整
        pass
    
    ws = await ws_info.value
    ws.on("framereceived", lambda frame: handle_websocket(ws))
    
    class WebSocketMonitor:
        async def wait_for_messages(
            self,
            count: int = 1,
            timeout: float = 5.0
        ) -> List[Dict]:
            """等待指定数量的消息"""
            import asyncio
            start_time = asyncio.get_event_loop().time()
            
            while len(messages) < count:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"等待 {count} 条消息超时，实际收到 {len(messages)} 条")
                await asyncio.sleep(0.1)
            
            return messages[:count]
        
        def get_messages(self) -> List[Dict]:
            """获取所有已收到的消息"""
            return messages.copy()
        
        def clear(self):
            """清空消息缓存"""
            messages.clear()
    
    yield WebSocketMonitor()
```

### 2.2 长时间运行测试支持

**目标**：支持多轮迭代、长时间运行的测试

```python
# tests/research_agent/fixtures/long_running_fixture.py
"""
长时间运行测试支持
包括：状态快照、断点续传、资源监控
"""

import pytest
from typing import Dict, Optional
import time
import psutil
import os


@pytest.fixture
def research_session_snapshot(request, tmp_path):
    """
    研究会话快照 Fixture
    支持测试中断后恢复
    """
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    
    class SessionSnapshot:
        def __init__(self, session_id: str):
            self.session_id = session_id
            self.snapshot_file = snapshot_dir / f"{session_id}.json"
            self.checkpoints: List[Dict] = []
        
        def save_checkpoint(self, round_number: int, state: Dict):
            """保存检查点"""
            checkpoint = {
                "round": round_number,
                "timestamp": time.time(),
                "state": state
            }
            self.checkpoints.append(checkpoint)
            
            # 写入文件
            import json
            with open(self.snapshot_file, "w") as f:
                json.dump(self.checkpoints, f, indent=2)
        
        def load_checkpoint(self, round_number: int) -> Optional[Dict]:
            """加载检查点"""
            for checkpoint in self.checkpoints:
                if checkpoint["round"] == round_number:
                    return checkpoint["state"]
            return None
    
    yield SessionSnapshot
    
    # 清理
    if snapshot_dir.exists():
        import shutil
        shutil.rmtree(snapshot_dir)


@pytest.fixture
def resource_monitor():
    """
    资源监控 Fixture
    监控内存、CPU 使用，检测内存泄漏
    """
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    class ResourceMonitor:
        def get_memory_usage(self) -> float:
            """获取当前内存使用（MB）"""
            return process.memory_info().rss / 1024 / 1024
        
        def get_memory_increase(self) -> float:
            """获取内存增长（MB）"""
            return self.get_memory_usage() - initial_memory
        
        def check_memory_leak(self, threshold: float = 100.0) -> bool:
            """检查是否有内存泄漏（增长超过阈值）"""
            return self.get_memory_increase() > threshold
    
    yield ResourceMonitor()
```

---

## 三、验收标准定义（P0）

### 3.1 AI 输出质量验收标准

**目标**：定义每个阶段 AI 输出的质量要求

```python
# tests/research_agent/acceptance_criteria.py
"""
验收标准定义
每个阶段 AI 输出的质量要求
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from eval import EvalPipeline


@dataclass
class BriefingAcceptanceCriteria:
    """研究简报验收标准"""
    min_score: float = 0.7  # 最低得分
    required_elements: List[str] = None  # 必需元素
    min_length: int = 500  # 最小长度
    max_length: int = 2000  # 最大长度
    
    def __post_init__(self):
        if self.required_elements is None:
            self.required_elements = [
                "问题改写",
                "假设清单",
                "风险清单",
                "里程碑路线图"
            ]


@dataclass
class ConclusionCardAcceptanceCriteria:
    """结论卡验收标准"""
    min_confidence: float = 0.6  # 最低可信度
    required_fields: List[str] = None
    min_evidence_count: int = 2  # 最少证据数量
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = [
                "结论内容",
                "可信度",
                "证据链接"
            ]


class AcceptanceChecker:
    """验收检查器"""
    
    def __init__(self, eval_pipeline: EvalPipeline):
        self.eval_pipeline = eval_pipeline
    
    def check_briefing(
        self,
        briefing: str,
        criteria: Optional[BriefingAcceptanceCriteria] = None
    ) -> Dict[str, any]:
        """
        检查研究简报是否满足验收标准
        
        Returns:
            {
                "passed": bool,
                "score": float,
                "missing_elements": List[str],
                "violations": List[str]
            }
        """
        criteria = criteria or BriefingAcceptanceCriteria()
        
        # 使用 Eval 框架评估
        eval_result = self.eval_pipeline.run(
            briefing,
            context="研究简报验收检查"
        )
        
        # 检查必需元素
        missing_elements = []
        for element in criteria.required_elements:
            if element not in briefing:
                missing_elements.append(element)
        
        # 检查长度
        violations = []
        if len(briefing) < criteria.min_length:
            violations.append(f"长度不足：{len(briefing)} < {criteria.min_length}")
        if len(briefing) > criteria.max_length:
            violations.append(f"长度超限：{len(briefing)} > {criteria.max_length}")
        
        # 综合判断
        passed = (
            eval_result["overall_passed"] and
            eval_result["overall_score"] >= criteria.min_score and
            len(missing_elements) == 0 and
            len(violations) == 0
        )
        
        return {
            "passed": passed,
            "score": eval_result["overall_score"],
            "missing_elements": missing_elements,
            "violations": violations,
            "eval_result": eval_result
        }
    
    def check_conclusion_card(
        self,
        conclusion_card: str,
        criteria: Optional[ConclusionCardAcceptanceCriteria] = None
    ) -> Dict[str, any]:
        """检查结论卡是否满足验收标准"""
        # 类似实现
        pass


# ============================================================
# Fixture 集成
# ============================================================

@pytest.fixture
def acceptance_checker(eval_pipeline) -> AcceptanceChecker:
    """验收检查器 Fixture"""
    return AcceptanceChecker(eval_pipeline)


@pytest.fixture
def briefing_criteria() -> BriefingAcceptanceCriteria:
    """研究简报验收标准 Fixture"""
    return BriefingAcceptanceCriteria()


# ============================================================
# 使用示例
# ============================================================

def test_briefing_meets_acceptance_criteria(
    acceptance_checker,
    briefing_criteria,
    mock_research_briefing
):
    """测试研究简报满足验收标准"""
    result = acceptance_checker.check_briefing(
        mock_research_briefing,
        briefing_criteria
    )
    
    assert result["passed"], f"""
    研究简报未满足验收标准：
    - 得分: {result['score']}
    - 缺失元素: {result['missing_elements']}
    - 违规项: {result['violations']}
    """
```

---

## 四、可观测性设计（P1）

### 4.1 测试执行日志与追踪

**目标**：记录测试执行过程中的关键事件，便于调试

```python
# tests/research_agent/observability/test_tracer.py
"""
测试执行追踪器
记录测试过程中的关键事件，生成可观测性报告
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class TestTracer:
    """测试追踪器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.events: List[Dict] = []
        self.start_time = datetime.now()
    
    def log_event(
        self,
        event_type: str,
        description: str,
        data: Optional[Dict] = None
    ):
        """记录事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,  # agent_start, agent_complete, user_action, etc.
            "description": description,
            "data": data or {}
        }
        self.events.append(event)
    
    def log_agent_start(self, agent_type: str, round_number: int):
        """记录 Agent 启动"""
        self.log_event(
            "agent_start",
            f"{agent_type} 在 Round {round_number} 启动",
            {"agent_type": agent_type, "round": round_number}
        )
    
    def log_agent_complete(
        self,
        agent_type: str,
        round_number: int,
        duration: float,
        output_summary: str
    ):
        """记录 Agent 完成"""
        self.log_event(
            "agent_complete",
            f"{agent_type} 在 Round {round_number} 完成",
            {
                "agent_type": agent_type,
                "round": round_number,
                "duration": duration,
                "output_summary": output_summary
            }
        )
    
    def log_user_action(self, action: str, details: Dict):
        """记录用户操作"""
        self.log_event(
            "user_action",
            f"用户操作: {action}",
            details
        )
    
    def generate_report(self) -> Dict:
        """生成追踪报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # 统计 Agent 执行时间
        agent_times = {}
        for event in self.events:
            if event["type"] == "agent_complete":
                agent_type = event["data"]["agent_type"]
                if agent_type not in agent_times:
                    agent_times[agent_type] = []
                agent_times[agent_type].append(event["data"]["duration"])
        
        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "total_events": len(self.events),
            "agent_statistics": {
                agent: {
                    "count": len(times),
                    "avg_duration": sum(times) / len(times),
                    "total_duration": sum(times)
                }
                for agent, times in agent_times.items()
            },
            "events": self.events
        }
    
    def save_report(self, filepath: str):
        """保存报告到文件"""
        report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


# ============================================================
# Fixture 集成
# ============================================================

@pytest.fixture
def test_tracer(request) -> TestTracer:
    """测试追踪器 Fixture"""
    test_name = request.node.name
    tracer = TestTracer(test_name)
    
    yield tracer
    
    # 测试结束后保存报告
    report_dir = request.config.getoption("--trace-report-dir", default="trace-reports")
    import os
    os.makedirs(report_dir, exist_ok=True)
    tracer.save_report(f"{report_dir}/{test_name}.json")
```

---

## 五、测试工具开发（P1）

### 5.1 测试场景生成器

**目标**：根据需求文档自动生成测试场景

```python
# tests/research_agent/tools/scenario_generator.py
"""
测试场景生成器
根据需求文档生成测试场景
"""

from typing import List, Dict
import re


class ScenarioGenerator:
    """测试场景生成器"""
    
    def parse_requirements_to_scenarios(self, requirements_content: str) -> List[Dict]:
        """
        解析需求文档内容，生成测试场景
        
        Args:
            requirements_content: 需求文档的 Markdown 内容
        
        Returns:
            测试场景列表
        """
        scenarios = []
        
        # 解析用户输入阶段
        input_scenarios = self._parse_input_phase(requirements_content)
        scenarios.extend(input_scenarios)
        
        # 解析研究简报阶段
        briefing_scenarios = self._parse_briefing_phase(requirements_content)
        scenarios.extend(briefing_scenarios)
        
        # 解析并行调研阶段
        research_scenarios = self._parse_research_phase(requirements_content)
        scenarios.extend(research_scenarios)
        
        # ... 更多阶段
        
        return scenarios
    
    def _parse_input_phase(self, content: str) -> List[Dict]:
        """解析输入阶段场景"""
        scenarios = []
        
        # 匹配"用户输入方向"相关描述
        pattern = r"用户输入.*?方向"
        matches = re.findall(pattern, content)
        
        for match in matches:
            scenarios.append({
                "phase": "input",
                "description": match,
                "test_id": "P0-001",
                "expected": "系统返回研究简报"
            })
        
        return scenarios
```

### 5.2 测试覆盖率分析工具

**目标**：分析测试用例对需求的覆盖情况

```python
# tests/research_agent/tools/coverage_analyzer.py
"""
测试覆盖率分析器
分析测试用例对需求的覆盖情况
"""

from typing import Dict, List, Set
from pathlib import Path


class CoverageAnalyzer:
    """覆盖率分析器"""
    
    def __init__(self, test_plan_path: str):
        """
        Args:
            test_plan_path: 测试计划文档路径
        """
        self.test_plan_path = Path(test_plan_path)
        self.requirements: Dict[str, List[str]] = {}  # 需求ID -> 测试用例ID列表
        self._load_test_plan()
    
    def _load_test_plan(self):
        """加载测试计划，提取需求映射"""
        # 解析测试计划文档，提取需求ID和测试用例ID的映射
        # 这里需要根据实际文档格式实现
        pass
    
    def analyze_coverage(
        self,
        test_files: List[str]
    ) -> Dict[str, any]:
        """
        分析测试覆盖率
        
        Args:
            test_files: 测试文件路径列表
        
        Returns:
            覆盖率报告
        """
        # 提取测试文件中的测试用例ID
        test_case_ids = self._extract_test_case_ids(test_files)
        
        # 计算覆盖率
        total_requirements = len(self.requirements)
        covered_requirements = sum(
            1 for req_id, test_ids in self.requirements.items()
            if any(tid in test_case_ids for tid in test_ids)
        )
        
        coverage_rate = covered_requirements / total_requirements if total_requirements > 0 else 0
        
        return {
            "total_requirements": total_requirements,
            "covered_requirements": covered_requirements,
            "coverage_rate": coverage_rate,
            "missing_requirements": [
                req_id for req_id in self.requirements.keys()
                if not any(tid in test_case_ids for tid in self.requirements[req_id])
            ]
        }
```

---

## 六、集成测试框架（P1）

### 6.1 端到端测试脚手架

**目标**：提供端到端测试的基础框架

```python
# tests/research_agent/e2e/research_workflow_test.py
"""
端到端测试：完整研究流程
"""

import pytest
from pages.research_input_page import ResearchInputPage
from pages.briefing_page import BriefingPage
from pages.progress_panel import ProgressPanel
from pages.delivery_center_page import DeliveryCenterPage


class TestResearchWorkflow:
    """完整研究流程测试"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_research_workflow(
        self,
        page,
        test_account,
        mock_agent_responses,
        acceptance_checker,
        test_tracer
    ):
        """
        测试完整研究流程：输入 → 简报 → 多轮迭代 → 交付
        
        这是一个端到端测试，验证整个系统的协作
        """
        # ========== 阶段 1: 输入方向 ==========
        test_tracer.log_user_action("输入研究方向", {
            "direction": "研究多 Agent 协作架构"
        })
        
        input_page = ResearchInputPage(page)
        input_page.navigate()
        input_page.input_direction("研究多 Agent 协作架构")
        input_page.set_constraints({
            "budget": "medium",
            "speed": "normal"
        })
        input_page.click_start()
        
        # ========== 阶段 2: 研究简报 ==========
        briefing_page = BriefingPage(page)
        briefing_page.wait_for_briefing()
        
        briefing_content = briefing_page.get_briefing_content()
        
        # 验收检查
        briefing_result = acceptance_checker.check_briefing(briefing_content)
        assert briefing_result["passed"], f"研究简报未满足验收标准: {briefing_result}"
        
        test_tracer.log_event(
            "briefing_generated",
            "研究简报生成完成",
            {"score": briefing_result["score"]}
        )
        
        # ========== 阶段 3: 进入 Round 1 ==========
        briefing_page.click_continue()
        
        progress_panel = ProgressPanel(page)
        
        # 等待 Agent 并行工作
        test_tracer.log_agent_start("PLANNER", round_number=1)
        test_tracer.log_agent_start("LIBRARIAN", round_number=1)
        test_tracer.log_agent_start("REASONER", round_number=1)
        
        # 验证 Agent 状态
        agent_statuses = progress_panel.get_agent_statuses()
        assert "PLANNER" in agent_statuses
        assert "LIBRARIAN" in agent_statuses
        assert "REASONER" in agent_statuses
        
        # 等待 Round 1 完成
        progress_panel.wait_for_round_complete(round_number=1, timeout=60)
        
        # ========== 阶段 4: 检查交付物 ==========
        delivery_center = DeliveryCenterPage(page)
        delivery_center.navigate()
        
        # 验证交付物更新
        conclusions = delivery_center.get_conclusions()
        assert len(conclusions) > 0, "应该有结论生成"
        
        paper_draft = delivery_center.get_paper_draft()
        assert len(paper_draft) > 0, "应该有论文草稿"
        
        # ========== 阶段 5: 多轮迭代 ==========
        for round_num in range(2, 4):  # Round 2, 3
            test_tracer.log_event(
                "round_start",
                f"Round {round_num} 开始",
                {"round": round_num}
            )
            
            # 继续下一轮
            delivery_center.click_continue_next_round()
            
            # 等待完成
            progress_panel.wait_for_round_complete(round_number=round_num, timeout=60)
            
            # 验证交付物更新
            new_conclusions = delivery_center.get_conclusions()
            assert len(new_conclusions) >= len(conclusions), "结论应该增加"
        
        # ========== 最终验证 ==========
        final_paper = delivery_center.get_paper_draft()
        
        # 使用 Eval 框架评估最终论文质量
        from eval import full_eval
        final_eval = full_eval(final_paper, context="多轮研究流程")
        
        assert final_eval["overall_passed"], f"""
        最终论文质量未达标：
        - 得分: {final_eval['overall_score']}
        - 建议: {final_eval.get('llm_eval', {}).get('suggestions', [])}
        """
        
        # 生成追踪报告
        report = test_tracer.generate_report()
        assert report["duration"] < 300, "完整流程应在 5 分钟内完成"
```

---

## 七、优先级与排期建议

### 立即开始（本周）

1. ✅ **Agent Mock 框架**（1-2 天）
   - 实现 `AgentMockFactory`
   - 创建基础 Mock 数据
   - 集成到 Fixtures

2. ✅ **测试数据生成器**（1 天）
   - 实现 `TestDataGenerator`
   - 生成边界测试数据

3. ✅ **验收标准定义**（1 天）
   - 定义各阶段验收标准
   - 实现 `AcceptanceChecker`

### 第一周完成

4. ✅ **WebSocket 测试支持**（1-2 天）
   - 实现 `websocket_monitor` Fixture
   - 测试实时状态更新

5. ✅ **端到端测试脚手架**（2 天）
   - 实现基础 E2E 测试框架
   - 编写第一个完整流程测试

### 第二周完成

6. ✅ **可观测性设计**（2 天）
   - 实现 `TestTracer`
   - 集成到测试框架

7. ✅ **测试工具开发**（2 天）
   - 场景生成器
   - 覆盖率分析器

---

## 八、与开发团队的协作建议

### 8.1 接口契约定义

**建议**：在开发开始前，与开发团队共同定义 Agent 接口契约

```python
# tests/research_agent/contracts/agent_contracts.py
"""
Agent 接口契约定义
测试和开发共同遵守的接口规范
"""

from typing import Protocol, Dict, List
from dataclasses import dataclass


@dataclass
class PlannerResponse:
    """Planner Agent 响应契约"""
    plan: str
    milestones: List[str]
    estimated_time: int  # 秒


@dataclass
class LibrarianResponse:
    """Librarian Agent 响应契约"""
    evidence_count: int
    evidence_list: List[Dict]
    conflicts: List[str]
    gaps: List[str]


# 使用 Protocol 定义接口
class PlannerAgent(Protocol):
    """Planner Agent 接口协议"""
    def generate_plan(self, direction: str, constraints: Dict) -> PlannerResponse:
        """生成研究计划"""
        ...
```

### 8.2 测试驱动开发（TDD）

**建议**：在开发 Agent 前，先编写测试用例

```python
# tests/research_agent/tdd/test_planner_agent.py
"""
Planner Agent TDD 测试
在开发前定义期望行为
"""

import pytest
from tests.research_agent.contracts.agent_contracts import PlannerResponse


class TestPlannerAgent:
    """Planner Agent 测试（TDD）"""
    
    def test_generate_plan_should_return_valid_response(self, planner_agent):
        """测试生成计划应返回有效响应"""
        direction = "研究多 Agent 协作"
        constraints = {"budget": "medium"}
        
        response = planner_agent.generate_plan(direction, constraints)
        
        assert isinstance(response, PlannerResponse)
        assert response.plan is not None
        assert len(response.milestones) > 0
        assert response.estimated_time > 0
```

---

## 九、总结

作为测试开发工程师，在系统开发阶段可以提前准备：

1. **Mock 基础设施**：让测试不依赖真实 Agent
2. **测试数据生成**：覆盖各种场景和边界情况
3. **验收标准定义**：明确质量要求
4. **测试框架扩展**：支持 WebSocket、长时间运行等
5. **可观测性设计**：便于调试和问题定位
6. **工具开发**：提升测试效率

**核心价值**：**提前介入，而非被动等待**。测试不是开发完成后的验证，而是与开发并行的质量保障。

---

## 相关文档

- [需求文档](../requirements/multi-round-research-agent-requirements.md) - 系统完整需求规格说明
- [测试计划](./multi-round-research-agent.md) - 详细测试用例和测试策略

---

*Generated: 2026-01-12*  
*基于需求文档和现有测试框架*

