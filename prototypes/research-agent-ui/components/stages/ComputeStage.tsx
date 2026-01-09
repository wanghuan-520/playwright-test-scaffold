// ═══════════════════════════════════════════════════════════════
// 执行计划卡（运算确认弹窗）
// ═══════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import { Cpu, Package, DollarSign, AlertTriangle, Clock, Lightbulb } from 'lucide-react'

export function ComputeStage() {
  const session = useResearchStore(state => state.session)
  const handleComputeDecision = useResearchStore(state => state.handleComputeDecision)

  if (!session?.executionPlan) return null

  const { executionPlan } = session

  const levelColors = {
    low: 'bg-green-500',
    medium: 'bg-amber-500',
    high: 'bg-red-500'
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="border-indigo-500/50">
        <CardHeader className="border-b border-slate-700">
          <CardTitle className="flex items-center gap-2 text-xl">
            <Cpu className="w-6 h-6 text-indigo-400" />
            需要执行程序运算
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 py-6">
          {/* 运算描述 */}
          <div className="space-y-2">
            <h4 className="text-sm text-slate-400 flex items-center gap-2">
              <Package className="w-4 h-4" />
              运算描述
            </h4>
            <p className="text-white">{executionPlan.description}</p>
          </div>

          {/* 预期产物 */}
          <div className="space-y-2">
            <h4 className="text-sm text-slate-400 flex items-center gap-2">
              <Package className="w-4 h-4" />
              预期产物
            </h4>
            <ul className="list-disc list-inside text-slate-300 space-y-1">
              {executionPlan.expectedOutput.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>

          {/* 成本/风险/时间 */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-400">成本级别</span>
              </div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${levelColors[executionPlan.costLevel]}`}
                    style={{ width: executionPlan.costLevel === 'low' ? '33%' : executionPlan.costLevel === 'medium' ? '66%' : '100%' }}
                  />
                </div>
                <span className="text-white text-sm">
                  {executionPlan.costLevel === 'low' ? '低' : executionPlan.costLevel === 'medium' ? '中' : '高'}
                </span>
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-400">风险级别</span>
              </div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${levelColors[executionPlan.riskLevel]}`}
                    style={{ width: executionPlan.riskLevel === 'low' ? '33%' : executionPlan.riskLevel === 'medium' ? '66%' : '100%' }}
                  />
                </div>
                <span className="text-white text-sm">
                  {executionPlan.riskLevel === 'low' ? '低' : executionPlan.riskLevel === 'medium' ? '中' : '高'}
                </span>
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-400">预计耗时</span>
              </div>
              <span className="text-white">{executionPlan.estimatedTime}</span>
            </div>
          </div>

          {/* 系统推荐 */}
          <div className="p-4 bg-indigo-900/30 border border-indigo-500/50 rounded-lg">
            <div className="flex items-start gap-3">
              <Lightbulb className="w-5 h-5 text-indigo-400 mt-0.5" />
              <div>
                <p className="text-indigo-300 font-medium">
                  系统推荐：{executionPlan.recommendation === 'execute' ? '执行' : executionPlan.recommendation === 'downgrade' ? '降级' : '跳过'}
                </p>
                <p className="text-slate-400 text-sm mt-1">{executionPlan.recommendationReason}</p>
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex justify-center gap-4 pt-4">
            <Button variant="primary" size="lg" onClick={() => handleComputeDecision('execute')}>
              ▶️ 执行
            </Button>
            <Button variant="outline" size="lg" onClick={() => handleComputeDecision('downgrade')}>
              ⬇️ 降级
            </Button>
            <Button variant="ghost" size="lg" onClick={() => handleComputeDecision('skip')}>
              ⏭️ 暂不执行
            </Button>
          </div>

          {/* 降级方案说明 */}
          {executionPlan.downgradePlan && (
            <p className="text-center text-sm text-slate-500">
              ℹ️ 降级方案：{executionPlan.downgradePlan}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

