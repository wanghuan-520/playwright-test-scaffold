// ═══════════════════════════════════════════════════════════════
// 多轮 AI 研究助手系统 - 类型定义
// ═══════════════════════════════════════════════════════════════

// 研究会话状态
export type SessionStage = 
  | 'input'      // 输入方向
  | 'briefing'   // 研究简报
  | 'running'    // 调研进行中
  | 'compute'    // 运算确认
  | 'monitoring' // 运算监控
  | 'delivery'   // 交付中心

// Agent 类型
export type AgentType = 'Planner' | 'Librarian' | 'Reasoner' | 'Verifier' | 'Compute'

// Agent 状态
export type AgentStatusType = 'idle' | 'working' | 'completed' | 'error' | 'waiting'

// 边界约束
export interface Constraints {
  budget: 'low' | 'medium' | 'high'
  speed: 'fast' | 'standard' | 'deep'
  rigor: number // 1-10
  exclusions: string
}

// 假设
export interface Assumption {
  id: string
  content: string
  checked: boolean
}

// 风险
export interface Risk {
  id: string
  content: string
  level: 'low' | 'medium' | 'high'
}

// 里程碑
export interface Milestone {
  round: number
  title: string
  description: string
  estimatedTime: string
}

// 研究简报
export interface Briefing {
  originalQuestion: string
  rewrittenQuestion: string
  scope: string[]
  keyTerms: string[]
  assumptions: Assumption[]
  risks: Risk[]
  roadmap: Milestone[]
}

// Agent 状态
export interface AgentStatus {
  agent: AgentType
  status: AgentStatusType
  message: string
  progress?: number
  details?: string
}

// 日志条目
export interface LogEntry {
  timestamp: string
  agent: AgentType
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

// 初步发现
export interface Finding {
  id: string
  type: 'conclusion' | 'pending'
  content: string
}

// 执行计划
export interface ExecutionPlan {
  id: string
  description: string
  expectedOutput: string[]
  costLevel: 'low' | 'medium' | 'high'
  riskLevel: 'low' | 'medium' | 'high'
  estimatedTime: string
  recommendation: 'execute' | 'downgrade' | 'skip'
  recommendationReason: string
  downgradePlan?: string
}

// 运算状态
export interface ComputeStatus {
  stage: string
  currentItem: string
  progress: number
  totalItems: number
  intermediateResult?: string
}

// 证据
export interface Evidence {
  id: string
  source: string
  content: string
}

// 结论
export interface Conclusion {
  id: string
  content: string
  confidence: 'high' | 'medium' | 'low'
  evidenceCount: number
  isVerified: boolean
}

// 下一步选项
export interface NextStepOption {
  id: string
  title: string
  description: string
  estimatedTime: string
  expectedBenefit: 'high' | 'medium' | 'low'
  isRecommended: boolean
}

// 交付物
export interface Deliverable {
  paperDraft: string
  conclusions: Conclusion[]
  pendingItems: string[]
  nextSteps: NextStepOption[]
  completionRate: number
}

// 研究会话
export interface ResearchSession {
  id: string
  direction: string
  constraints: Constraints
  stage: SessionStage
  currentRound: number
  briefing?: Briefing
  agentStatuses: AgentStatus[]
  logs: LogEntry[]
  findings: Finding[]
  executionPlan?: ExecutionPlan
  computeStatus?: ComputeStatus
  deliverable?: Deliverable
}

