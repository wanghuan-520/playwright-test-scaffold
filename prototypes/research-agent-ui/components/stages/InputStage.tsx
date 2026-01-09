// ═══════════════════════════════════════════════════════════════
// 阶段 0：输入方向
// ═══════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import type { Constraints } from '@/types'
import { Sparkles, Settings2 } from 'lucide-react'

export function InputStage() {
  const [direction, setDirection] = useState('')
  const [showConstraints, setShowConstraints] = useState(false)
  const [constraints, setConstraints] = useState<Constraints>({
    budget: 'medium',
    speed: 'standard',
    rigor: 5,
    exclusions: ''
  })

  const startResearch = useResearchStore(state => state.startResearch)

  const handleSubmit = () => {
    if (!direction.trim()) return
    startResearch(direction, constraints)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-white flex items-center justify-center gap-3">
          <Sparkles className="w-8 h-8 text-indigo-400" />
          AI 研究助手
        </h1>
        <p className="text-slate-400">输入你的研究方向，让 AI 帮你完成系统性研究</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📝 研究方向
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            placeholder="例如：研究大语言模型在代码生成领域的最新进展，重点关注 Prompt Engineering 技术..."
            className="w-full h-32 px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />

          <button
            onClick={() => setShowConstraints(!showConstraints)}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <Settings2 className="w-4 h-4" />
            {showConstraints ? '收起' : '展开'}研究边界设置
          </button>

          {showConstraints && (
            <div className="space-y-4 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
              {/* 预算 */}
              <div className="space-y-2">
                <label className="text-sm text-slate-300">💰 预算级别</label>
                <div className="flex gap-2">
                  {(['low', 'medium', 'high'] as const).map((level) => (
                    <button
                      key={level}
                      onClick={() => setConstraints({ ...constraints, budget: level })}
                      className={`px-4 py-2 rounded-lg text-sm transition-all ${
                        constraints.budget === level
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                    >
                      {level === 'low' ? '低' : level === 'medium' ? '中' : '高'}
                    </button>
                  ))}
                </div>
              </div>

              {/* 速度 */}
              <div className="space-y-2">
                <label className="text-sm text-slate-300">⚡ 速度偏好</label>
                <div className="flex gap-2">
                  {(['fast', 'standard', 'deep'] as const).map((speed) => (
                    <button
                      key={speed}
                      onClick={() => setConstraints({ ...constraints, speed })}
                      className={`px-4 py-2 rounded-lg text-sm transition-all ${
                        constraints.speed === speed
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                    >
                      {speed === 'fast' ? '快速' : speed === 'standard' ? '标准' : '深度'}
                    </button>
                  ))}
                </div>
              </div>

              {/* 严谨度 */}
              <div className="space-y-2">
                <label className="text-sm text-slate-300">📊 严谨度 ({constraints.rigor}/10)</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={constraints.rigor}
                  onChange={(e) => setConstraints({ ...constraints, rigor: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>

              {/* 禁止项 */}
              <div className="space-y-2">
                <label className="text-sm text-slate-300">🚫 禁止项</label>
                <input
                  type="text"
                  value={constraints.exclusions}
                  onChange={(e) => setConstraints({ ...constraints, exclusions: e.target.value })}
                  placeholder="不涉及的领域，用逗号分隔"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            className="w-full"
            onClick={handleSubmit}
            disabled={!direction.trim()}
          >
            🚀 开始研究
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

