import { useRef, useMemo, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Mesh, MeshStandardMaterial } from 'three'
import type { GraphNode as GraphNodeType, NodeType } from '@/types/graph'
import { useGraphStore } from '@/stores/graphStore'
import { NODE_COLORS, getNodeRadius } from '@/utils/colors'

interface Props {
  node: GraphNodeType
  position: [number, number, number]
}

function NodeGeometry({ type }: { type: NodeType }) {
  switch (type) {
    case 'equipment':
      return <sphereGeometry args={[1, 16, 16]} />
    case 'orders':
      return <boxGeometry args={[1.4, 1.4, 1.4]} />
    case 'products':
      return <icosahedronGeometry args={[1.1, 0]} />
    case 'quality':
      return <octahedronGeometry args={[1.0, 0]} />
    case 'people':
      return <torusGeometry args={[0.8, 0.3, 8, 16]} />
    case 'suppliers':
      return <octahedronGeometry args={[1.0, 0]} />
    case 'production_lines':
      return <capsuleGeometry args={[0.5, 1.5, 4, 8]} />
    case 'document':
      return <cylinderGeometry args={[0.8, 0.8, 1.4, 8]} />
    case 'knowledge':
      return <dodecahedronGeometry args={[0.9, 0]} />
    default:
      return <sphereGeometry args={[1, 12, 12]} />
  }
}

export function GraphNode({ node, position }: Props) {
  const meshRef = useRef<Mesh>(null)
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const hoveredNodeId = useGraphStore((s) => s.hoveredNodeId)
  const selectNode = useGraphStore((s) => s.selectNode)
  const hoverNode = useGraphStore((s) => s.hoverNode)

  const isSelected = selectedNodeId === node.id
  const isHovered = hoveredNodeId === node.id
  const color = NODE_COLORS[node.type] || '#ffffff'
  const radius = getNodeRadius(node.type)

  const targetScale = isSelected ? 1.3 : isHovered ? 1.2 : 1.0
  const targetEmissive = isSelected ? 0.8 : isHovered ? 0.5 : 0.2

  // Rotation for suppliers (diamond look)
  const rotation = useMemo<[number, number, number]>(
    () => (node.type === 'suppliers' ? [0, 0, Math.PI / 4] : [0, 0, 0]),
    [node.type],
  )

  const handleClick = useCallback(
    (e: { stopPropagation: () => void }) => {
      e.stopPropagation()
      selectNode(node.id)
    },
    [selectNode, node.id],
  )

  const handlePointerOver = useCallback(
    (e: { stopPropagation: () => void }) => {
      e.stopPropagation()
      hoverNode(node.id)
    },
    [hoverNode, node.id],
  )

  const handlePointerOut = useCallback(() => {
    hoverNode(null)
  }, [hoverNode])

  const isInteractive = isSelected || isHovered

  useFrame((_, delta) => {
    if (!meshRef.current) return

    // Only run per-frame animations for selected/hovered nodes
    if (!isInteractive) {
      // Set static scale once and skip further updates
      const currentScale = meshRef.current.scale.x
      if (Math.abs(currentScale - radius) > 0.01) {
        meshRef.current.scale.setScalar(radius)
      }
      return
    }

    // Smooth scale transition
    const s = meshRef.current.scale.x
    const newScale = s + (targetScale * radius - s) * Math.min(delta * 8, 1)
    meshRef.current.scale.setScalar(newScale)

    // Slow idle rotation for interactive nodes
    meshRef.current.rotation.y += delta * 0.3

    // Update emissive intensity
    const mat = meshRef.current.material as MeshStandardMaterial
    if (mat.emissiveIntensity !== undefined) {
      mat.emissiveIntensity +=
        (targetEmissive - mat.emissiveIntensity) * Math.min(delta * 8, 1)
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={position}
      rotation={rotation}
      onClick={handleClick}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
    >
      <NodeGeometry type={node.type} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.2}
        metalness={0.3}
        roughness={0.4}
        toneMapped={false}
      />
    </mesh>
  )
}
