// ═══════════════════════════════════════════════════════════════
// 主页面 - 根据阶段渲染不同组件
// ═══════════════════════════════════════════════════════════════

'use client'

import { useResearchStore } from '@/lib/store'
import { 
  InputStage, 
  BriefingStage, 
  RunningStage, 
  ComputeStage,
  MonitoringStage,
  DeliveryStage 
} from '@/components/stages'
import { History, Settings } from 'lucide-react'

export default function Home() {
  const session = useResearchStore(state => state.session)

  const renderStage = () => {
    if (!session) {
      return <InputStage />
    }

    switch (session.stage) {
      case 'briefing':
        return <BriefingStage />
      case 'running':
        return <RunningStage />
      case 'compute':
        return <ComputeStage />
      case 'monitoring':
        return <MonitoringStage />
      case 'delivery':
        return <DeliveryStage />
      default:
        return <InputStage />
    }
  }

  return (
    <main className="min-h-screen">
      {/* 顶部导航 */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔬</span>
            <span className="font-semibold text-white">AI 研究助手</span>
            {session && (
              <span className="px-2 py-0.5 bg-indigo-900 text-indigo-300 rounded text-xs ml-2">
                {session.stage === 'input' ? '输入' :
                 session.stage === 'briefing' ? '简报' :
                 session.stage === 'running' ? `Round ${session.currentRound}` :
                 session.stage === 'compute' ? '运算确认' :
                 session.stage === 'monitoring' ? '运算中' :
                 '交付中心'}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <button className="text-slate-400 hover:text-white transition-colors flex items-center gap-1">
              <History className="w-4 h-4" />
              <span className="text-sm">历史</span>
            </button>
            <button className="text-slate-400 hover:text-white transition-colors flex items-center gap-1">
              <Settings className="w-4 h-4" />
              <span className="text-sm">设置</span>
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="pt-20 pb-12 px-6">
        {renderStage()}
      </div>

      {/* 底部状态栏 */}
      {session && (
        <footer className="fixed bottom-0 left-0 right-0 bg-slate-900/80 backdrop-blur-sm border-t border-slate-800">
          <div className="max-w-7xl mx-auto px-6 py-2 flex items-center justify-between text-xs text-slate-400">
            <span>Session: {session.id.slice(0, 12)}...</span>
            <span>
              状态: {
                session.stage === 'briefing' ? '等待确认' :
                session.stage === 'running' ? '调研中' :
                session.stage === 'compute' ? '等待决策' :
                session.stage === 'monitoring' ? '运算中' :
                '完成'
              }
            </span>
          </div>
        </footer>
      )}
    </main>
  )
}

