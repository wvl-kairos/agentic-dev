import type { GraphResponse } from '@/types/graph'
import type { DocumentListResponse, IngestionStatus } from '@/types/document'

const API_BASE = import.meta.env.VITE_API_URL || ''

export async function fetchGraphData(): Promise<GraphResponse> {
  const res = await fetch(`${API_BASE}/api/graph`)
  if (!res.ok) {
    throw new Error(`Failed to fetch graph: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    return res.ok
  } catch {
    return false
  }
}

export async function fetchDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${API_BASE}/api/documents`)
  if (!res.ok) {
    throw new Error(`Failed to fetch documents: ${res.status}`)
  }
  return res.json()
}

export async function uploadDocument(file: File): Promise<{ id: string; title: string; filename: string; status: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`)
  }
  return res.json()
}

export async function triggerIngestion(docId: string): Promise<IngestionStatus> {
  const res = await fetch(`${API_BASE}/api/ingest/${docId}`, {
    method: 'POST',
  })
  if (!res.ok) {
    throw new Error(`Ingestion trigger failed: ${res.status}`)
  }
  return res.json()
}

export async function getIngestionStatus(docId: string): Promise<IngestionStatus> {
  const res = await fetch(`${API_BASE}/api/ingest/${docId}/status`)
  if (!res.ok) {
    throw new Error(`Failed to get ingestion status: ${res.status}`)
  }
  return res.json()
}

export async function sendQuery(query: string): Promise<{ response: string; sources: unknown[] }> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) {
    throw new Error(`Query failed: ${res.status}`)
  }
  return res.json()
}

export async function resetGraph(): Promise<GraphResponse> {
  const res = await fetch(`${API_BASE}/api/graph/reset`, { method: 'POST' })
  if (!res.ok) {
    throw new Error(`Reset failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export function getWebSocketUrl(): string {
  const wsBase = API_BASE.replace(/^http/, 'ws') || `ws://${window.location.host}`
  return `${wsBase}/ws/chat`
}
