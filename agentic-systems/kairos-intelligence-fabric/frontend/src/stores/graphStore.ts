import { create } from 'zustand'
import type { GraphEdge, GraphMetadata, GraphNode } from '@/types/graph'
import { fetchGraphData } from '@/utils/api'

interface GraphState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: GraphMetadata | null
  nodePositions: Map<string, [number, number, number]>
  selectedNodeId: string | null
  hoveredNodeId: string | null
  loading: boolean
  error: string | null

  fetchGraph: () => Promise<void>
  setGraphData: (data: { nodes: GraphNode[]; edges: GraphEdge[]; metadata: GraphMetadata }) => void
  selectNode: (id: string | null) => void
  hoverNode: (id: string | null) => void
  updateNodePositions: (positions: Map<string, [number, number, number]>) => void
  addNodes: (nodes: GraphNode[]) => void
  addEdges: (edges: GraphEdge[]) => void
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  metadata: null,
  nodePositions: new Map(),
  selectedNodeId: null,
  hoveredNodeId: null,
  loading: false,
  error: null,

  fetchGraph: async () => {
    set({ loading: true, error: null })
    const minDisplay = new Promise((r) => setTimeout(r, 1800))
    try {
      const [data] = await Promise.all([fetchGraphData(), minDisplay])
      set({
        nodes: data.nodes,
        edges: data.edges,
        metadata: data.metadata,
        loading: false,
      })
    } catch (err) {
      await minDisplay
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch graph',
        loading: false,
      })
    }
  },

  setGraphData: (data) =>
    set({
      nodes: data.nodes,
      edges: data.edges,
      metadata: data.metadata,
    }),

  selectNode: (id) => {
    const current = get().selectedNodeId
    set({ selectedNodeId: current === id ? null : id })
  },

  hoverNode: (id) => set({ hoveredNodeId: id }),

  updateNodePositions: (positions) => set({ nodePositions: positions }),

  addNodes: (newNodes) =>
    set((s) => {
      const existingIds = new Set(s.nodes.map((n) => n.id))
      const toAdd = newNodes.filter((n) => !existingIds.has(n.id))
      if (toAdd.length === 0) return s
      return { nodes: [...s.nodes, ...toAdd] }
    }),

  addEdges: (newEdges) =>
    set((s) => {
      const existingKeys = new Set(
        s.edges.map((e) => `${e.source}:${e.target}:${e.type}`),
      )
      const toAdd = newEdges.filter(
        (e) => !existingKeys.has(`${e.source}:${e.target}:${e.type}`),
      )
      if (toAdd.length === 0) return s
      return { edges: [...s.edges, ...toAdd] }
    }),
}))

// Derived selectors
export const useConnectedEdges = (nodeId: string | null) =>
  useGraphStore((s) =>
    nodeId
      ? s.edges.filter((e) => e.source === nodeId || e.target === nodeId)
      : [],
  )

export const useConnectedNodeIds = (nodeId: string | null) =>
  useGraphStore((s) => {
    if (!nodeId) return new Set<string>()
    const ids = new Set<string>()
    for (const e of s.edges) {
      if (e.source === nodeId) ids.add(e.target)
      if (e.target === nodeId) ids.add(e.source)
    }
    return ids
  })
