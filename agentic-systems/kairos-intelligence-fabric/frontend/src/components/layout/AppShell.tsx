import { AlertTriangle } from 'lucide-react'
import { GraphCanvas } from '@/components/graph/GraphCanvas'
import { TopBar } from '@/components/layout/TopBar'
import { NodeDetailPanel } from '@/components/panels/NodeDetailPanel'
import { DocumentUploadPanel } from '@/components/panels/DocumentUploadPanel'
import { ChatPanel } from '@/components/panels/ChatPanel'
import { AgentActivityPanel } from '@/components/panels/AgentActivityPanel'
import { LoadingOrb } from '@/components/ui/LoadingOrb'
import { useGraphData } from '@/hooks/useGraphData'

export function AppShell() {
  const { loading, error } = useGraphData()

  return (
    <div className="w-full h-full relative">
      <LoadingOrb isVisible={loading} />

      {error && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background">
          <div className="text-center glass-panel p-8 max-w-md">
            <AlertTriangle size={40} className="mx-auto mb-4 text-warning" />
            <h2 className="text-lg font-semibold text-white mb-2">
              Connection Error
            </h2>
            <p className="text-sm text-white/50 mb-4">
              Unable to connect to the Cerebro backend service.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-button text-sm font-medium"
              style={{
                background: 'rgba(99, 102, 241, 0.2)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#6366f1',
              }}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {!loading && !error && (
        <>
          <GraphCanvas />
          <TopBar />
          <NodeDetailPanel />
          <DocumentUploadPanel />
          <ChatPanel />
          <AgentActivityPanel />

          {/* Tagline */}
          <div className="fixed bottom-4 left-4 z-20">
            <p
              className="text-xs font-mono tracking-widest"
              style={{ color: 'rgba(255, 255, 255, 0.3)' }}
            >
              See Your Factory Think
            </p>
          </div>
        </>
      )}
    </div>
  )
}
