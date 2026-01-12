"""
LLM 评估器
使用大模型评估 AI 输出的质量，特别是理论正确性

支持：DeepSeek、智谱、OpenAI、Ollama
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .config import EvalConfig, get_default_config
from .llm_client import LLMClient


@dataclass
class EvalDimension:
    """评估维度"""
    name: str
    description: str
    weight: float
    criteria: str


# 评估维度定义（针对研究/推理系统优化）
EVAL_DIMENSIONS: List[EvalDimension] = [
    EvalDimension(
        name="logic",
        description="逻辑正确性：推理链是否严密，论证是否自洽",
        weight=0.25,
        criteria="""
0分: 存在明显逻辑错误或自相矛盾
0.5分: 逻辑基本正确，但有跳跃或不严密之处
1分: 逻辑严密，论证自洽，推理链完整
"""
    ),
    EvalDimension(
        name="evidence",
        description="证据充分性：结论是否有充分的证据支撑",
        weight=0.25,
        criteria="""
0分: 无证据或证据与结论无关
0.5分: 有证据但不充分，或证据质量不高
1分: 证据充分、相关、可靠，能有效支撑结论
"""
    ),
    EvalDimension(
        name="accuracy",
        description="事实准确性：陈述的事实是否正确",
        weight=0.20,
        criteria="""
0分: 存在明显事实错误
0.5分: 大部分正确，但有小错误或不精确之处
1分: 事实准确无误，引用可靠
"""
    ),
    EvalDimension(
        name="completeness",
        description="完整性：是否涵盖了问题的关键方面",
        weight=0.15,
        criteria="""
0分: 严重缺失，遗漏关键内容
0.5分: 基本完整，但有明显遗漏
1分: 内容全面，涵盖所有关键方面
"""
    ),
    EvalDimension(
        name="insight",
        description="洞察力：是否有深度分析和独到见解",
        weight=0.15,
        criteria="""
0分: 纯搬运，无分析无见解
0.5分: 有一定分析，但见解普通
1分: 分析深入，有独到见解或创新性观点
"""
    ),
]


class LLMEvaluator:
    """
    LLM 评估器
    
    使用方法:
        # 方式 1：使用默认配置（从环境变量读取）
        evaluator = LLMEvaluator()
        
        # 方式 2：指定配置
        config = EvalConfig(provider="deepseek", api_key="sk-xxx")
        evaluator = LLMEvaluator(config)
        
        # 评估
        result = evaluator.evaluate(text, context="用户的原始问题")
    """
    
    def __init__(self, config: Optional[EvalConfig] = None):
        """
        初始化 LLM 评估器
        
        Args:
            config: 评估配置，如不提供则从环境变量读取
        """
        self.config = config or get_default_config()
        
        if not self.config.validate():
            raise ValueError(
                f"配置不完整！请设置环境变量：\n"
                f"  export {self.config.provider.upper()}_API_KEY=your-key\n"
                f"或在代码中传入 api_key 参数"
            )
        
        # 使用轻量级客户端（不依赖 openai 包）
        self.client = LLMClient(
            base_url=self.config.base_url,
            api_key=self.config.api_key or "ollama",
            model=self.config.model,
        )
    
    def evaluate(
        self, 
        text: str, 
        context: Optional[str] = None,
        custom_criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估文本质量
        
        Args:
            text: 要评估的文本（AI 输出）
            context: 上下文（用户的原始问题/研究方向）
            custom_criteria: 自定义评估标准（可选）
        
        Returns:
            {
                "passed": True,
                "score": 0.85,
                "dimensions": {...},
                "summary": "...",
                "suggestions": [...]
            }
        """
        prompt = self._build_prompt(text, context, custom_criteria)
        
        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度，确保评估稳定
            )
            
            content = self.client.get_content(response)
            
            # 解析 JSON 响应
            result = self._parse_response(content)
            
            # 计算加权总分
            score = self._calculate_score(result.get("dimensions", {}))
            
            return {
                "passed": score >= self.config.threshold,
                "score": round(score, 2),
                "threshold": self.config.threshold,
                "dimensions": result.get("dimensions", {}),
                "summary": result.get("summary", ""),
                "suggestions": result.get("suggestions", []),
                "model": self.config.model,
                "provider": self.config.provider,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "score": 0,
                "error": str(e),
                "model": self.config.model,
                "provider": self.config.provider,
            }
    
    def evaluate_theory(
        self,
        theory: str,
        premises: List[str],
        expected_conclusion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        专门评估推理/理论的正确性
        
        Args:
            theory: 推导出的理论/结论
            premises: 前提条件列表
            expected_conclusion: 预期结论（可选，用于对比）
        
        Returns:
            评估结果
        """
        prompt = f"""
请评估以下推理/理论的正确性：

## 前提条件
{chr(10).join(f"- {p}" for p in premises)}

## 推导出的理论/结论
{theory}

{f"## 预期结论（供参考）{chr(10)}{expected_conclusion}" if expected_conclusion else ""}

## 评估要求
1. 检查推理链是否完整、严密
2. 检查结论是否能从前提正确推导出
3. 检查是否存在逻辑跳跃或隐含假设
4. 评估结论的可信度

请给出详细评估，包括：
- 推理正确性评分（0-1）
- 存在的问题（如有）
- 改进建议

输出 JSON 格式。
"""
        return self.evaluate(prompt, context="理论推理验证")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        return """你是一个严格的学术评审专家，擅长评估研究内容的质量。

你的评估标准：
1. 逻辑严密：推理链完整，论证自洽
2. 证据充分：结论有可靠证据支撑
3. 事实准确：陈述的事实正确无误
4. 内容完整：涵盖问题的关键方面
5. 有洞察力：分析深入，有独到见解

请始终输出有效的 JSON 格式。"""
    
    def _build_prompt(
        self, 
        text: str, 
        context: Optional[str],
        custom_criteria: Optional[str]
    ) -> str:
        """构建评估提示"""
        
        dimensions_text = "\n".join([
            f"### {d.name} - {d.description}（权重 {d.weight}）\n评分标准：{d.criteria}"
            for d in EVAL_DIMENSIONS
        ])
        
        return f"""
请评估以下内容的质量：

## 原始问题/研究方向
{context or "未提供"}

## 待评估内容
{text}

## 评估维度
{dimensions_text}

{f"## 额外评估标准{chr(10)}{custom_criteria}" if custom_criteria else ""}

## 输出要求
请输出 JSON 格式：
{{
  "dimensions": {{
    "logic": {{"score": 0.9, "reason": "推理链完整..."}},
    "evidence": {{"score": 0.8, "reason": "证据充分..."}},
    "accuracy": {{"score": 0.85, "reason": "事实准确..."}},
    "completeness": {{"score": 0.9, "reason": "内容全面..."}},
    "insight": {{"score": 0.7, "reason": "分析有一定深度..."}}
  }},
  "summary": "总体评价...",
  "suggestions": ["建议1", "建议2"]
}}
"""
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        # 尝试直接解析 JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 markdown 代码块中提取 JSON
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试找到 { } 包围的内容
        brace_match = re.search(r'\{[\s\S]*\}', content)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass
        
        # 解析失败，返回空结果
        return {"summary": content, "dimensions": {}}
    
    def _calculate_score(self, dimensions: Dict[str, Any]) -> float:
        """计算加权总分"""
        total = 0
        weight_sum = 0
        
        for dim in EVAL_DIMENSIONS:
            if dim.name in dimensions:
                score = dimensions[dim.name].get("score", 0)
                total += score * dim.weight
                weight_sum += dim.weight
        
        return total / weight_sum if weight_sum > 0 else 0
    
    def print_result(self, result: Dict[str, Any]):
        """美化打印评估结果"""
        status = "✅ 通过" if result.get("passed") else "❌ 未通过"
        
        print(f"\n{'='*60}")
        print(f"LLM 评估结果: {status}")
        print(f"模型: {result.get('provider', '')} / {result.get('model', '')}")
        print(f"总分: {result.get('score', 0)} (阈值: {result.get('threshold', 0.7)})")
        print(f"{'='*60}")
        
        if "error" in result:
            print(f"\n❌ 错误: {result['error']}")
            return
        
        print(f"\n📝 总结: {result.get('summary', '')}")
        
        dimensions = result.get("dimensions", {})
        if dimensions:
            print("\n📊 各维度评分:")
            for name, data in dimensions.items():
                score = data.get("score", 0)
                reason = data.get("reason", "")
                bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                print(f"  {name}: [{bar}] {score:.2f} - {reason[:50]}...")
        
        suggestions = result.get("suggestions", [])
        if suggestions:
            print("\n💡 改进建议:")
            for s in suggestions:
                print(f"  - {s}")
        
        print()

