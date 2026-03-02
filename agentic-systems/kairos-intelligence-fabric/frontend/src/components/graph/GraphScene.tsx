import { useMemo } from 'react'
import { useGraphStore } from '@/stores/graphStore'
import { useForceLayout } from '@/hooks/useForceLayout'
import { GraphNode } from './GraphNode'
import { GraphEdge } from './GraphEdge'
import { NodeLabel } from './NodeLabel'

export function GraphScene() {
  const nodes = useGraphStore((s) => s.nodes)
  const edges = useGraphStore((s) => s.edges)
  const nodePositions = useGraphStore((s) => s.nodePositions)

  useForceLayout(nodes, edges)

  // Create a lookup for edge positions
  const edgeElements = useMemo(() => {
    if (nodePositions.size === 0) return null

    return edges.map((edge) => {
      const sourcePos = nodePositions.get(edge.source)
      const targetPos = nodePositions.get(edge.target)
      if (!sourcePos || !targetPos) return null

      return (
        <GraphEdge
          key={`${edge.source}:${edge.target}:${edge.type}`}
          edge={edge}
          sourcePos={sourcePos}
          targetPos={targetPos}
        />
      )
    })
  }, [edges, nodePositions])

  const nodeElements = useMemo(() => {
    if (nodePositions.size === 0) return null

    return nodes.map((node) => {
      const pos = nodePositions.get(node.id)
      if (!pos) return null

      return (
        <group key={node.id}>
          <GraphNode node={node} position={pos} />
          <NodeLabel node={node} position={pos} />
        </group>
      )
    })
  }, [nodes, nodePositions])

  return (
    <group>
      {edgeElements}
      {nodeElements}
    </group>
  )
}
