import { create } from 'zustand'
import type { SemanticZoomLevel } from '@/types/graph'
import { getSemanticZoomLevel } from '@/utils/graphLayout'

interface UIState {
  sidebarOpen: boolean
  detailPanelOpen: boolean
  cameraDistance: number
  zoomLevel: SemanticZoomLevel
  showLabels: boolean
  showEdges: boolean
  bloomIntensity: number
  showUploadPanel: boolean
  showChatPanel: boolean

  toggleSidebar: () => void
  toggleDetailPanel: () => void
  setDetailPanelOpen: (open: boolean) => void
  setCameraDistance: (d: number) => void
  toggleUploadPanel: () => void
  toggleChatPanel: () => void
  setUploadPanelOpen: (open: boolean) => void
  setChatPanelOpen: (open: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  detailPanelOpen: false,
  cameraDistance: 150,
  zoomLevel: 'medium',
  showLabels: true,
  showEdges: true,
  bloomIntensity: 0.8,
  showUploadPanel: false,
  showChatPanel: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleDetailPanel: () => set((s) => ({ detailPanelOpen: !s.detailPanelOpen })),
  setDetailPanelOpen: (open) => set({ detailPanelOpen: open }),
  setCameraDistance: (d) =>
    set({ cameraDistance: d, zoomLevel: getSemanticZoomLevel(d) }),
  toggleUploadPanel: () => set((s) => ({ showUploadPanel: !s.showUploadPanel })),
  toggleChatPanel: () => set((s) => ({ showChatPanel: !s.showChatPanel })),
  setUploadPanelOpen: (open) => set({ showUploadPanel: open }),
  setChatPanelOpen: (open) => set({ showChatPanel: open }),
}))
