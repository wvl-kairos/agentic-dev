import { useEffect } from 'react'
import { useGraphStore } from '@/stores/graphStore'

export function useGraphData() {
  const fetchGraph = useGraphStore((s) => s.fetchGraph)
  const nodes = useGraphStore((s) => s.nodes)
  const edges = useGraphStore((s) => s.edges)
  const loading = useGraphStore((s) => s.loading)
  const error = useGraphStore((s) => s.error)

  useEffect(() => {
    fetchGraph()
  }, [fetchGraph])

  return { nodes, edges, loading, error }
}
