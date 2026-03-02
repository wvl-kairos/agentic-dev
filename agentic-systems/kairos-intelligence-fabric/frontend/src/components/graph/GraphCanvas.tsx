import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { BackgroundEnvironment } from './BackgroundEnvironment'
import { PostProcessing } from './PostProcessing'
import { CameraController } from './CameraController'
import { GraphScene } from './GraphScene'
import { useGraphStore } from '@/stores/graphStore'

function CursorManager() {
  const hoveredNodeId = useGraphStore((s) => s.hoveredNodeId)
  const canvas = document.querySelector('canvas')
  if (canvas) {
    canvas.style.cursor = hoveredNodeId ? 'pointer' : 'default'
  }
  return null
}

export function GraphCanvas() {
  const selectNode = useGraphStore((s) => s.selectNode)

  return (
    <Canvas
      camera={{ position: [0, 0, 150], fov: 60, near: 0.1, far: 1000 }}
      gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      dpr={[1, 1.5]}
      onPointerMissed={() => selectNode(null)}
      style={{ width: '100%', height: '100%' }}
    >
      <Suspense fallback={null}>
        <BackgroundEnvironment />
        <GraphScene />
        <PostProcessing />
        <CameraController />
        <CursorManager />
      </Suspense>
    </Canvas>
  )
}
