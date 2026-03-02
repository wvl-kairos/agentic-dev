import { Vector3, QuadraticBezierCurve3 } from 'three'
import type { SemanticZoomLevel } from '@/types/graph'

export function getSemanticZoomLevel(distance: number): SemanticZoomLevel {
  if (distance > 200) return 'far'
  if (distance > 80) return 'medium'
  return 'close'
}

export function getEdgeCurvePoints(
  source: [number, number, number],
  target: [number, number, number],
  curveAmount: number = 0.3,
): Vector3[] {
  const start = new Vector3(...source)
  const end = new Vector3(...target)
  const mid = new Vector3().addVectors(start, end).multiplyScalar(0.5)

  // Offset control point perpendicular to the line
  const dir = new Vector3().subVectors(end, start)
  const perp = new Vector3(-dir.y, dir.x, dir.z * 0.5).normalize()
  mid.add(perp.multiplyScalar(dir.length() * curveAmount))

  const curve = new QuadraticBezierCurve3(start, mid, end)
  return curve.getPoints(20)
}

export function getNodeScale(isHovered: boolean, isSelected: boolean): number {
  if (isSelected) return 1.3
  if (isHovered) return 1.2
  return 1.0
}
