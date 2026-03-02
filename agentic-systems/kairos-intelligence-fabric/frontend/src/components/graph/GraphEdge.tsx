import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import { Vector3, Mesh } from 'three'
import type { GraphEdge as GraphEdgeType } from '@/types/graph'
import { useGraphStore } from '@/stores/graphStore'
import { EDGE_COLORS } from '@/utils/colors'

interface Props {
  edge: GraphEdgeType
  sourcePos: [number, number, number]
  targetPos: [number, number, number]
}

// Reusable Vector3 instances to avoid per-call allocation
const _start = new Vector3()
const _end = new Vector3()
const _mid = new Vector3()
const _dir = new Vector3()
const _perp = new Vector3()

function getCurvePoints(
  source: [number, number, number],
  target: [number, number, number],
): [number, number, number][] {
  _start.set(source[0], source[1], source[2])
  _end.set(target[0], target[1], target[2])
  _mid.addVectors(_start, _end).multiplyScalar(0.5)

  _dir.subVectors(_end, _start)
  const len = _dir.length()
  _perp.set(-_dir.y, _dir.x, _dir.z * 0.3)
    .normalize()
    .multiplyScalar(len * 0.15)
  _mid.add(_perp)

  // 9 points (step 0.125) instead of 21 (step 0.05) — minimal visual difference
  const points: [number, number, number][] = []
  for (let t = 0; t <= 1; t += 0.125) {
    const t2 = t * t
    const mt = 1 - t
    const mt2 = mt * mt
    points.push([
      mt2 * _start.x + 2 * mt * t * _mid.x + t2 * _end.x,
      mt2 * _start.y + 2 * mt * t * _mid.y + t2 * _end.y,
      mt2 * _start.z + 2 * mt * t * _mid.z + t2 * _end.z,
    ])
  }
  return points
}

function FlowParticle({
  points,
  color,
  speed,
  offset,
}: {
  points: [number, number, number][]
  color: string
  speed: number
  offset: number
}) {
  const ref = useRef<Mesh>(null)

  useFrame((state) => {
    if (!ref.current || points.length < 2) return
    const t = ((state.clock.elapsedTime * speed + offset) % 1)
    const idx = Math.floor(t * (points.length - 1))
    const nextIdx = Math.min(idx + 1, points.length - 1)
    const frac = t * (points.length - 1) - idx

    ref.current.position.set(
      points[idx][0] + (points[nextIdx][0] - points[idx][0]) * frac,
      points[idx][1] + (points[nextIdx][1] - points[idx][1]) * frac,
      points[idx][2] + (points[nextIdx][2] - points[idx][2]) * frac,
    )
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.25, 6, 6]} />
      <meshBasicMaterial color={color} transparent opacity={0.8} toneMapped={false} />
    </mesh>
  )
}

export function GraphEdge({ edge, sourcePos, targetPos }: Props) {
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const color = EDGE_COLORS[edge.type] || '#94a3b8'

  const isConnected =
    selectedNodeId === edge.source || selectedNodeId === edge.target
  const opacity = selectedNodeId ? (isConnected ? 0.8 : 0.08) : 0.3

  const curvePoints = useMemo(
    () => getCurvePoints(sourcePos, targetPos),
    [sourcePos, targetPos],
  )

  const linePoints = useMemo(
    () => curvePoints.map(([x, y, z]) => new Vector3(x, y, z)),
    [curvePoints],
  )

  return (
    <group>
      <Line
        points={linePoints}
        color={color}
        lineWidth={isConnected ? 2 : 0.8}
        transparent
        opacity={opacity}
      />
      {/* Flow particles - show more when edge is connected to selection */}
      {(isConnected || !selectedNodeId) && (
        <>
          <FlowParticle points={curvePoints} color={color} speed={0.3} offset={0} />
          {isConnected && (
            <FlowParticle points={curvePoints} color={color} speed={0.3} offset={0.5} />
          )}
        </>
      )}
    </group>
  )
}
