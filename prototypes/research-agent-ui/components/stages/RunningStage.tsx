// ═══════════════════════════════════════════════════════════════
// 阶段 2-6：并行调研进度面板
// ═══════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import { Bot, FileText, Brain, Shield, Loader2, Check, Clock, AlertCircle } from 'lucide-react'
import type { AgentType, AgentStatusType } from '@/types'

const agentIcons: Record<AgentType, React.ReactNode> = {
  Planner: <FileText className="w-5 h-5" />,
  Librarian: <Bot className="w-5 h-5" />,
  Reasoner: <Brain className="w-5 h-5" />,
  Verifier: <Shield className="w-5 h-5" />,
  Compute: <Loader2 className="w-5 h-5" />
}

const statusIcons: Record<AgentStatusType, React.ReactNode> = {
  idle: <Clock className="w-4 h-4 text-slate-500" />,
  waiting: <Clock className="w-4 h-4 text-amber-400" />,
  working: <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />,
  completed: <Check className="w-4 h-4 text-green-400" />,
  error: <AlertCircle className="w-4 h-4 text-red-400" />
}

export function RunningStage() {
  const session = useResearchStore(state => state.session)
  const stopResearch = useResearchStore(state => state.stopResearch)

  if (!session) return null

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            📊 Round {session.currentRound} - 深度分析
          </h1>
          <p className="text-slate-400">系统正在自动调研中...</p>
        </div>
        <div className="text-right">
          <span className="text-slate-400">⏱️</span>
          <span className="text-white ml-2 font-mono">12:34</span>
        </div>
      </div>

      {/* 进度条 */}
      <div className="w-full bg-slate-800 rounded-full h-2">
        <div 
          className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
          style={{ width: '45%' }}
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Agent 状态 */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>🤖 Agent 工作状态</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {session.agentStatuses.map((agent) => (
                <div 
                  key={agent.agent}
                  className={`p-4 rounded-lg border ${
                    agent.status === 'working' ? 'border-indigo-500 bg-indigo-900/20' :
                    agent.status === 'completed' ? 'border-green-500 bg-green-900/20' :
                    'border-slate-700 bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-slate-300">{agentIcons[agent.agent]}</span>
                    <span className="font-medium text-white">{agent.agent}</span>
                    {statusIcons[agent.status]}
                  </div>
                  <p className="text-sm text-slate-400">{agent.message}</p>
                  {agent.progress !== undefined && (
                    <div className="mt-2 w-full bg-slate-700 rounded-full h-1">
                      <div 
                        className="bg-indigo-500 h-1 rounded-full"
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 实时日志 */}
        <Card>
          <CardHeader>
            <CardTitle>📝 实时日志</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-48 overflow-y-auto font-mono text-xs">
              {session.logs.map((log, i) => (
                <div key={i} className={`${
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'warning' ? 'text-amber-400' :
                  log.type === 'error' ? 'text-red-400' :
                  'text-slate-400'
                }`}>
                  <span className="text-slate-500">{log.timestamp}</span>
                  <span className="ml-2">[{log.agent}]</span>
                  <span className="ml-2">{log.message}</span>
                </div>
              ))}
              <div className="text-indigo-400 animate-pulse">█</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 当前发现 */}
      {session.findings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>🎯 当前发现（实时更新）</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {session.findings.filter(f => f.type === 'conclusion').length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">💡 初步结论：</p>
                  <ul className="list-disc list-inside text-slate-300 space-y-1">
                    {session.findings.filter(f => f.type === 'conclusion').map((f) => (
                      <li key={f.id}>{f.content}</li>
                    ))}
                  </ul>
                </div>
              )}
              {session.findings.filter(f => f.type === 'pending').length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">❓ 待验证：</p>
                  <ul className="list-disc list-inside text-slate-300 space-y-1">
                    {session.findings.filter(f => f.type === 'pending').map((f) => (
                      <li key={f.id}>{f.content}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 操作按钮 */}
      <div className="flex justify-center gap-4">
        <Button variant="outline">⏸️ 暂停</Button>
        <Button variant="outline">🔄 改方向</Button>
        <Button variant="danger" onClick={stopResearch}>⏹️ 停止</Button>
      </div>
    </div>
  )
}

