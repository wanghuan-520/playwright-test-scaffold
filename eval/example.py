#!/usr/bin/env python3
"""
Eval 框架使用示例
运行: python -m eval.example
"""

from eval import RuleEvaluator

# 示例 AI 输出（模拟研究论文）
SAMPLE_OUTPUT = """
# LLM 代码生成技术综述

## 摘要

本文综述了大语言模型（LLM）在代码生成领域的最新进展，重点分析了 Prompt Engineering 和 Agent 架构两个核心方向。研究表明，优化的 Prompt 策略可将代码正确率提升 15-20%，而多 Agent 协作架构在复杂任务中表现优于单模型方案。

## 1. 引言

近年来，以 GPT-4、Claude、Gemini 为代表的大语言模型在代码生成任务上取得了显著突破。根据最新研究数据，这些模型在 HumanEval 基准测试中的通过率已超过 80%。然而，如何进一步提升生成代码的质量和可靠性，仍是学术界和工业界共同关注的焦点。

本文将从以下三个方面展开分析：
1. Prompt Engineering 技术演进
2. Agent 架构设计模式
3. 未来发展趋势

## 2. Prompt Engineering

Prompt Engineering 是指通过精心设计输入提示来优化 LLM 输出的技术。实验数据表明，采用 Few-shot 和 Chain-of-Thought (CoT) 策略，可显著提升代码生成的准确性。

### 2.1 Few-shot Learning

通过在 Prompt 中提供少量示例，模型能更好地理解任务意图。研究发现，3-5 个高质量示例通常能达到最佳效果。

### 2.2 Chain-of-Thought

CoT 技术通过引导模型逐步推理，有效降低了复杂问题的错误率。据统计，在算法题目上，CoT 可将正确率从 65% 提升至 85%。

## 3. Agent 架构

多 Agent 协作是当前 LLM 应用的热点方向。典型架构包括：
- ReAct：结合推理与行动
- AutoGPT：自主任务分解
- MetaGPT：多角色协作

实验表明，在需要多步骤推理的任务中，Agent 架构的成功率比单轮生成高出 25%。

## 4. 结论

综合以上分析，我们得出以下结论：

1. Prompt Engineering 仍是提升 LLM 代码生成质量的最直接有效手段
2. Agent 架构在复杂任务中展现出明显优势
3. 两种技术的结合将是未来的主流方向

未来研究可进一步探索多模态代码生成、实时代码补全优化等方向。
"""

# 低质量输出示例
LOW_QUALITY_OUTPUT = """
这是一段简短的文字。

[TODO: 待补充内容]

结论待定...
"""


def main():
    """运行示例"""
    print("=" * 60)
    print("Eval 框架 - 纯规则快速验证 示例")
    print("=" * 60)
    
    evaluator = RuleEvaluator(threshold=0.7)
    
    # 示例 1: 高质量输出
    print("\n📄 示例 1: 高质量 AI 输出")
    print("-" * 40)
    result1 = evaluator.evaluate(SAMPLE_OUTPUT, context="LLM 代码生成研究")
    evaluator.print_result(result1)
    
    # 示例 2: 低质量输出
    print("\n📄 示例 2: 低质量 AI 输出")
    print("-" * 40)
    result2 = evaluator.evaluate(LOW_QUALITY_OUTPUT, context="测试输出")
    evaluator.print_result(result2)
    
    # 示例 3: 批量评估
    print("\n📄 示例 3: 批量评估")
    print("-" * 40)
    batch_result = evaluator.evaluate_batch([
        {"text": SAMPLE_OUTPUT, "context": "高质量"},
        {"text": LOW_QUALITY_OUTPUT, "context": "低质量"},
    ])
    print(f"总数: {batch_result['total']}")
    print(f"通过: {batch_result['passed']}")
    print(f"通过率: {batch_result['pass_rate']}")
    print(f"平均分: {batch_result['avg_score']}")
    
    # 示例 4: 最简用法
    print("\n📄 示例 4: 最简用法")
    print("-" * 40)
    from eval.rule_evaluator import is_quality_ok, quick_eval
    
    print(f"is_quality_ok(高质量): {is_quality_ok(SAMPLE_OUTPUT)}")
    print(f"is_quality_ok(低质量): {is_quality_ok(LOW_QUALITY_OUTPUT)}")
    
    quick_result = quick_eval(SAMPLE_OUTPUT)
    print(f"quick_eval 得分: {quick_result['score']}")


if __name__ == "__main__":
    main()

