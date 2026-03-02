export type NodeType =
  | 'equipment'
  | 'orders'
  | 'products'
  | 'quality'
  | 'people'
  | 'suppliers'
  | 'production_lines'
  | 'document'
  | 'knowledge'

export type EdgeType =
  | 'PRODUCES'
  | 'REQUIRES'
  | 'INSPECTED_BY'
  | 'SUPPLIED_BY'
  | 'BELONGS_TO'
  | 'DEPENDS_ON'
  | 'DOCUMENTED_IN'
  | 'EXTRACTED_FROM'
  | 'RELATES_TO'
  | 'CITES'

export interface GraphNode {
  id: string
  type: NodeType
  label: string
  properties: Record<string, unknown>
  position: [number, number, number] | null
}

export interface GraphEdge {
  source: string
  target: string
  type: EdgeType
  properties: Record<string, unknown>
}

export interface GraphMetadata {
  total_nodes: number
  total_edges: number
  ontology_version: string
  last_updated: string
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: GraphMetadata
}

export type SemanticZoomLevel = 'far' | 'medium' | 'close'
