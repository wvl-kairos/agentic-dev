import { create } from 'zustand'
import type { ChatMessage, AgentInfo, SourceAttribution } from '@/types/chat'

interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  activeAgents: AgentInfo[]
  wsConnected: boolean

  addMessage: (message: ChatMessage) => void
  appendToLastMessage: (content: string) => void
  setStreaming: (streaming: boolean) => void
  setActiveAgents: (agents: AgentInfo[]) => void
  updateAgentStatus: (name: string, status: AgentInfo['status']) => void
  setWsConnected: (connected: boolean) => void
  addSourcesToLastMessage: (sources: SourceAttribution[]) => void
  clearMessages: () => void
}

let _nextId = 1

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  activeAgents: [],
  wsConnected: false,

  addMessage: (message) =>
    set((s) => ({ messages: [...s.messages, { ...message, id: message.id || String(_nextId++) }] })),

  appendToLastMessage: (content) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + content }
      }
      return { messages: msgs }
    }),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  setActiveAgents: (agents) => set({ activeAgents: agents }),

  updateAgentStatus: (name, status) =>
    set((s) => ({
      activeAgents: s.activeAgents.map((a) =>
        a.name === name ? { ...a, status } : a,
      ),
    })),

  setWsConnected: (connected) => set({ wsConnected: connected }),

  addSourcesToLastMessage: (sources) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, sources }
      }
      return { messages: msgs }
    }),

  clearMessages: () => set({ messages: [], activeAgents: [] }),
}))
