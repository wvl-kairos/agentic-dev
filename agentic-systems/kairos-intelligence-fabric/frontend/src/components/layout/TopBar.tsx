import { useGraphStore } from '@/stores/graphStore'
import { useUIStore } from '@/stores/uiStore'
import { useChatStore } from '@/stores/chatStore'
import { useEffect, useState } from 'react'
import { checkHealth, resetGraph } from '@/utils/api'
import { FileUp, MessageSquare, RotateCcw } from 'lucide-react'

export function TopBar() {
  const metadata = useGraphStore((s) => s.metadata)
  const fetchGraph = useGraphStore((s) => s.fetchGraph)
  const [isConnected, setIsConnected] = useState(false)
  const toggleUploadPanel = useUIStore((s) => s.toggleUploadPanel)
  const toggleChatPanel = useUIStore((s) => s.toggleChatPanel)
  const showUploadPanel = useUIStore((s) => s.showUploadPanel)
  const showChatPanel = useUIStore((s) => s.showChatPanel)
  const clearMessages = useChatStore((s) => s.clearMessages)
  const selectNode = useGraphStore((s) => s.selectNode)

  useEffect(() => {
    checkHealth().then(setIsConnected)
    const interval = setInterval(() => {
      checkHealth().then(setIsConnected)
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const [resetting, setResetting] = useState(false)

  const handleReset = async () => {
    setResetting(true)
    clearMessages()
    useChatStore.getState().setStreaming(false)
    selectNode(null)
    useUIStore.getState().setUploadPanelOpen(false)
    try {
      const data = await resetGraph()
      useGraphStore.getState().setGraphData(data)
      window.dispatchEvent(new Event('kairos:graph-reset'))
    } catch {
      // Fallback: just refetch current graph
      await fetchGraph()
    } finally {
      setResetting(false)
    }
  }

  return (
    <div
      className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-6 py-4"
      style={{
        background: 'rgba(10, 10, 26, 0.7)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-base font-bold"
          style={{
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.3)',
          }}
        >
          C
        </div>
        <div>
          <span className="text-base font-semibold tracking-wide text-white/90">
            Cerebro
          </span>
          <span className="text-base font-light tracking-wide text-white/50 ml-1.5">
            Intelligence Fabric
          </span>
        </div>
      </div>

      {/* Actions + Stats */}
      <div className="flex items-center gap-5">
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleUploadPanel}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors"
            style={{
              background: showUploadPanel ? 'rgba(236, 72, 153, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              color: showUploadPanel ? '#ec4899' : 'rgba(255, 255, 255, 0.6)',
              border: `1px solid ${showUploadPanel ? 'rgba(236, 72, 153, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
            }}
          >
            <FileUp size={16} />
            <span>Docs</span>
          </button>

          <button
            onClick={toggleChatPanel}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors"
            style={{
              background: showChatPanel ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              color: showChatPanel ? '#818cf8' : 'rgba(255, 255, 255, 0.6)',
              border: `1px solid ${showChatPanel ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
            }}
          >
            <MessageSquare size={16} />
            <span>Chat</span>
          </button>

          <button
            onClick={handleReset}
            disabled={resetting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors"
            style={{
              background: resetting ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              color: resetting ? '#f87171' : 'rgba(255, 255, 255, 0.6)',
              border: `1px solid ${resetting ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
            }}
            title="Reset graph to baseline (before ingestion)"
          >
            <RotateCcw size={16} className={resetting ? 'animate-spin' : ''} />
            <span>{resetting ? 'Resetting...' : 'Reset'}</span>
          </button>
        </div>

        {/* Stats */}
        {metadata && (
          <div className="flex items-center gap-5 text-sm font-mono text-white/40">
            <span>
              <span className="text-white/60">{metadata.total_nodes}</span> nodes
            </span>
            <span>
              <span className="text-white/60">{metadata.total_edges}</span> edges
            </span>
            <span>
              v<span className="text-white/60">{metadata.ontology_version}</span>
            </span>
          </div>
        )}

        {/* Connection status */}
        <div className="flex items-center gap-2 text-sm text-white/40">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{
              background: isConnected ? '#22c55e' : '#ef4444',
              boxShadow: isConnected
                ? '0 0 8px rgba(34, 197, 94, 0.5)'
                : '0 0 8px rgba(239, 68, 68, 0.5)',
            }}
          />
          {isConnected ? 'Connected' : 'Offline'}
        </div>
      </div>
    </div>
  )
}
