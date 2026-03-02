import { Color } from 'three'
import type { NodeType, EdgeType } from '@/types/graph'

export const NODE_COLORS: Record<NodeType, string> = {
  equipment: '#3b82f6',
  orders: '#f59e0b',
  products: '#22c55e',
  quality: '#ef4444',
  people: '#a855f7',
  suppliers: '#06b6d4',
  production_lines: '#f97316',
  document: '#ec4899',
  knowledge: '#14b8a6',
}

export const EDGE_COLORS: Record<EdgeType, string> = {
  PRODUCES: '#22c55e',
  REQUIRES: '#f59e0b',
  INSPECTED_BY: '#ef4444',
  SUPPLIED_BY: '#06b6d4',
  BELONGS_TO: '#94a3b8',
  DEPENDS_ON: '#f97316',
  DOCUMENTED_IN: '#ec4899',
  EXTRACTED_FROM: '#14b8a6',
  RELATES_TO: '#8b5cf6',
  CITES: '#64748b',
}

export function hexToThreeColor(hex: string): Color {
  return new Color(hex)
}

export function getNodeRadius(type: NodeType): number {
  switch (type) {
    case 'production_lines':
      return 2.3
    case 'equipment':
      return 1.7
    case 'orders':
      return 1.5
    case 'products':
      return 1.5
    case 'quality':
      return 1.3
    case 'people':
      return 1.3
    case 'suppliers':
      return 1.4
    case 'document':
      return 1.8
    case 'knowledge':
      return 1.2
    default:
      return 1.3
  }
}
