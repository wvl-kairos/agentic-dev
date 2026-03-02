export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  agent?: string
  sources?: SourceAttribution[]
  isStreaming?: boolean
}

export interface SourceAttribution {
  type: 'graph' | 'document' | 'knowledge'
  id: string
  label: string
  relevance: number
}

export interface StreamChunk {
  type: 'thinking' | 'content' | 'source' | 'agent' | 'done' | 'error'
  data: string
}

export interface AgentInfo {
  name: string
  type: string
  status: 'idle' | 'thinking' | 'responding' | 'done'
}
