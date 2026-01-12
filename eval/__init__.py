"""
Eval 框架 - AI 输出质量评估

支持两种评估模式：
1. 纯规则检查（免费、快速）
2. LLM 深度评估（需要 API Key，能评估理论正确性）

快速使用：
    # 纯规则检查
    from eval import is_quality_ok, quick_eval
    
    if is_quality_ok(ai_output):
        print("基本合格")
    
    # 完整评估（规则 + LLM）
    from eval import full_eval
    
    result = full_eval(ai_output, context="研究方向")

Pytest 集成：
    # conftest.py
    pytest_plugins = ["eval.pytest_plugin"]
    
    # test_xxx.py
    def test_ai_output(eval_pipeline, eval_assert):
        result = eval_pipeline.run(ai_output)
        eval_assert.passed(result)
"""

# 纯规则评估（免费）
from .rule_evaluator import RuleEvaluator, quick_eval, is_quality_ok

# 配置
from .config import EvalConfig, LLMProvider, get_default_config

# LLM 评估（需要 API Key）
try:
    from .llm_evaluator import LLMEvaluator
except ImportError:
    LLMEvaluator = None

# 完整 Pipeline
try:
    from .pipeline import EvalPipeline, full_eval, quick_check
except ImportError:
    EvalPipeline = None
    full_eval = None
    quick_check = None

__all__ = [
    # 规则评估
    "RuleEvaluator",
    "quick_eval",
    "is_quality_ok",
    # 配置
    "EvalConfig",
    "LLMProvider",
    "get_default_config",
    # LLM 评估
    "LLMEvaluator",
    # Pipeline
    "EvalPipeline",
    "full_eval",
    "quick_check",
]
