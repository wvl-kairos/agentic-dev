import { useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useUIStore } from '@/stores/uiStore'

export function CameraController() {
  const controlsRef = useRef(null)
  const setCameraDistance = useUIStore((s) => s.setCameraDistance)
  const { camera } = useThree()
  const lastDistanceRef = useRef(0)
  const frameCountRef = useRef(0)

  useFrame(() => {
    // Throttle store updates to every 5th frame
    frameCountRef.current++
    if (frameCountRef.current % 5 !== 0) return

    const distance = camera.position.length()
    // Only update if distance changed meaningfully
    if (Math.abs(distance - lastDistanceRef.current) > 1) {
      lastDistanceRef.current = distance
      setCameraDistance(distance)
    }
  })

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.05}
      minDistance={20}
      maxDistance={400}
      rotateSpeed={0.5}
      zoomSpeed={0.8}
      panSpeed={0.5}
    />
  )
}
