# Eval 框架 - 纯规则快速验证

> 不需要 LLM，完全基于规则检查，免费且快速

---

## 🚀 快速开始

### 最简单的用法（一行代码）

```python
from eval.rule_evaluator import is_quality_ok

if is_quality_ok(ai_output):
    print("质量达标 ✅")
else:
    print("质量不达标 ❌")
```

### 获取详细评估结果

```python
from eval.rule_evaluator import quick_eval

result = quick_eval(ai_output)

print(f"通过: {result['passed']}")
print(f"得分: {result['score']}")
print(f"摘要: {result['summary']}")
print(f"失败项: {result['failed_checks']}")
```

### 完整用法

```python
from eval import RuleEvaluator

# 创建评估器（可自定义阈值）
evaluator = RuleEvaluator(threshold=0.7)

# 评估
result = evaluator.evaluate(
    text=ai_output,
    context="用户的原始输入"  # 可选
)

# 美化打印
evaluator.print_result(result)
```

---

## 📊 检查项说明

### 结构检查 (Structure)

| 检查项 | 说明 | 通过条件 |
|-------|------|---------|
| `has_titles` | 是否有标题结构 | ≥2 个 # 标题 |
| `has_sections` | 是否有必要章节 | 包含摘要/引言/结论等 |
| `paragraph_structure` | 段落结构合理 | 5-50 段，平均 50-500 字 |

### 内容检查 (Content)

| 检查项 | 说明 | 通过条件 |
|-------|------|---------|
| `min_length` | 最小长度 | ≥500 字 |
| `has_evidence` | 有证据支撑 | ≥2 个证据关键词 |
| `has_data` | 有数据 | ≥1 处数据 |
| `no_placeholder` | 无占位符 | 无 [TODO] 等 |

### 质量检查 (Quality)

| 检查项 | 说明 | 通过条件 |
|-------|------|---------|
| `no_repetition` | 无重复 | 重复率 <10% |
| `readability` | 可读性 | 平均句长 20-80 字 |
| `terminology` | 专业术语 | 术语覆盖 ≥20% |

---

## 📈 评分规则

- 每项检查得分 0-1
- 总分 = 所有检查项的平均分
- 默认通过阈值 = 0.7

---

## 🔧 自定义配置

### 修改通过阈值

```python
# 严格模式
evaluator = RuleEvaluator(threshold=0.8)

# 宽松模式
evaluator = RuleEvaluator(threshold=0.6)
```

### 只运行部分检查

```python
from eval.checkers import StructureChecker, ContentChecker

# 只检查结构
structure = StructureChecker()
results = structure.run_all(text)

# 只检查内容
content = ContentChecker()
results = content.run_all(text)
```

---

## 📁 文件结构

```
eval/
├── __init__.py          # 导出接口
├── checkers.py          # 三类检查器
├── rule_evaluator.py    # 主评估器
└── README.md            # 本文件
```

---

## 💡 使用场景

1. **CI/CD 集成**：作为质量门禁
2. **开发自测**：快速验证 AI 输出
3. **批量筛选**：过滤低质量输出
4. **预检**：在调用 LLM 评估前先做规则检查

---

## 🎯 与 pytest 集成

```python
# tests/test_eval.py

import pytest
from eval import RuleEvaluator

evaluator = RuleEvaluator(threshold=0.7)

def test_output_quality():
    ai_output = get_ai_output()
    result = evaluator.evaluate(ai_output)
    
    assert result["passed"], f"质量不达标: {result['failed_checks']}"
    assert result["score"] >= 0.7, f"得分过低: {result['score']}"
```

---

## 📊 输出示例

```
==================================================
评估结果: ✅ 通过
总分: 0.85 (阈值: 0.7)
摘要: 通过 8/10 项检查，得分 0.85
==================================================

❌ 未通过的检查:
  - has_data: 缺少数据支撑
  - terminology: 术语覆盖 15%

✅ 通过的检查: has_titles, has_sections, paragraph_structure, min_length, has_evidence, no_placeholder, no_repetition, readability
```

