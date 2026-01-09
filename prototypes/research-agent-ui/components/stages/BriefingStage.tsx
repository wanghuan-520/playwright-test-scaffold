// ═══════════════════════════════════════════════════════════════
// 阶段 1：研究简报
// ═══════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import { Target, CheckSquare, AlertTriangle, Map } from 'lucide-react'

export function BriefingStage() {
  const session = useResearchStore(state => state.session)
  const confirmBriefing = useResearchStore(state => state.confirmBriefing)

  if (!session?.briefing) return null

  const { briefing } = session

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-white">📋 研究简报</h1>
        <p className="text-slate-400">确认研究方向和假设</p>
      </div>

      {/* 问题改写 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-indigo-400" />
            问题改写
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">原始问题：</p>
            <p className="text-slate-300">{briefing.originalQuestion}</p>
          </div>
          <div className="space-y-2">
            <p className="text-sm text-slate-400">系统理解：</p>
            <p className="text-white font-medium">{briefing.rewrittenQuestion}</p>
            <ul className="list-disc list-inside text-slate-300 space-y-1">
              {briefing.scope.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="flex flex-wrap gap-2">
            {briefing.keyTerms.map((term, i) => (
              <span key={i} className="px-2 py-1 bg-indigo-900/50 text-indigo-300 rounded text-sm">
                {term}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 假设清单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-green-400" />
            默认假设
            <span className="text-sm text-slate-400 font-normal">（可编辑）</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {briefing.assumptions.map((assumption) => (
              <label key={assumption.id} className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  defaultChecked={assumption.checked}
                  className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-slate-300 group-hover:text-white transition-colors">
                  {assumption.content}
                </span>
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 风险清单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            风险清单
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {briefing.risks.map((risk) => (
              <div key={risk.id} className="flex items-start gap-3">
                <span className={`px-2 py-0.5 rounded text-xs ${
                  risk.level === 'high' ? 'bg-red-900/50 text-red-300' :
                  risk.level === 'medium' ? 'bg-amber-900/50 text-amber-300' :
                  'bg-green-900/50 text-green-300'
                }`}>
                  {risk.level === 'high' ? '高' : risk.level === 'medium' ? '中' : '低'}
                </span>
                <span className="text-slate-300">{risk.content}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 里程碑路线图 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Map className="w-5 h-5 text-blue-400" />
            里程碑路线图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-start">
            {briefing.roadmap.map((milestone, i) => (
              <div key={milestone.round} className="flex-1 text-center relative">
                {i < briefing.roadmap.length - 1 && (
                  <div className="absolute top-4 left-1/2 w-full h-0.5 bg-slate-700" />
                )}
                <div className="relative z-10 w-8 h-8 mx-auto mb-2 rounded-full bg-indigo-900 border-2 border-indigo-500 flex items-center justify-center text-sm text-white">
                  {milestone.round}
                </div>
                <p className="text-white font-medium text-sm">{milestone.title}</p>
                <p className="text-slate-400 text-xs">{milestone.description}</p>
                <p className="text-slate-500 text-xs">{milestone.estimatedTime}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex justify-center gap-4">
        <Button variant="outline" size="lg" onClick={() => confirmBriefing('adjust')}>
          ✏️ 纠偏
        </Button>
        <Button variant="primary" size="lg" onClick={() => confirmBriefing('continue')}>
          ▶️ 继续
        </Button>
      </div>
    </div>
  )
}

