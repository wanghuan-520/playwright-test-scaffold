"""
规则检查器集合
每个检查器负责一类规则，返回统一格式的结果
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    passed: bool
    score: float  # 0-1
    reason: str
    details: Dict[str, Any] = None


class StructureChecker:
    """
    结构检查器：验证输出的结构完整性
    
    检查项：
    - 是否有标题层级
    - 是否有必要章节
    - 是否有合理的段落划分
    """
    
    REQUIRED_SECTIONS = ["摘要", "引言", "结论", "总结", "conclusion", "summary", "abstract"]
    
    def check_has_titles(self, text: str) -> CheckResult:
        """检查是否有标题结构"""
        # 匹配 # 标题 或 ## 标题
        titles = re.findall(r'^#{1,4}\s+.+$', text, re.MULTILINE)
        has_titles = len(titles) >= 2
        
        return CheckResult(
            name="has_titles",
            passed=has_titles,
            score=min(len(titles) / 5, 1.0),  # 5个标题得满分
            reason=f"找到 {len(titles)} 个标题" if has_titles else "缺少标题结构",
            details={"title_count": len(titles), "titles": titles[:5]}
        )
    
    def check_has_sections(self, text: str) -> CheckResult:
        """检查是否有必要章节"""
        text_lower = text.lower()
        found = [s for s in self.REQUIRED_SECTIONS if s in text_lower]
        has_sections = len(found) >= 2
        
        return CheckResult(
            name="has_sections",
            passed=has_sections,
            score=min(len(found) / 3, 1.0),
            reason=f"找到章节: {found}" if found else "缺少必要章节（摘要/引言/结论）",
            details={"found_sections": found}
        )
    
    def check_paragraph_structure(self, text: str) -> CheckResult:
        """检查段落结构"""
        # 按空行分段
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        avg_length = sum(len(p) for p in paragraphs) / max(len(paragraphs), 1)
        
        # 好的段落：数量适中，长度适中
        good_count = 5 <= len(paragraphs) <= 50
        good_length = 50 <= avg_length <= 500
        
        return CheckResult(
            name="paragraph_structure",
            passed=good_count and good_length,
            score=0.5 * int(good_count) + 0.5 * int(good_length),
            reason=f"{len(paragraphs)} 个段落，平均 {avg_length:.0f} 字",
            details={"paragraph_count": len(paragraphs), "avg_length": avg_length}
        )
    
    def run_all(self, text: str) -> List[CheckResult]:
        """运行所有结构检查"""
        return [
            self.check_has_titles(text),
            self.check_has_sections(text),
            self.check_paragraph_structure(text),
        ]


class ContentChecker:
    """
    内容检查器：验证输出的内容质量
    
    检查项：
    - 是否有足够长度
    - 是否有证据/引用
    - 是否有数据支撑
    - 是否无占位符残留
    """
    
    MIN_LENGTH = 500
    EVIDENCE_KEYWORDS = ["研究表明", "数据显示", "根据", "表明", "证明", "发现", 
                         "实验", "论文", "文献", "引用", "参考"]
    DATA_PATTERNS = [r'\d+%', r'\d+\.\d+', r'[\d,]+\s*(个|篇|项|次|人)']
    PLACEHOLDER_PATTERNS = [r'\[TODO\]', r'\[TBD\]', r'\{\{.*?\}\}', 
                            r'<待补充>', r'<待完善>', r'\.\.\.待']
    
    def check_min_length(self, text: str) -> CheckResult:
        """检查最小长度"""
        length = len(text)
        passed = length >= self.MIN_LENGTH
        
        return CheckResult(
            name="min_length",
            passed=passed,
            score=min(length / self.MIN_LENGTH, 1.0),
            reason=f"长度 {length} 字" + ("" if passed else f"（需要至少 {self.MIN_LENGTH} 字）"),
            details={"length": length, "required": self.MIN_LENGTH}
        )
    
    def check_has_evidence(self, text: str) -> CheckResult:
        """检查是否有证据支撑"""
        found = [k for k in self.EVIDENCE_KEYWORDS if k in text]
        has_evidence = len(found) >= 2
        
        return CheckResult(
            name="has_evidence",
            passed=has_evidence,
            score=min(len(found) / 4, 1.0),
            reason=f"证据关键词: {found[:5]}" if found else "缺少证据支撑的表述",
            details={"evidence_keywords": found}
        )
    
    def check_has_data(self, text: str) -> CheckResult:
        """检查是否有数据"""
        data_matches = []
        for pattern in self.DATA_PATTERNS:
            matches = re.findall(pattern, text)
            data_matches.extend(matches)
        
        has_data = len(data_matches) >= 1
        
        return CheckResult(
            name="has_data",
            passed=has_data,
            score=min(len(data_matches) / 3, 1.0),
            reason=f"找到 {len(data_matches)} 处数据" if has_data else "缺少数据支撑",
            details={"data_count": len(data_matches), "samples": data_matches[:5]}
        )
    
    def check_no_placeholder(self, text: str) -> CheckResult:
        """检查无占位符残留"""
        found_placeholders = []
        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_placeholders.extend(matches)
        
        no_placeholder = len(found_placeholders) == 0
        
        return CheckResult(
            name="no_placeholder",
            passed=no_placeholder,
            score=1.0 if no_placeholder else 0.0,
            reason="无占位符" if no_placeholder else f"发现占位符: {found_placeholders}",
            details={"placeholders": found_placeholders}
        )
    
    def run_all(self, text: str) -> List[CheckResult]:
        """运行所有内容检查"""
        return [
            self.check_min_length(text),
            self.check_has_evidence(text),
            self.check_has_data(text),
            self.check_no_placeholder(text),
        ]


class QualityChecker:
    """
    质量检查器：验证输出的质量指标
    
    检查项：
    - 重复度检查
    - 可读性检查（句子长度）
    - 专业术语密度
    """
    
    def check_no_repetition(self, text: str) -> CheckResult:
        """检查是否有大量重复"""
        # 按句子分割
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) < 3:
            return CheckResult(
                name="no_repetition",
                passed=True,
                score=1.0,
                reason="句子数量过少，跳过重复检查",
                details={}
            )
        
        # 检查重复句子
        unique = set(sentences)
        repetition_rate = 1 - len(unique) / len(sentences)
        no_repetition = repetition_rate < 0.1  # 重复率低于 10%
        
        return CheckResult(
            name="no_repetition",
            passed=no_repetition,
            score=1.0 - repetition_rate,
            reason=f"重复率 {repetition_rate*100:.1f}%",
            details={"total_sentences": len(sentences), "unique": len(unique)}
        )
    
    def check_readability(self, text: str) -> CheckResult:
        """检查可读性（句子平均长度）"""
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return CheckResult(
                name="readability",
                passed=False,
                score=0.0,
                reason="无有效句子",
                details={}
            )
        
        avg_length = sum(len(s) for s in sentences) / len(sentences)
        # 理想句子长度：20-80 字
        good_readability = 20 <= avg_length <= 80
        
        return CheckResult(
            name="readability",
            passed=good_readability,
            score=1.0 if good_readability else max(0, 1 - abs(avg_length - 50) / 50),
            reason=f"平均句长 {avg_length:.0f} 字" + ("" if good_readability else "（建议 20-80 字）"),
            details={"avg_sentence_length": avg_length, "sentence_count": len(sentences)}
        )
    
    def check_terminology(self, text: str) -> CheckResult:
        """检查专业术语密度"""
        # 常见 AI/研究领域术语
        terms = ["模型", "算法", "数据", "训练", "推理", "优化", "参数", 
                 "架构", "性能", "实验", "分析", "方法", "结果", "研究",
                 "LLM", "AI", "ML", "NLP", "Agent", "Prompt", "API"]
        
        text_lower = text.lower()
        found = [t for t in terms if t.lower() in text_lower]
        term_density = len(found) / len(terms)
        
        has_terminology = term_density >= 0.2  # 至少 20% 的术语出现
        
        return CheckResult(
            name="terminology",
            passed=has_terminology,
            score=min(term_density * 2, 1.0),
            reason=f"术语覆盖 {term_density*100:.0f}%: {found[:5]}",
            details={"found_terms": found, "density": term_density}
        )
    
    def run_all(self, text: str) -> List[CheckResult]:
        """运行所有质量检查"""
        return [
            self.check_no_repetition(text),
            self.check_readability(text),
            self.check_terminology(text),
        ]

