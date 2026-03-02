import { useEffect, useRef, useCallback } from 'react'
import { getWebSocketUrl } from '@/utils/api'
import { useChatStore } from '@/stores/chatStore'
import type { StreamChunk, SourceAttribution } from '@/types/chat'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const setWsConnected = useChatStore((s) => s.setWsConnected)
  const addMessage = useChatStore((s) => s.addMessage)
  const appendToLastMessage = useChatStore((s) => s.appendToLastMessage)
  const setStreaming = useChatStore((s) => s.setStreaming)
  const updateAgentStatus = useChatStore((s) => s.updateAgentStatus)
  const setActiveAgents = useChatStore((s) => s.setActiveAgents)
  const addSourcesToLastMessage = useChatStore((s) => s.addSourcesToLastMessage)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(getWebSocketUrl())
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
    }

    ws.onclose = () => {
      setWsConnected(false)
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onmessage = (event) => {
      try {
        const chunk: StreamChunk = JSON.parse(event.data)
        switch (chunk.type) {
          case 'content':
            appendToLastMessage(chunk.data)
            break
          case 'thinking':
            // Agent is thinking — could show typing indicator
            break
          case 'agent':
            try {
              const agentData = JSON.parse(chunk.data)
              if (Array.isArray(agentData)) {
                setActiveAgents(agentData)
              } else {
                updateAgentStatus(agentData.name, agentData.status)
              }
            } catch {
              // ignore parse error
            }
            break
          case 'source':
            try {
              const sources: SourceAttribution[] = JSON.parse(chunk.data)
              addSourcesToLastMessage(sources)
            } catch {
              // ignore parse error
            }
            break
          case 'done':
            setStreaming(false)
            break
          case 'error':
            appendToLastMessage(`\n\n_Error: ${chunk.data}_`)
            setStreaming(false)
            break
        }
      } catch {
        // ignore non-JSON messages
      }
    }
  }, [setWsConnected, appendToLastMessage, setStreaming, updateAgentStatus, setActiveAgents, addSourcesToLastMessage, addMessage])

  const sendMessage = useCallback(
    (query: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return false
      }

      // Add user message
      addMessage({
        id: '',
        role: 'user',
        content: query,
        timestamp: Date.now(),
      })

      // Add placeholder assistant message
      addMessage({
        id: '',
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isStreaming: true,
      })

      setStreaming(true)

      // Send query with recent conversation history for context
      const allMessages = useChatStore.getState().messages
      // Grab last 10 messages (excluding the two we just added)
      const history = allMessages.slice(0, -2).slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      wsRef.current.send(JSON.stringify({ query, history }))
      return true
    },
    [addMessage, setStreaming],
  )

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { sendMessage }
}
