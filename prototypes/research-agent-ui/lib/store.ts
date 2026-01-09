// ═══════════════════════════════════════════════════════════════
// 状态管理 - Zustand Store
// ═══════════════════════════════════════════════════════════════

import { create } from 'zustand'
import type { 
  ResearchSession, 
  SessionStage, 
  Constraints, 
  Briefing,
  AgentStatus,
  LogEntry,
  ExecutionPlan,
  ComputeStatus,
  Deliverable
} from '@/types'
import { mockBriefing, mockDeliverable, mockExecutionPlan } from './mock-data'

interface ResearchStore {
  // 状态
  session: ResearchSession | null
  isLoading: boolean
  
  // Actions
  startResearch: (direction: string, constraints: Constraints) => void
  confirmBriefing: (action: 'continue' | 'adjust') => void
  handleComputeDecision: (decision: 'execute' | 'downgrade' | 'skip') => void
  selectNextStep: (optionId: string) => void
  stopResearch: () => void
  
  // 模拟状态更新
  simulateProgress: () => void
}

const defaultConstraints: Constraints = {
  budget: 'medium',
  speed: 'standard',
  rigor: 5,
  exclusions: ''
}

export const useResearchStore = create<ResearchStore>((set, get) => ({
  session: null,
  isLoading: false,

  startResearch: (direction, constraints) => {
    const session: ResearchSession = {
      id: `session-${Date.now()}`,
      direction,
      constraints,
      stage: 'briefing',
      currentRound: 0,
      briefing: mockBriefing(direction),
      agentStatuses: [],
      logs: [],
      findings: []
    }
    set({ session, isLoading: false })
  },

  confirmBriefing: (action) => {
    const { session } = get()
    if (!session) return

    if (action === 'continue') {
      set({
        session: {
          ...session,
          stage: 'running',
          currentRound: 1,
          agentStatuses: [
            { agent: 'Planner', status: 'working', message: '生成研究计划...' },
            { agent: 'Librarian', status: 'waiting', message: '等待计划完成' },
            { agent: 'Reasoner', status: 'idle', message: '待启动' },
            { agent: 'Verifier', status: 'idle', message: '待启动' },
          ],
          logs: [
            { timestamp: new Date().toLocaleTimeString(), agent: 'Planner', message: '开始分解研究任务...', type: 'info' }
          ]
        }
      })
      // 启动模拟进度
      setTimeout(() => get().simulateProgress(), 2000)
    }
  },

  simulateProgress: () => {
    const { session } = get()
    if (!session || session.stage !== 'running') return

    // 模拟 Agent 状态变化
    const stages = [
      { 
        agentStatuses: [
          { agent: 'Planner' as const, status: 'completed' as const, message: '✓ 任务分解完成：5 个子任务' },
          { agent: 'Librarian' as const, status: 'working' as const, message: '正在检索 arXiv...', progress: 30 },
          { agent: 'Reasoner' as const, status: 'waiting' as const, message: '等待证据收集' },
          { agent: 'Verifier' as const, status: 'idle' as const, message: '待启动' },
        ],
        logs: [
          { timestamp: new Date().toLocaleTimeString(), agent: 'Planner' as const, message: '✓ 任务分解完成：5 个子任务', type: 'success' as const },
          { timestamp: new Date().toLocaleTimeString(), agent: 'Librarian' as const, message: '开始检索 arXiv...', type: 'info' as const },
        ]
      },
      {
        agentStatuses: [
          { agent: 'Planner' as const, status: 'completed' as const, message: '✓ 任务分解完成' },
          { agent: 'Librarian' as const, status: 'working' as const, message: '已找到 23 篇论文', progress: 80 },
          { agent: 'Reasoner' as const, status: 'working' as const, message: '开始综合推理...' },
          { agent: 'Verifier' as const, status: 'idle' as const, message: '待启动' },
        ],
        logs: [
          { timestamp: new Date().toLocaleTimeString(), agent: 'Librarian' as const, message: '找到 23 篇相关论文', type: 'success' as const },
          { timestamp: new Date().toLocaleTimeString(), agent: 'Reasoner' as const, message: '开始综合推理...', type: 'info' as const },
        ],
        findings: [
          { id: '1', type: 'conclusion' as const, content: 'Prompt Engineering 可提升代码正确率 15-20%' },
        ]
      },
      {
        // 触发运算确认
        stage: 'compute' as const,
        executionPlan: mockExecutionPlan(),
      }
    ]

    let stageIndex = 0
    const interval = setInterval(() => {
      const { session } = get()
      if (!session) {
        clearInterval(interval)
        return
      }

      if (stageIndex >= stages.length) {
        clearInterval(interval)
        return
      }

      const update = stages[stageIndex]
      set({
        session: {
          ...session,
          ...update,
          logs: [...session.logs, ...(update.logs || [])],
          findings: [...session.findings, ...(update.findings || [])]
        }
      })
      stageIndex++
    }, 3000)
  },

  handleComputeDecision: (decision) => {
    const { session } = get()
    if (!session) return

    if (decision === 'execute') {
      set({
        session: {
          ...session,
          stage: 'monitoring',
          computeStatus: {
            stage: '分析论文引用关系',
            currentItem: '第 1/23 篇论文',
            progress: 0,
            totalItems: 23
          }
        }
      })
      // 模拟运算进度
      let progress = 0
      const interval = setInterval(() => {
        progress += 10
        const { session } = get()
        if (!session || progress > 100) {
          clearInterval(interval)
          // 运算完成，进入交付
          if (session) {
            set({
              session: {
                ...session,
                stage: 'delivery',
                deliverable: mockDeliverable()
              }
            })
          }
          return
        }
        set({
          session: {
            ...session,
            computeStatus: {
              stage: '分析论文引用关系',
              currentItem: `第 ${Math.ceil(progress / 100 * 23)}/23 篇论文`,
              progress,
              totalItems: 23
            }
          }
        })
      }, 1000)
    } else {
      // 跳过或降级，直接进入交付
      set({
        session: {
          ...session,
          stage: 'delivery',
          deliverable: mockDeliverable()
        }
      })
    }
  },

  selectNextStep: (optionId) => {
    const { session } = get()
    if (!session) return

    // 开始下一轮
    set({
      session: {
        ...session,
        stage: 'running',
        currentRound: session.currentRound + 1,
        agentStatuses: [
          { agent: 'Planner', status: 'working', message: '规划下一轮任务...' },
          { agent: 'Librarian', status: 'waiting', message: '等待计划' },
          { agent: 'Reasoner', status: 'idle', message: '待启动' },
          { agent: 'Verifier', status: 'idle', message: '待启动' },
        ],
        logs: [
          ...session.logs,
          { timestamp: new Date().toLocaleTimeString(), agent: 'Planner', message: `开始 Round ${session.currentRound + 1}...`, type: 'info' }
        ]
      }
    })
    setTimeout(() => get().simulateProgress(), 2000)
  },

  stopResearch: () => {
    const { session } = get()
    if (!session) return

    set({
      session: {
        ...session,
        stage: 'delivery',
        deliverable: mockDeliverable()
      }
    })
  }
}))

