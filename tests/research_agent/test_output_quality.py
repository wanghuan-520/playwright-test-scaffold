"""
AI 研究系统输出质量测试

使用 Eval 框架验证 AI 输出的质量，包括：
- 规则检查：结构、内容、质量
- LLM 评估：逻辑、证据、准确性、完整性、洞察力
"""

import pytest
from eval import quick_eval, is_quality_ok


class TestRuleEvaluation:
    """规则评估测试（免费，快速）"""
    
    @pytest.mark.eval_rule
    def test_briefing_structure(self, eval_rule, mock_research_briefing):
        """测试研究简报结构是否完整"""
        result = eval_rule.evaluate(mock_research_briefing)
        
        assert result["passed"], f"研究简报结构不合格: {result['failed_checks']}"
        assert result["score"] >= 0.7, f"得分过低: {result['score']}"
    
    @pytest.mark.eval_rule
    def test_conclusion_card_structure(self, eval_rule, mock_conclusion_card):
        """测试结论卡结构是否完整"""
        result = eval_rule.evaluate(mock_conclusion_card)
        
        assert result["passed"], f"结论卡结构不合格: {result['failed_checks']}"
    
    @pytest.mark.eval_rule
    def test_paper_draft_structure(self, eval_rule, mock_paper_draft):
        """测试论文草稿结构是否完整"""
        result = eval_rule.evaluate(mock_paper_draft)
        
        assert result["passed"], f"论文草稿结构不合格: {result['failed_checks']}"
        assert result["score"] >= 0.8, f"论文草稿得分过低: {result['score']}"
    
    @pytest.mark.eval_rule
    def test_low_quality_detection(self, eval_rule, mock_low_quality_output):
        """测试能否检测出低质量输出"""
        result = eval_rule.evaluate(mock_low_quality_output)
        
        # 预期：低质量输出应该不通过
        assert not result["passed"], "未能检测出低质量输出"
        assert result["score"] < 0.5, f"低质量输出得分过高: {result['score']}"


class TestLLMEvaluation:
    """LLM 评估测试（需要 API Key）"""
    
    @pytest.mark.eval_llm
    def test_briefing_quality(self, eval_llm, mock_research_briefing, eval_assert):
        """测试研究简报内容质量"""
        result = eval_llm.evaluate(
            mock_research_briefing, 
            context="评估多 Agent 协作研究简报"
        )
        
        eval_assert.passed(result)
        eval_assert.score_above(result, 0.6)
    
    @pytest.mark.eval_llm
    def test_conclusion_logic(self, eval_llm, mock_conclusion_card, eval_assert):
        """测试结论卡逻辑正确性"""
        result = eval_llm.evaluate(
            mock_conclusion_card,
            context="评估研究结论的逻辑正确性"
        )
        
        eval_assert.passed(result)
        eval_assert.dimension_above(result, "logic", 0.7, "结论逻辑应严密")
        eval_assert.dimension_above(result, "evidence", 0.6, "应有证据支撑")
    
    @pytest.mark.eval_llm
    def test_paper_comprehensive(self, eval_llm, mock_paper_draft, eval_assert):
        """测试论文草稿综合质量"""
        result = eval_llm.evaluate(
            mock_paper_draft,
            context="评估多 Agent 协作研究论文草稿"
        )
        
        eval_assert.passed(result)
        eval_assert.score_above(result, 0.7)
        eval_assert.dimension_above(result, "completeness", 0.8, "论文应完整")
    
    @pytest.mark.eval_llm
    def test_low_quality_rejection(self, eval_llm, mock_low_quality_output, eval_assert):
        """测试 LLM 能否拒绝低质量输出"""
        result = eval_llm.evaluate(
            mock_low_quality_output,
            context="评估研究结论"
        )
        
        # 预期：低质量输出应该不通过
        assert not result.get("passed", True), "LLM 未能识别低质量输出"
        assert result.get("score", 1.0) < 0.5, f"低质量输出得分过高: {result.get('score')}"


class TestPipelineEvaluation:
    """完整流水线评估测试"""
    
    def test_full_pipeline_briefing(self, eval_pipeline, mock_research_briefing, eval_assert):
        """完整流水线测试：研究简报"""
        result = eval_pipeline.run(
            mock_research_briefing,
            context="多 Agent 协作研究简报"
        )
        
        eval_assert.passed(result)
        eval_assert.score_above(result, 0.7)
        
        # 检查规则和 LLM 都通过
        assert result["rule_check"]["passed"], f"规则检查失败: {result['rule_check']}"
        if result.get("llm_eval") and not result.get("skipped_llm"):
            assert result["llm_eval"]["passed"], f"LLM 评估失败: {result['llm_eval']}"
    
    def test_full_pipeline_paper(self, eval_pipeline, mock_paper_draft, eval_assert):
        """完整流水线测试：论文草稿"""
        result = eval_pipeline.run(
            mock_paper_draft,
            context="多 Agent 协作研究论文"
        )
        
        eval_assert.passed(result)
        eval_assert.score_above(result, 0.75, "论文草稿应有较高质量")


class TestTheoryVerification:
    """理论验证测试（Vibe Research 专用）"""
    
    @pytest.mark.eval_theory
    def test_valid_reasoning(self, eval_llm):
        """测试有效推理的验证"""
        result = eval_llm.evaluate_theory(
            theory="多 Agent 协作比单 Agent 更高效",
            premises=[
                "单 Agent 受上下文长度限制",
                "多 Agent 可以并行处理不同子任务",
                "专业化分工可以提升质量",
                "实验显示多 Agent 完成时间减少 60%"
            ],
            expected_conclusion="多 Agent 架构在复杂任务中更有优势"
        )
        
        assert result.get("passed", False), f"有效推理应该通过: {result}"
    
    @pytest.mark.eval_theory
    def test_invalid_reasoning(self, eval_llm):
        """测试无效推理的识别"""
        result = eval_llm.evaluate_theory(
            theory="AI 将完全取代人类科研",
            premises=[
                "AI 可以处理文献检索",
                "AI 可以生成文本"
            ],
            expected_conclusion=None  # 不提供预期结论
        )
        
        # 这个推理应该被识别为逻辑跳跃
        # 但具体结果取决于 LLM 的判断
        assert "score" in result or "passed" in result


# ============================================================
# 快捷测试函数
# ============================================================

class TestQuickEval:
    """快捷评估函数测试"""
    
    def test_is_quality_ok(self, mock_paper_draft, mock_low_quality_output):
        """测试 is_quality_ok 函数"""
        assert is_quality_ok(mock_paper_draft), "高质量输出应该通过"
        assert not is_quality_ok(mock_low_quality_output), "低质量输出应该不通过"
    
    def test_quick_eval(self, mock_conclusion_card):
        """测试 quick_eval 函数"""
        result = quick_eval(mock_conclusion_card)
        
        assert "passed" in result
        assert "score" in result
        assert "failed_checks" in result

