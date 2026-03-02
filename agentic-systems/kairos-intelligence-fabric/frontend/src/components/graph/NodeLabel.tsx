import { Html } from '@react-three/drei'
import type { GraphNode } from '@/types/graph'
import { useUIStore } from '@/stores/uiStore'
import { useGraphStore } from '@/stores/graphStore'
import { NODE_COLORS } from '@/utils/colors'

interface Props {
  node: GraphNode
  position: [number, number, number]
}

export function NodeLabel({ node, position }: Props) {
  const zoomLevel = useUIStore((s) => s.zoomLevel)
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const hoveredNodeId = useGraphStore((s) => s.hoveredNodeId)

  const isActive = selectedNodeId === node.id || hoveredNodeId === node.id

  // Semantic zoom: only show labels when close enough or when active
  if (zoomLevel === 'far' && !isActive) return null

  const color = NODE_COLORS[node.type] || '#ffffff'

  return (
    <Html
      position={[position[0], position[1] + 2.5, position[2]]}
      center
      distanceFactor={zoomLevel === 'close' ? 15 : 25}
      style={{
        pointerEvents: 'none',
        userSelect: 'none',
        whiteSpace: 'nowrap',
      }}
    >
      <div
        className="px-2 py-1 rounded-md text-center"
        style={{
          background: 'rgba(10, 10, 26, 0.85)',
          backdropFilter: 'blur(8px)',
          border: `1px solid ${color}33`,
          fontSize: isActive ? '12px' : '10px',
          fontFamily: 'Inter, sans-serif',
          color: '#e2e8f0',
          opacity: isActive ? 1 : 0.8,
          transition: 'all 200ms ease-out',
        }}
      >
        <span style={{ color, fontWeight: 600 }}>{node.label}</span>
        {(zoomLevel === 'close' || isActive) && (
          <div
            style={{
              fontSize: '8px',
              color: '#94a3b8',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop: '2px',
            }}
          >
            {node.type.replace('_', ' ')}
          </div>
        )}
      </div>
    </Html>
  )
}
