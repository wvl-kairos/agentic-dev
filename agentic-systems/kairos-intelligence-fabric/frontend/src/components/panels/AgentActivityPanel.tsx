import { useChatStore } from '@/stores/chatStore'

export function AgentActivityPanel() {
  const activeAgents = useChatStore((s) => s.activeAgents)
  const isStreaming = useChatStore((s) => s.isStreaming)

  if (!isStreaming || activeAgents.length === 0) return null

  return (
    <div
      className="fixed bottom-20 left-4 z-30 px-4 py-3 rounded-lg"
      style={{
        background: 'rgba(18, 18, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <p className="text-xs text-white/30 mb-1.5">Active Agents</p>
      <div className="space-y-1.5">
        {activeAgents.map((agent) => (
          <div key={agent.name} className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{
                background:
                  agent.status === 'thinking'
                    ? '#818cf8'
                    : agent.status === 'responding'
                      ? '#22c55e'
                      : '#64748b',
                boxShadow:
                  agent.status === 'thinking'
                    ? '0 0 6px rgba(129, 140, 248, 0.5)'
                    : 'none',
              }}
            />
            <span className="text-sm text-white/50">{agent.name}</span>
            <span className="text-xs text-white/25">{agent.status}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
