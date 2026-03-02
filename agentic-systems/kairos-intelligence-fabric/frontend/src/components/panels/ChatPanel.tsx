import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Wifi, WifiOff, Bot, Trash2 } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useChatStore } from '@/stores/chatStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { sendQuery } from '@/utils/api'

export function ChatPanel() {
  const showPanel = useUIStore((s) => s.showChatPanel)
  const setOpen = useUIStore((s) => s.setChatPanelOpen)
  const messages = useChatStore((s) => s.messages)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const wsConnected = useChatStore((s) => s.wsConnected)
  const activeAgents = useChatStore((s) => s.activeAgents)
  const addMessage = useChatStore((s) => s.addMessage)
  const setStreaming = useChatStore((s) => s.setStreaming)
  const clearMessages = useChatStore((s) => s.clearMessages)
  const { sendMessage: wsSend } = useWebSocket()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const query = input.trim()
    if (!query || isStreaming) return
    setInput('')

    if (wsConnected) {
      wsSend(query)
    } else {
      addMessage({ id: '', role: 'user', content: query, timestamp: Date.now() })
      addMessage({ id: '', role: 'assistant', content: '', timestamp: Date.now(), isStreaming: true })
      setStreaming(true)

      try {
        const result = await sendQuery(query)
        useChatStore.getState().appendToLastMessage(result.response)
      } catch (err) {
        useChatStore.getState().appendToLastMessage(
          `_Error: ${err instanceof Error ? err.message : 'Query failed'}_`,
        )
      } finally {
        setStreaming(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <AnimatePresence>
      {showPanel && (
        <motion.div
          initial={{ y: 400, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed bottom-4 right-4 z-30 w-96 flex flex-col"
          style={{
            height: '520px',
            background: 'rgba(18, 18, 42, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '12px',
          }}
        >
          {/* Header */}
          <div
            className="px-4 py-3 flex items-center justify-between flex-shrink-0"
            style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}
          >
            <div className="flex items-center gap-2">
              <Bot size={18} className="text-indigo-400" />
              <span className="text-base font-semibold text-white/80">Cerebro Agent</span>
              <div className="flex items-center gap-1 ml-2">
                {wsConnected ? (
                  <Wifi size={14} className="text-green-400" />
                ) : (
                  <WifiOff size={14} className="text-white/30" />
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={clearMessages}
                  className="p-1.5 rounded-md hover:bg-white/10 transition-colors"
                  title="Clear chat"
                >
                  <Trash2 size={14} className="text-white/30" />
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-md hover:bg-white/10 transition-colors"
              >
                <X size={16} className="text-white/40" />
              </button>
            </div>
          </div>

          {/* Active agents */}
          {activeAgents.length > 0 && (
            <div className="px-4 py-2 flex flex-wrap gap-1" style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
              {activeAgents.map((agent) => (
                <span
                  key={agent.name}
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    background: agent.status === 'thinking' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    color: agent.status === 'thinking' ? '#818cf8' : 'rgba(255, 255, 255, 0.4)',
                  }}
                >
                  {agent.name}
                </span>
              ))}
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <Bot size={36} className="mx-auto text-white/10 mb-3" />
                <p className="text-sm text-white/30">
                  Ask about your manufacturing data...
                </p>
                <div className="mt-4 space-y-1">
                  {[
                    'What maintenance is needed for CNC Mill A-7?',
                    'Show me the OEE trends',
                    'Which suppliers have quality issues?',
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => { setInput(q); }}
                      className="block w-full text-left text-sm text-white/25 hover:text-white/50 px-3 py-2 rounded hover:bg-white/5 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className="max-w-[85%] px-3 py-2 rounded-lg text-sm leading-relaxed"
                  style={{
                    background: msg.role === 'user'
                      ? 'rgba(99, 102, 241, 0.2)'
                      : 'rgba(255, 255, 255, 0.05)',
                    color: 'rgba(255, 255, 255, 0.8)',
                  }}
                >
                  <div className="whitespace-pre-wrap">{msg.content || (isStreaming ? '...' : '')}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <p className="text-xs text-white/30 mb-1">Sources:</p>
                      {msg.sources.map((s, i) => (
                        <span
                          key={i}
                          className="inline-block text-xs mr-1 mb-1 px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255, 255, 255, 0.4)' }}
                        >
                          {s.label}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            className="px-4 py-3 flex-shrink-0"
            style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}
          >
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2.5"
              style={{ background: 'rgba(255, 255, 255, 0.05)' }}
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your data..."
                disabled={isStreaming}
                className="flex-1 bg-transparent text-sm text-white/80 placeholder:text-white/25 outline-none"
              />
              <button
                onClick={handleSend}
                disabled={isStreaming || !input.trim()}
                className="p-1.5 rounded hover:bg-white/10 transition-colors disabled:opacity-30"
              >
                <Send size={16} className="text-indigo-400" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
