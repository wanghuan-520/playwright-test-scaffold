// ═══════════════════════════════════════════════════════════════
// 运算监控面板
// ═══════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import { Cpu, Activity, FileText, AlertCircle } from 'lucide-react'

export function MonitoringStage() {
  const session = useResearchStore(state => state.session)
  const stopResearch = useResearchStore(state => state.stopResearch)

  if (!session?.computeStatus) return null

  const { computeStatus } = session

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 标题 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white flex items-center justify-center gap-3">
          <Cpu className="w-6 h-6 text-indigo-400 animate-pulse" />
          程序运算中...
        </h1>
        <p className="text-slate-400 mt-2">⏱️ 01:23</p>
      </div>

      {/* 状态时间线 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            状态时间线
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {['初始化', '数据加载', '分析中', '生成图谱'].map((step, i) => {
              const isCompleted = i < 2
              const isCurrent = i === 2
              return (
                <div key={step} className="flex-1 text-center relative">
                  {i < 3 && (
                    <div className={`absolute top-4 left-1/2 w-full h-0.5 ${
                      isCompleted ? 'bg-indigo-500' : 'bg-slate-700'
                    }`} />
                  )}
                  <div className={`relative z-10 w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${
                    isCompleted ? 'bg-indigo-500' :
                    isCurrent ? 'bg-indigo-500 animate-pulse' :
                    'bg-slate-700'
                  }`}>
                    {isCompleted ? '✓' : isCurrent ? '●' : '○'}
                  </div>
                  <p className={`text-sm ${isCurrent ? 'text-white' : 'text-slate-400'}`}>{step}</p>
                  <p className="text-xs text-slate-500">
                    {i === 0 ? '0:05' : i === 1 ? '0:32' : i === 2 ? '1:23' : '~2:30'}
                  </p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* 当前阶段 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            当前阶段：{computeStatus.stage}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-300">
            正在处理：{computeStatus.currentItem}
          </p>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{computeStatus.progress}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div 
                className="bg-indigo-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${computeStatus.progress}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 中间结果快照 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔍 中间结果快照
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-slate-900 rounded-lg font-mono text-sm text-slate-400">
            <pre>{`
              ┌─────┐
              │GPT-4│
              └──┬──┘
         ┌──────┴──────┐
      ┌──┴──┐       ┌──┴──┐
      │CoT  │       │ReAct│
      └──┬──┘       └──┬──┘
         │             │
      ...正在构建中...
            `}</pre>
          </div>
        </CardContent>
      </Card>

      {/* 日志摘要 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📋 日志摘要
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-1 font-mono text-xs text-slate-400">
            <p>01:20:15  处理第 14 篇论文完成</p>
            <p>01:21:02  发现 5 条新引用关系</p>
            <p>01:22:18  开始处理第 15 篇论文...</p>
            <p className="text-amber-400 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              01:23:05  ⚠️ 警告：论文 PDF 解析耗时较长
            </p>
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex justify-center">
        <Button variant="danger" size="lg" onClick={stopResearch}>
          ⏹️ 中断运算
        </Button>
      </div>

      {/* 并行提示 */}
      <p className="text-center text-sm text-slate-500">
        ℹ️ 系统仍在并行：Librarian 继续补充证据 | Reasoner 准备结果解读框架
      </p>
    </div>
  )
}

