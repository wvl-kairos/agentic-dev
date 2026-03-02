import { useMemo } from 'react'
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing'
import { BlendFunction } from 'postprocessing'
import { Vector2 } from 'three'

const CHROMATIC_OFFSET = new Vector2(0.0005, 0.0005)

function detectLowPowerGPU(): boolean {
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    if (!gl) return false
    const ext = gl.getExtension('WEBGL_debug_renderer_info')
    if (!ext) return false
    const renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)
    return /Intel|Mali|Adreno/i.test(renderer)
  } catch {
    return false
  }
}

export function PostProcessing() {
  const isLowPower = useMemo(() => detectLowPowerGPU(), [])

  if (isLowPower) {
    return (
      <EffectComposer>
        <Bloom
          luminanceThreshold={0.5}
          luminanceSmoothing={0.9}
          intensity={0.6}
          mipmapBlur
          levels={4}
        />
      </EffectComposer>
    )
  }

  return (
    <EffectComposer>
      <Bloom
        luminanceThreshold={0.5}
        luminanceSmoothing={0.9}
        intensity={0.6}
        mipmapBlur
        levels={4}
      />
      <ChromaticAberration
        blendFunction={BlendFunction.NORMAL}
        offset={CHROMATIC_OFFSET}
        radialModulation={false}
        modulationOffset={0}
      />
    </EffectComposer>
  )
}
