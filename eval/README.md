# Eval 框架 - AI 输出质量评估

适用于 **Vibe Research** 等 AI 研究系统的输出质量评估框架。

## 核心特性

| 功能 | 说明 | 成本 |
|-----|------|------|
| **规则检查** | 结构、内容、质量 10 项快速检查 | 免费 |
| **LLM 评估** | 逻辑、证据、准确性、完整性、洞察力 5 维深度评估 | 付费 |
| **理论验证** | 专门验证推理/结论的正确性 | 付费 |
| **Pipeline** | 规则预检 + LLM 深度评估组合 | 混合 |

---

## 快速开始

### 1. 安装依赖

```bash
pip install openai  # LLM 评估需要
```

### 2. 配置 API Key

```bash
# 推荐 DeepSeek（性价比之王）
export EVAL_LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-your-key
```

详细配置见 [CONFIG_GUIDE.md](CONFIG_GUIDE.md)

### 3. 使用

```python
# 快速检查（免费）
from eval import is_quality_ok

if is_quality_ok(ai_output):
    print("基本合格 ✅")

# 完整评估（规则 + LLM）
from eval import full_eval

result = full_eval(ai_output, context="研究方向")
print(f"得分: {result['overall_score']}")
```

---

## 使用场景

### 场景 1：开发调试（只用规则，免费）

```python
from eval import quick_eval

result = quick_eval(ai_output)
if not result["passed"]:
    print("问题:", result["failed_checks"])
```

### 场景 2：CI/CD 测试（规则 + LLM）

```python
from eval import EvalPipeline

pipeline = EvalPipeline()
result = pipeline.run(ai_output, context="研究方向")

assert result["overall_passed"], f"Eval 失败: {result}"
```

### 场景 3：理论正确性验证（Vibe Research 专用）

```python
from eval import LLMEvaluator

evaluator = LLMEvaluator()
result = evaluator.evaluate_theory(
    theory="AI 推导出的结论",
    premises=["前提条件 1", "前提条件 2"],
    expected_conclusion="预期结论（可选）"
)

if result["passed"]:
    print("推理正确 ✅")
else:
    print("推理有问题:", result["suggestions"])
```

### 场景 4：批量评估

```python
from eval import EvalPipeline

pipeline = EvalPipeline()
report = pipeline.run_batch([
    {"text": output1, "context": "问题 1"},
    {"text": output2, "context": "问题 2"},
])

print(f"通过率: {report['pass_rate']}")
print(f"平均分: {report['avg_score']}")
pipeline.save_report(report, "eval_report.json")
```

---

## 评估维度

### 规则检查（10 项）

| 类别 | 检查项 | 说明 |
|-----|--------|------|
| 结构 | has_titles | 是否有标题层级 |
| 结构 | has_sections | 是否有必要章节 |
| 结构 | paragraph_structure | 段落结构是否合理 |
| 内容 | min_length | 是否达到最小长度 |
| 内容 | has_evidence | 是否有证据支撑 |
| 内容 | has_data | 是否有数据 |
| 内容 | no_placeholder | 是否无占位符 |
| 质量 | no_repetition | 是否无重复 |
| 质量 | readability | 可读性是否良好 |
| 质量 | terminology | 专业术语覆盖 |

### LLM 评估（5 维）

| 维度 | 权重 | 说明 |
|-----|------|------|
| **逻辑** (logic) | 25% | 推理链是否严密，论证是否自洽 |
| **证据** (evidence) | 25% | 结论是否有充分证据支撑 |
| **准确** (accuracy) | 20% | 陈述的事实是否正确 |
| **完整** (completeness) | 15% | 是否涵盖关键方面 |
| **洞察** (insight) | 15% | 是否有深度分析和独到见解 |

---

## 文件结构

```
eval/
├── __init__.py         # 包入口，导出所有公共 API
├── config.py           # 配置管理（支持多 LLM 提供商）
├── checkers.py         # 规则检查器实现
├── rule_evaluator.py   # 纯规则评估器
├── llm_evaluator.py    # LLM 深度评估器
├── pipeline.py         # 完整评估流水线
├── CONFIG_GUIDE.md     # 配置指南
└── README.md           # 本文档
```

---

## 成本估算

假设每次评估 2000 tokens：

| 提供商 | 100 次/天 | 月成本 |
|-------|----------|--------|
| DeepSeek | ¥0.2 | ¥6 |
| 智谱 GLM-4-Flash | ¥0.02 | ¥0.6 |
| OpenAI GPT-4o-mini | ¥2 | ¥60 |
| Ollama 本地 | 免费 | ¥0 |

---

## 集成到 Pytest

```python
# conftest.py
import pytest
from eval import EvalPipeline

@pytest.fixture
def eval_pipeline():
    return EvalPipeline()

# test_research.py
def test_ai_output_quality(eval_pipeline, ai_output):
    result = eval_pipeline.run(ai_output, context="研究方向")
    
    assert result["overall_passed"], f"""
    Eval 失败！
    得分: {result['overall_score']}
    规则检查: {result['rule_check']}
    LLM 评估: {result['llm_eval']}
    """
```

---

## FAQ

**Q: 不配置 API Key 能用吗？**

A: 可以！只用规则检查：

```python
from eval import is_quality_ok
is_quality_ok(text)  # 不需要 API Key
```

**Q: 哪个 LLM 最划算？**

A: DeepSeek，¥0.001/千 tokens，能力接近 GPT-4。

**Q: 本地跑免费吗？**

A: 用 Ollama 完全免费，但需要 GPU：

```bash
ollama pull qwen2.5:7b
export EVAL_LLM_PROVIDER=ollama
```
