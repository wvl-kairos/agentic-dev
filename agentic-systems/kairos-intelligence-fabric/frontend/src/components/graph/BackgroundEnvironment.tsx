import { Stars } from '@react-three/drei'

export function BackgroundEnvironment() {
  return (
    <>
      <color attach="background" args={['#0a0a1a']} />
      <Stars
        radius={300}
        depth={60}
        count={1000}
        factor={4}
        saturation={0}
        fade
        speed={0.5}
      />
      <ambientLight intensity={0.15} />
      <pointLight position={[100, 100, 100]} intensity={0.3} color="#6366f1" />
      <pointLight position={[-100, -100, -50]} intensity={0.2} color="#06b6d4" />
    </>
  )
}
