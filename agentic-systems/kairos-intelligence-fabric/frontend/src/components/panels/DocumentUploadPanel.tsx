import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, FileText, Loader2, CheckCircle, AlertCircle, Zap, Info } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useChatStore } from '@/stores/chatStore'
import { useDocuments } from '@/hooks/useDocuments'
import { useGraphStore } from '@/stores/graphStore'

export function DocumentUploadPanel() {
  const showPanel = useUIStore((s) => s.showUploadPanel)
  const setOpen = useUIStore((s) => s.setUploadPanelOpen)
  const { documents, upload, ingest, loading } = useDocuments()
  const fetchGraph = useGraphStore((s) => s.fetchGraph)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [ingesting, setIngesting] = useState<string | null>(null)

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const files = Array.from(e.dataTransfer.files)
      if (files.length === 0) return
      setUploading(true)
      try {
        for (const file of files) {
          await upload(file)
        }
      } finally {
        setUploading(false)
      }
    },
    [upload],
  )

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (files.length === 0) return
      setUploading(true)
      try {
        for (const file of files) {
          await upload(file)
        }
      } finally {
        setUploading(false)
      }
    },
    [upload],
  )

  const handleIngest = useCallback(
    async (docId: string) => {
      setIngesting(docId)
      try {
        const status = await ingest(docId)
        await fetchGraph()

        // Push ingestion summary to chat
        if (status?.result) {
          const r = status.result
          const doc = documents.find((d) => d.id === docId)
          const title = doc?.title || docId
          const lines = [
            `**Document Ingested: ${title}**`,
            `Entities extracted: **${r.entities_extracted}** | Resolved: **${r.entities_resolved}**`,
            `New nodes: **${r.nodes_created}** | New edges: **${r.edges_created}**`,
          ]
          if (r.graph_total_nodes) {
            lines.push(`Graph total: **${r.graph_total_nodes}** nodes, **${r.graph_total_edges}** edges`)
          }
          if (r.error_message) {
            lines.push(`Error: ${r.error_message}`)
          }
          useChatStore.getState().addMessage({
            id: '',
            role: 'assistant',
            content: lines.join('\n'),
            timestamp: Date.now(),
          })
          useUIStore.getState().setChatPanelOpen(true)
        }
      } finally {
        setIngesting(null)
      }
    },
    [ingest, fetchGraph, documents],
  )

  const statusIcon = (status: string) => {
    switch (status) {
      case 'ingested':
        return <CheckCircle size={16} className="text-green-400" />
      case 'ingesting':
        return <Loader2 size={16} className="text-yellow-400 animate-spin" />
      case 'error':
        return <AlertCircle size={16} className="text-red-400" />
      default:
        return <FileText size={16} className="text-white/40" />
    }
  }

  const statusLabel = (status: string) => {
    switch (status) {
      case 'ingested':
        return 'Ingested — knowledge extracted'
      case 'ingesting':
        return 'Extracting knowledge...'
      case 'error':
        return 'Ingestion failed'
      default:
        return 'Pending — click ⚡ to ingest'
    }
  }

  return (
    <AnimatePresence>
      {showPanel && (
        <motion.div
          initial={{ x: -400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed top-16 left-4 bottom-4 z-30 w-80 overflow-hidden flex flex-col"
          style={{
            background: 'rgba(18, 18, 42, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '12px',
          }}
        >
          {/* Header */}
          <div
            className="px-4 py-3 flex items-center justify-between flex-shrink-0"
            style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}
          >
            <span className="text-base font-semibold text-white/80">Documents</span>
            <button
              onClick={() => setOpen(false)}
              className="p-1 rounded-md hover:bg-white/10 transition-colors"
            >
              <X size={16} className="text-white/40" />
            </button>
          </div>

          {/* Info banner */}
          <div
            className="mx-4 mt-3 px-3 py-2 rounded-lg flex items-start gap-2"
            style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.15)' }}
          >
            <Info size={14} className="text-indigo-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-indigo-300/70 leading-relaxed">
              Upload documents, then click <strong>⚡</strong> to extract knowledge into the graph. Ingested docs link to existing nodes automatically.
            </p>
          </div>

          {/* Drop zone */}
          <div
            className="mx-4 mt-3 p-5 rounded-lg border-2 border-dashed text-center cursor-pointer transition-colors"
            style={{
              borderColor: dragOver ? 'rgba(236, 72, 153, 0.5)' : 'rgba(255, 255, 255, 0.1)',
              background: dragOver ? 'rgba(236, 72, 153, 0.05)' : 'transparent',
            }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            {uploading ? (
              <Loader2 size={24} className="mx-auto text-pink-400 animate-spin" />
            ) : (
              <Upload size={24} className="mx-auto text-white/30" />
            )}
            <p className="text-sm text-white/40 mt-2">
              {uploading ? 'Uploading...' : 'Drop files or click to upload'}
            </p>
            <p className="text-xs text-white/20 mt-1">.txt, .pdf, .md, .csv, .sql, .json</p>
            <input
              id="file-input"
              type="file"
              multiple
              className="hidden"
              onChange={handleFileSelect}
              accept=".txt,.pdf,.md,.csv,.sql,.json,text/plain,application/json,application/sql"
            />
          </div>

          {/* Document list */}
          <div className="flex-1 overflow-y-auto px-4 pt-3 pb-4 space-y-2">
            {loading && documents.length === 0 && (
              <p className="text-sm text-white/30 text-center py-4">Loading...</p>
            )}
            {documents.length === 0 && !loading && (
              <p className="text-sm text-white/20 text-center py-4">No documents yet</p>
            )}
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 py-2.5 px-3 rounded-lg"
                style={{ background: 'rgba(255, 255, 255, 0.03)' }}
              >
                {statusIcon(doc.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/70 truncate">{doc.title}</p>
                  <p className="text-xs text-white/30">
                    {(doc.size_bytes / 1024).toFixed(1)} KB · {statusLabel(doc.status)}
                  </p>
                </div>
                {doc.status === 'uploaded' && (
                  <button
                    onClick={() => handleIngest(doc.id)}
                    disabled={ingesting === doc.id}
                    className="p-1.5 rounded-md hover:bg-white/10 transition-colors"
                    title="Extract knowledge from this document"
                  >
                    {ingesting === doc.id ? (
                      <Loader2 size={16} className="text-yellow-400 animate-spin" />
                    ) : (
                      <Zap size={16} className="text-pink-400" />
                    )}
                  </button>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
