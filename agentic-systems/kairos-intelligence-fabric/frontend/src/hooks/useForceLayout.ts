import { useEffect, useRef, useCallback } from 'react'
import {
  forceSimulation,
  forceManyBody,
  forceLink,
  forceCenter,
  forceCollide,
} from 'd3-force-3d'
import type { GraphNode, GraphEdge } from '@/types/graph'
import { useGraphStore } from '@/stores/graphStore'

interface SimNode {
  id: string
  x: number
  y: number
  z: number
  vx: number
  vy: number
  vz: number
}

export function useForceLayout(nodes: GraphNode[], edges: GraphEdge[]) {
  const simulationRef = useRef<any>(null)
  const updateNodePositions = useGraphStore((s) => s.updateNodePositions)
  const frameRef = useRef(0)
  const positionsRef = useRef(new Map<string, [number, number, number]>())

  useEffect(() => {
    if (!nodes.length) return

    const simNodes: SimNode[] = nodes.map((n) => ({
      id: n.id,
      x: (Math.random() - 0.5) * 50,
      y: (Math.random() - 0.5) * 50,
      z: (Math.random() - 0.5) * 50,
      vx: 0,
      vy: 0,
      vz: 0,
    }))

    const simLinks = edges.map((e) => ({
      source: e.source,
      target: e.target,
    }))

    const sim = forceSimulation(simNodes, 3)
      .force('charge', forceManyBody().strength(-80))
      .force(
        'link',
        forceLink(simLinks)
          .id((d: any) => d.id)
          .distance(22)
          .strength(0.6),
      )
      .force('center', forceCenter())
      .force('collision', forceCollide().radius(4))
      .alphaDecay(0.02)
      .velocityDecay(0.3)
      .stop()

    // Run initial ticks synchronously for fast convergence
    for (let i = 0; i < 200; i++) sim.tick()

    // Reuse a single Map to avoid GC pressure
    const collectPositions = () => {
      const pos = positionsRef.current
      pos.clear()
      simNodes.forEach((n: SimNode) => pos.set(n.id, [n.x, n.y, n.z]))
      // Pass a new Map reference so Zustand detects the change
      updateNodePositions(new Map(pos))
    }

    collectPositions()

    // Continue with settling animation
    sim.alpha(0.3).restart()
    sim.on('tick', () => {
      frameRef.current++
      if (frameRef.current % 2 === 0) {
        collectPositions()
      }
    })

    simulationRef.current = sim

    return () => {
      sim.stop()
    }
  }, [nodes, edges, updateNodePositions])

  const reheat = useCallback(() => {
    simulationRef.current?.alpha(0.5).restart()
  }, [])

  return { reheat }
}
