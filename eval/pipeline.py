"""
完整 Eval Pipeline
结合规则检查 + LLM 深度评估

流程：
1. 规则预检（快速、免费）
2. LLM 深度评估（慢、花钱，但能评估理论正确性）
3. 综合评分

使用方法:
    from eval.pipeline import EvalPipeline
    
    pipeline = EvalPipeline()
    result = pipeline.run(ai_output, context="研究方向")
    pipeline.print_result(result)
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import EvalConfig, get_default_config
from .rule_evaluator import RuleEvaluator
from .llm_evaluator import LLMEvaluator


class EvalPipeline:
    """
    完整 Eval 流水线
    
    特点：
    - 规则预检：快速过滤明显低质量内容
    - LLM 评估：深度评估理论正确性
    - 可配置：支持多种 LLM 提供商
    """
    
    def __init__(
        self,
        config: Optional[EvalConfig] = None,
        rule_threshold: float = 0.6,
        llm_threshold: float = 0.7,
        skip_llm_on_rule_fail: bool = False,  # 改为 False，即使规则失败也跑 LLM
    ):
        """
        初始化 Pipeline
        
        Args:
            config: LLM 配置
            rule_threshold: 规则检查通过阈值
            llm_threshold: LLM 评估通过阈值
            skip_llm_on_rule_fail: 规则失败时是否跳过 LLM（建议 False）
        """
        self.config = config or get_default_config()
        self.rule_threshold = rule_threshold
        self.llm_threshold = llm_threshold
        self.skip_llm_on_rule_fail = skip_llm_on_rule_fail
        
        # 初始化评估器
        self.rule_evaluator = RuleEvaluator(threshold=rule_threshold)
        
        # LLM 评估器延迟初始化（避免没有 key 时报错）
        self._llm_evaluator = None
    
    @property
    def llm_evaluator(self) -> LLMEvaluator:
        """延迟初始化 LLM 评估器"""
        if self._llm_evaluator is None:
            self._llm_evaluator = LLMEvaluator(self.config)
        return self._llm_evaluator
    
    def run(
        self,
        text: str,
        context: Optional[str] = None,
        run_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        运行完整评估
        
        Args:
            text: 要评估的文本
            context: 上下文（研究方向、原始问题等）
            run_llm: 是否运行 LLM 评估（关闭可省钱）
        
        Returns:
            完整评估结果
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "context": context[:100] + "..." if context and len(context) > 100 else context,
            "text_length": len(text),
        }
        
        # ========== Step 1: 规则预检 ==========
        rule_result = self.rule_evaluator.evaluate(text)
        result["rule_check"] = {
            "passed": rule_result["passed"],
            "score": rule_result["score"],
            "failed_checks": rule_result["failed_checks"],
        }
        
        # 规则严重失败时跳过 LLM（可配置）
        if not rule_result["passed"] and self.skip_llm_on_rule_fail:
            result["llm_eval"] = None
            result["skipped_llm"] = True
            result["overall_passed"] = False
            result["overall_score"] = rule_result["score"] * 0.3  # 规则分打折
            result["reason"] = f"规则预检失败: {rule_result['failed_checks']}"
            return result
        
        # ========== Step 2: LLM 深度评估 ==========
        if run_llm:
            try:
                llm_result = self.llm_evaluator.evaluate(text, context)
                result["llm_eval"] = {
                    "passed": llm_result["passed"],
                    "score": llm_result["score"],
                    "dimensions": llm_result.get("dimensions", {}),
                    "summary": llm_result.get("summary", ""),
                    "suggestions": llm_result.get("suggestions", []),
                }
                result["skipped_llm"] = False
                
                # 综合评分：规则 30% + LLM 70%
                combined_score = rule_result["score"] * 0.3 + llm_result["score"] * 0.7
                result["overall_score"] = round(combined_score, 2)
                # 使用 round 后的分数进行比较，避免浮点精度问题
                result["overall_passed"] = (
                    result["overall_score"] >= self.llm_threshold and
                    llm_result["score"] >= 0.6  # LLM 评分至少 0.6
                )
                
            except Exception as e:
                result["llm_eval"] = {"error": str(e)}
                result["skipped_llm"] = False
                result["overall_score"] = rule_result["score"] * 0.3
                result["overall_passed"] = False
                result["reason"] = f"LLM 评估失败: {e}"
        else:
            result["llm_eval"] = None
            result["skipped_llm"] = True
            result["overall_score"] = rule_result["score"]
            result["overall_passed"] = rule_result["passed"]
        
        return result
    
    def run_batch(
        self,
        items: List[Dict[str, str]],
        run_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        批量评估
        
        Args:
            items: [{"text": "...", "context": "..."}, ...]
            run_llm: 是否运行 LLM 评估
        
        Returns:
            批量评估报告
        """
        results = []
        for item in items:
            result = self.run(
                text=item.get("text", ""),
                context=item.get("context"),
                run_llm=run_llm,
            )
            results.append(result)
        
        passed = sum(1 for r in results if r.get("overall_passed"))
        avg_score = sum(r.get("overall_score", 0) for r in results) / len(results) if results else 0
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": f"{passed/len(results)*100:.1f}%" if results else "0%",
            "avg_score": round(avg_score, 2),
            "llm_enabled": run_llm,
            "details": results,
        }
    
    def save_report(self, report: Dict[str, Any], path: str):
        """保存评估报告"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def print_result(self, result: Dict[str, Any]):
        """美化打印评估结果"""
        status = "✅ 通过" if result.get("overall_passed") else "❌ 未通过"
        
        print(f"\n{'='*60}")
        print(f"Eval Pipeline 评估结果: {status}")
        print(f"综合得分: {result.get('overall_score', 0)}")
        print(f"{'='*60}")
        
        # 规则检查
        rule = result.get("rule_check", {})
        print(f"\n📋 规则预检: {'✅' if rule.get('passed') else '❌'} (得分: {rule.get('score', 0)})")
        if rule.get("failed_checks"):
            for check in rule["failed_checks"]:
                print(f"   ❌ {check['name']}: {check['reason']}")
        
        # LLM 评估
        llm = result.get("llm_eval")
        if llm and not llm.get("error"):
            print(f"\n🤖 LLM 评估: {'✅' if llm.get('passed') else '❌'} (得分: {llm.get('score', 0)})")
            print(f"   📝 {llm.get('summary', '')[:100]}...")
            
            dims = llm.get("dimensions", {})
            if dims:
                print("\n   📊 维度评分:")
                for name, data in dims.items():
                    score = data.get("score", 0)
                    bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    print(f"      {name}: [{bar}] {score:.2f}")
            
            suggestions = llm.get("suggestions", [])
            if suggestions:
                print("\n   💡 改进建议:")
                for s in suggestions[:3]:  # 最多显示 3 条
                    print(f"      - {s}")
        elif llm and llm.get("error"):
            print(f"\n🤖 LLM 评估: ❌ 错误 - {llm['error']}")
        elif result.get("skipped_llm"):
            print("\n🤖 LLM 评估: ⏭️ 已跳过")
        
        print()


# ============================================================
# 便捷函数
# ============================================================

def full_eval(text: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    完整评估（规则 + LLM）
    
    使用方法:
        from eval.pipeline import full_eval
        result = full_eval(ai_output, "研究方向")
    """
    pipeline = EvalPipeline()
    return pipeline.run(text, context)


def quick_check(text: str) -> bool:
    """
    快速检查（只用规则，不调 LLM）
    
    使用方法:
        from eval.pipeline import quick_check
        if quick_check(ai_output):
            print("基本合格")
    """
    pipeline = EvalPipeline()
    result = pipeline.run(text, run_llm=False)
    return result.get("overall_passed", False)

