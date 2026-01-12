"""
Eval Pytest 插件
提供 fixtures 和 markers，用于测试 AI 输出质量

使用方法：
    # conftest.py
    pytest_plugins = ["eval.pytest_plugin"]
    
    # test_xxx.py
    def test_ai_output(eval_pipeline, eval_llm):
        result = eval_pipeline.run(ai_output)
        assert result["overall_passed"]
"""

import pytest
from typing import Generator

from .config import EvalConfig, get_default_config
from .rule_evaluator import RuleEvaluator
from .llm_evaluator import LLMEvaluator
from .pipeline import EvalPipeline


# ============================================================
# Pytest Fixtures
# ============================================================

@pytest.fixture(scope="session")
def eval_config() -> EvalConfig:
    """
    Eval 配置（会话级，整个测试会话共享）
    
    从环境变量读取配置，可通过 pytest.ini 或命令行参数覆盖
    """
    return get_default_config()


@pytest.fixture(scope="session")
def eval_rule() -> RuleEvaluator:
    """
    规则评估器（会话级，免费，快速）
    
    用法：
        def test_structure(eval_rule):
            result = eval_rule.evaluate(ai_output)
            assert result["passed"]
    """
    return RuleEvaluator(threshold=0.7)


@pytest.fixture(scope="session")
def eval_llm(eval_config: EvalConfig) -> LLMEvaluator:
    """
    LLM 评估器（会话级，需要 API Key）
    
    用法：
        def test_theory(eval_llm):
            result = eval_llm.evaluate(ai_output, context="研究方向")
            assert result["passed"]
    """
    if not eval_config.validate():
        pytest.skip("LLM 评估需要配置 API Key（设置 DEEPSEEK_API_KEY 等环境变量）")
    return LLMEvaluator(eval_config)


@pytest.fixture(scope="session")
def eval_pipeline(eval_config: EvalConfig) -> EvalPipeline:
    """
    完整评估流水线（会话级，规则 + LLM）
    
    用法：
        def test_full(eval_pipeline):
            result = eval_pipeline.run(ai_output, context="研究方向")
            assert result["overall_passed"]
    """
    return EvalPipeline(eval_config)


@pytest.fixture
def eval_context() -> dict:
    """
    评估上下文（函数级，每个测试可自定义）
    
    用法：
        def test_xxx(eval_context):
            eval_context["research_direction"] = "多Agent协作"
            eval_context["expected_sections"] = ["摘要", "方法", "结论"]
    """
    return {
        "research_direction": "",
        "expected_sections": [],
        "keywords": [],
        "threshold": 0.7,
    }


# ============================================================
# Pytest Markers
# ============================================================

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line(
        "markers", "eval_rule: 仅使用规则评估（免费，快速）"
    )
    config.addinivalue_line(
        "markers", "eval_llm: 使用 LLM 评估（需要 API Key，慢）"
    )
    config.addinivalue_line(
        "markers", "eval_theory: 理论验证专用（需要 API Key）"
    )


# ============================================================
# 断言助手
# ============================================================

class EvalAssertions:
    """
    Eval 断言助手
    
    用法：
        def test_xxx(eval_assert, eval_pipeline):
            result = eval_pipeline.run(ai_output)
            eval_assert.passed(result)
            eval_assert.score_above(result, 0.8)
            eval_assert.dimension_above(result, "logic", 0.7)
    """
    
    @staticmethod
    def passed(result: dict, msg: str = ""):
        """断言评估通过"""
        assert result.get("overall_passed") or result.get("passed"), \
            f"Eval 未通过: {result.get('summary', result)}\n{msg}"
    
    @staticmethod
    def score_above(result: dict, threshold: float, msg: str = ""):
        """断言分数高于阈值"""
        score = result.get("overall_score") or result.get("score", 0)
        assert score >= threshold, \
            f"Eval 分数 {score} 低于阈值 {threshold}\n{msg}"
    
    @staticmethod
    def dimension_above(result: dict, dimension: str, threshold: float, msg: str = ""):
        """断言某维度分数高于阈值"""
        llm_eval = result.get("llm_eval", {})
        dimensions = llm_eval.get("dimensions", {})
        dim_data = dimensions.get(dimension, {})
        score = dim_data.get("score", 0)
        assert score >= threshold, \
            f"维度 {dimension} 分数 {score} 低于阈值 {threshold}\n原因: {dim_data.get('reason', '')}\n{msg}"
    
    @staticmethod
    def no_failed_checks(result: dict, msg: str = ""):
        """断言规则检查全部通过"""
        failed = result.get("failed_checks", [])
        if isinstance(failed, list) and len(failed) > 0:
            failed_names = [f.get("name", f) if isinstance(f, dict) else f for f in failed]
            assert False, f"规则检查失败: {failed_names}\n{msg}"


@pytest.fixture
def eval_assert() -> EvalAssertions:
    """Eval 断言助手"""
    return EvalAssertions()

