export interface Document {
  id: string
  title: string
  filename: string
  content_preview: string
  uploaded_at: string
  status: 'uploaded' | 'ingesting' | 'ingested' | 'error'
  size_bytes: number
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

export interface IngestionStatus {
  document_id: string
  status: string
  result: {
    entities_extracted: number
    entities_resolved: number
    edges_created: number
    nodes_created: number
    graph_total_nodes: number
    graph_total_edges: number
    error_message: string | null
  } | null
}
