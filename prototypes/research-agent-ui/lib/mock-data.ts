// ═══════════════════════════════════════════════════════════════
// Mock 数据生成
// ═══════════════════════════════════════════════════════════════

import type { Briefing, ExecutionPlan, Deliverable } from '@/types'

export function mockBriefing(direction: string): Briefing {
  return {
    originalQuestion: direction,
    rewrittenQuestion: `基于「${direction.slice(0, 30)}...」的系统性研究`,
    scope: [
      '核心问题：技术发展趋势与最佳实践',
      '研究范围：学术论文 + 工业案例',
      '时间范围：2024-2025 年'
    ],
    keyTerms: ['LLM', 'Agent', 'Prompt Engineering', 'Code Generation'],
    assumptions: [
      { id: '1', content: '关注学术论文 + 工业实践案例', checked: true },
      { id: '2', content: '以主流模型（GPT-4、Claude、Gemini）为研究对象', checked: true },
      { id: '3', content: '代码生成质量以通过率、正确率为衡量标准', checked: true },
      { id: '4', content: '不考虑多模态代码生成（图像→代码）', checked: false },
    ],
    risks: [
      { id: '1', content: '部分最新论文可能无法获取全文（付费墙）', level: 'medium' },
      { id: '2', content: '工业实践案例可能存在商业机密限制', level: 'low' },
      { id: '3', content: '技术发展快，部分结论可能很快过时', level: 'low' },
    ],
    roadmap: [
      { round: 1, title: '文献检索', description: '初步分类', estimatedTime: '~30min' },
      { round: 2, title: '深度分析', description: '核心发现', estimatedTime: '~45min' },
      { round: 3, title: '实验验证', description: '假设验证', estimatedTime: '~60min' },
      { round: 4, title: '论文撰写', description: '结论收敛', estimatedTime: '~30min' },
    ]
  }
}

export function mockExecutionPlan(): ExecutionPlan {
  return {
    id: 'ep-001',
    description: '运行 Python 脚本分析 23 篇论文的引用关系，生成知识图谱',
    expectedOutput: [
      '论文引用关系图（可视化）',
      '核心论文排名（按影响力）',
      '研究脉络时间线'
    ],
    costLevel: 'low',
    riskLevel: 'low',
    estimatedTime: '约 3 分钟',
    recommendation: 'execute',
    recommendationReason: '成本低、风险低，且知识图谱对后续分析有重要价值',
    downgradePlan: '使用预训练模型估算引用关系（精度较低但无需运算）'
  }
}

export function mockDeliverable(): Deliverable {
  return {
    paperDraft: `# LLM 代码生成技术综述

## 摘要
本研究综述了 2024-2025 年大语言模型在代码生成领域的最新进展...

## 1. 引言
大语言模型在代码生成领域展现出强大的能力...

## 2. 相关工作
### 2.1 Prompt Engineering
...

## 3. 核心发现
### 3.1 Prompt Engineering 的效果
研究表明，优化的 Prompt 可以提升代码正确率 15-20%...

### 3.2 Agent 架构的演进
从单轮生成到多轮迭代，Agent 架构正在快速演进...

## 4. 结论
...`,
    conclusions: [
      { id: '1', content: 'Prompt Engineering 可提升代码正确率 15-20%', confidence: 'high', evidenceCount: 8, isVerified: true },
      { id: '2', content: 'Agent 多轮迭代优于单轮生成', confidence: 'high', evidenceCount: 5, isVerified: true },
      { id: '3', content: 'ReAct 在复杂任务中表现优于 CoT', confidence: 'medium', evidenceCount: 3, isVerified: false },
    ],
    pendingItems: [
      'Tool Use 与 Code Interpreter 的对比',
      '多模态代码生成的可行性'
    ],
    nextSteps: [
      {
        id: '1',
        title: '深入 Agent 架构对比实验',
        description: '验证 ReAct vs CoT 在不同复杂度任务中的表现',
        estimatedTime: '45 分钟',
        expectedBenefit: 'high',
        isRecommended: true
      },
      {
        id: '2',
        title: '扩展工业实践案例分析',
        description: '收集更多开源项目的 Agent 实现案例',
        estimatedTime: '30 分钟',
        expectedBenefit: 'medium',
        isRecommended: false
      },
      {
        id: '3',
        title: '收敛并完成论文',
        description: '基于当前结论完善论文，准备最终交付',
        estimatedTime: '20 分钟',
        expectedBenefit: 'medium',
        isRecommended: false
      }
    ],
    completionRate: 75
  }
}

