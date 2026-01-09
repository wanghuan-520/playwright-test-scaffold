"""
纯规则评估器
不需要 LLM，完全基于规则检查

使用方法:
    from eval import RuleEvaluator
    
    evaluator = RuleEvaluator()
    result = evaluator.evaluate("这是 AI 生成的内容...")
    
    print(result["passed"])       # True/False
    print(result["score"])        # 0.85
    print(result["summary"])      # "通过 8/10 项检查"
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .checkers import (
    StructureChecker,
    ContentChecker,
    QualityChecker,
    CheckResult,
)


class RuleEvaluator:
    """
    纯规则评估器
    
    特点：
    - 不需要 LLM，完全免费
    - 执行快速（毫秒级）
    - 结果确定（无随机性）
    - 可配置阈值
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        Args:
            threshold: 通过阈值（0-1），默认 0.7
        """
        self.threshold = threshold
        self.structure_checker = StructureChecker()
        self.content_checker = ContentChecker()
        self.quality_checker = QualityChecker()
    
    def evaluate(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        评估文本质量
        
        Args:
            text: 要评估的文本
            context: 可选的上下文信息（不影响评估，仅记录）
        
        Returns:
            {
                "passed": True,
                "score": 0.85,
                "summary": "通过 8/10 项检查",
                "checks": {...},
                "failed_checks": [...],
                "timestamp": "..."
            }
        """
        # 运行所有检查
        all_checks: List[CheckResult] = []
        all_checks.extend(self.structure_checker.run_all(text))
        all_checks.extend(self.content_checker.run_all(text))
        all_checks.extend(self.quality_checker.run_all(text))
        
        # 统计结果
        total = len(all_checks)
        passed_checks = [c for c in all_checks if c.passed]
        failed_checks = [c for c in all_checks if not c.passed]
        
        # 计算总分（平均分）
        score = sum(c.score for c in all_checks) / total if total > 0 else 0
        
        # 是否通过
        overall_passed = score >= self.threshold
        
        return {
            "passed": overall_passed,
            "score": round(score, 2),
            "threshold": self.threshold,
            "summary": f"通过 {len(passed_checks)}/{total} 项检查，得分 {score:.2f}",
            "checks": {
                "structure": [asdict(c) for c in self.structure_checker.run_all(text)],
                "content": [asdict(c) for c in self.content_checker.run_all(text)],
                "quality": [asdict(c) for c in self.quality_checker.run_all(text)],
            },
            "passed_checks": [c.name for c in passed_checks],
            "failed_checks": [{"name": c.name, "reason": c.reason} for c in failed_checks],
            "context": context[:100] + "..." if context and len(context) > 100 else context,
            "text_length": len(text),
            "timestamp": datetime.now().isoformat(),
        }
    
    def evaluate_batch(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        批量评估
        
        Args:
            items: [{"text": "...", "context": "..."}, ...]
        
        Returns:
            批量评估报告
        """
        results = []
        for item in items:
            result = self.evaluate(
                text=item.get("text", ""),
                context=item.get("context")
            )
            results.append(result)
        
        passed = sum(1 for r in results if r["passed"])
        avg_score = sum(r["score"] for r in results) / len(results) if results else 0
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": f"{passed/len(results)*100:.1f}%" if results else "0%",
            "avg_score": round(avg_score, 2),
            "details": results,
        }
    
    def save_report(self, report: Dict[str, Any], path: str):
        """保存评估报告到 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def print_result(self, result: Dict[str, Any]):
        """打印评估结果（美化输出）"""
        status = "✅ 通过" if result["passed"] else "❌ 未通过"
        
        print(f"\n{'='*50}")
        print(f"评估结果: {status}")
        print(f"总分: {result['score']} (阈值: {result['threshold']})")
        print(f"摘要: {result['summary']}")
        print(f"{'='*50}")
        
        if result["failed_checks"]:
            print("\n❌ 未通过的检查:")
            for check in result["failed_checks"]:
                print(f"  - {check['name']}: {check['reason']}")
        
        print(f"\n✅ 通过的检查: {', '.join(result['passed_checks'])}")
        print()


# ============================================================
# 便捷函数
# ============================================================

def quick_eval(text: str, threshold: float = 0.7) -> Dict[str, Any]:
    """
    快速评估（一行代码）
    
    使用方法:
        from eval.rule_evaluator import quick_eval
        result = quick_eval("你的文本...")
        print(result["passed"], result["score"])
    """
    evaluator = RuleEvaluator(threshold=threshold)
    return evaluator.evaluate(text)


def is_quality_ok(text: str, threshold: float = 0.7) -> bool:
    """
    最简单的质量检查（只返回 True/False）
    
    使用方法:
        from eval.rule_evaluator import is_quality_ok
        if is_quality_ok(ai_output):
            print("质量达标")
    """
    return quick_eval(text, threshold)["passed"]

