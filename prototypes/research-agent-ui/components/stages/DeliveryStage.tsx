// ═══════════════════════════════════════════════════════════════
// 阶段 8：交付物中心
// ═══════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResearchStore } from '@/lib/store'
import { FileText, CheckCircle, HelpCircle, ArrowRight, Star, Download } from 'lucide-react'

export function DeliveryStage() {
  const session = useResearchStore(state => state.session)
  const selectNextStep = useResearchStore(state => state.selectNextStep)

  if (!session?.deliverable) return null

  const { deliverable } = session

  const confidenceColors = {
    high: 'text-green-400 bg-green-900/30',
    medium: 'text-amber-400 bg-amber-900/30',
    low: 'text-red-400 bg-red-900/30'
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 标题 */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-white">📦 交付物中心</h1>
        <p className="text-slate-400">Round {session.currentRound} 完成</p>
        <div className="flex items-center justify-center gap-2">
          <span className="text-slate-400">完成度</span>
          <div className="w-32 h-2 bg-slate-700 rounded-full">
            <div 
              className="h-2 bg-indigo-500 rounded-full"
              style={{ width: `${deliverable.completionRate}%` }}
            />
          </div>
          <span className="text-white">{deliverable.completionRate}%</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 论文草稿 */}
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              论文草稿
            </CardTitle>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm">
                <Download className="w-4 h-4 mr-1" />
                MD
              </Button>
              <Button variant="ghost" size="sm">
                <Download className="w-4 h-4 mr-1" />
                PDF
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert prose-sm max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-slate-300 text-sm bg-slate-900 p-4 rounded-lg">
                {deliverable.paperDraft}
              </pre>
            </div>
            <Button variant="outline" size="sm" className="mt-4 w-full">
              ▼ 展开全文
            </Button>
          </CardContent>
        </Card>

        {/* 结论清单 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                已确认结论
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {deliverable.conclusions.map((conclusion) => (
                <div 
                  key={conclusion.id}
                  className="p-3 bg-slate-900/50 rounded-lg border border-slate-700"
                >
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-slate-300">{conclusion.content}</p>
                    <span className={`px-2 py-0.5 rounded text-xs whitespace-nowrap ${confidenceColors[conclusion.confidence]}`}>
                      {conclusion.confidence === 'high' ? '高可信' : conclusion.confidence === 'medium' ? '中可信' : '低可信'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    证据: {conclusion.evidenceCount} 篇 | {conclusion.isVerified ? '✓ 已验证' : '○ 待验证'}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-amber-400" />
                待验证
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {deliverable.pendingItems.map((item, i) => (
                  <li key={i} className="flex items-center gap-2 text-slate-400">
                    <span className="w-1.5 h-1.5 bg-amber-400 rounded-full" />
                    {item}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 下一轮建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowRight className="w-5 h-5 text-indigo-400" />
            下一轮建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {deliverable.nextSteps.map((option) => (
              <div 
                key={option.id}
                className={`p-4 rounded-lg border transition-all cursor-pointer hover:border-indigo-500 ${
                  option.isRecommended 
                    ? 'border-indigo-500 bg-indigo-900/20' 
                    : 'border-slate-700 bg-slate-800/50'
                }`}
                onClick={() => selectNextStep(option.id)}
              >
                {option.isRecommended && (
                  <div className="flex items-center gap-1 text-indigo-400 text-sm mb-2">
                    <Star className="w-4 h-4" />
                    推荐
                  </div>
                )}
                <h4 className="text-white font-medium mb-2">{option.title}</h4>
                <p className="text-slate-400 text-sm mb-3">{option.description}</p>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>⏱️ {option.estimatedTime}</span>
                  <span>预期收益: {option.expectedBenefit === 'high' ? '高' : option.expectedBenefit === 'medium' ? '中' : '低'}</span>
                </div>
                <Button 
                  variant={option.isRecommended ? 'primary' : 'outline'} 
                  size="sm" 
                  className="w-full mt-3"
                >
                  选择此方向
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex justify-center gap-4">
        <Button variant="outline" size="lg">
          ⏹️ 结束研究
        </Button>
        <Button variant="primary" size="lg">
          🔄 自动继续
        </Button>
      </div>
    </div>
  )
}

