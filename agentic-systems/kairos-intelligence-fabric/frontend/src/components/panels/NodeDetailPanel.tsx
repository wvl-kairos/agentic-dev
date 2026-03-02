import { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, FileText, Lightbulb } from 'lucide-react'
import { useGraphStore } from '@/stores/graphStore'
import { NODE_COLORS } from '@/utils/colors'
import type { NodeType } from '@/types/graph'

const TYPE_LABELS: Record<NodeType, string> = {
  equipment: 'Equipment',
  orders: 'Order',
  products: 'Product',
  quality: 'Quality',
  people: 'Person',
  suppliers: 'Supplier',
  production_lines: 'Production Line',
  document: 'Document',
  knowledge: 'Knowledge',
}

function formatPropertyValue(value: unknown): string {
  if (value == null) return '-'
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'number') {
    if (value > 0 && value < 1) return `${(value * 100).toFixed(0)}%`
    return value.toLocaleString()
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function NodeDetailPanel() {
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const nodes = useGraphStore((s) => s.nodes)
  const edges = useGraphStore((s) => s.edges)
  const selectNode = useGraphStore((s) => s.selectNode)

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId),
    [nodes, selectedNodeId],
  )

  const connectedNodes = useMemo(() => {
    if (!selectedNodeId) return []
    const connected = edges.filter(
      (e) => e.source === selectedNodeId || e.target === selectedNodeId,
    )
    return connected.map((e) => {
      const otherId = e.source === selectedNodeId ? e.target : e.source
      const otherNode = nodes.find((n) => n.id === otherId)
      return { edge: e, node: otherNode }
    })
  }, [edges, nodes, selectedNodeId])

  const isVisible = !!selectedNode

  const typeIcon = selectedNode?.type === 'document' ? (
    <FileText size={14} className="text-pink-400" />
  ) : selectedNode?.type === 'knowledge' ? (
    <Lightbulb size={14} className="text-teal-400" />
  ) : null

  return (
    <AnimatePresence>
      {isVisible && selectedNode && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed top-16 right-4 bottom-4 z-30 w-80 overflow-hidden"
          role="complementary"
          aria-label={`Details for ${selectedNode.label}`}
          style={{
            background: 'rgba(18, 18, 42, 0.9)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '12px',
          }}
        >
          {/* Header */}
          <div
            className="px-4 py-3 flex items-center justify-between"
            style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  background: NODE_COLORS[selectedNode.type],
                  boxShadow: `0 0 8px ${NODE_COLORS[selectedNode.type]}80`,
                }}
              />
              {typeIcon}
              <span className="text-sm font-mono text-white/50 uppercase">
                {TYPE_LABELS[selectedNode.type] || selectedNode.type}
              </span>
            </div>
            <button
              onClick={() => selectNode(null)}
              className="p-1 rounded-md hover:bg-white/10 transition-colors"
              aria-label="Close detail panel"
            >
              <X size={16} className="text-white/40" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(100% - 52px)' }}>
            {/* Node name */}
            <h3 className="text-lg font-semibold text-white mb-4">
              {selectedNode.label}
            </h3>

            {/* Document/Knowledge specific info */}
            {selectedNode.type === 'document' && !!selectedNode.properties.content_preview && (
              <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(236, 72, 153, 0.05)', border: '1px solid rgba(236, 72, 153, 0.1)' }}>
                <p className="text-xs text-pink-400/60 uppercase font-semibold mb-1">Preview</p>
                <p className="text-sm text-white/50 leading-relaxed">
                  {String(selectedNode.properties.content_preview)}
                </p>
              </div>
            )}

            {selectedNode.type === 'knowledge' && !!selectedNode.properties.content && (
              <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(20, 184, 166, 0.05)', border: '1px solid rgba(20, 184, 166, 0.1)' }}>
                <p className="text-xs text-teal-400/60 uppercase font-semibold mb-1">Insight</p>
                <p className="text-sm text-white/60 leading-relaxed">
                  {String(selectedNode.properties.content)}
                </p>
                {!!selectedNode.properties.agent && (
                  <p className="text-xs text-white/25 mt-2">
                    Generated by: {String(selectedNode.properties.agent)}
                  </p>
                )}
              </div>
            )}

            {/* Properties */}
            <div className="mb-6">
              <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
                Properties
              </h4>
              <div className="space-y-2">
                {Object.entries(selectedNode.properties)
                  .filter(([key]) => !['content_preview', 'content', 'agent'].includes(key))
                  .map(([key, value]) => (
                    <div
                      key={key}
                      className="flex justify-between items-start py-1.5 px-2 rounded-md"
                      style={{ background: 'rgba(255, 255, 255, 0.03)' }}
                    >
                      <span className="text-sm text-white/50">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="text-sm font-mono text-white/80 text-right ml-2">
                        {formatPropertyValue(value)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Connected nodes */}
            {connectedNodes.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
                  Connections ({connectedNodes.length})
                </h4>
                <div className="space-y-1" role="list">
                  {connectedNodes.map(({ edge, node }) =>
                    node ? (
                      <button
                        key={`${edge.source}:${edge.target}:${edge.type}`}
                        onClick={() => selectNode(node.id)}
                        className="w-full flex items-center gap-2 py-2 px-2 rounded-md text-left hover:bg-white/5 transition-colors"
                        role="listitem"
                        aria-label={`Navigate to ${node.label} (${edge.type})`}
                      >
                        <div
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ background: NODE_COLORS[node.type] }}
                        />
                        <span className="text-sm text-white/70 truncate flex-1">
                          {node.label}
                        </span>
                        <span
                          className="text-xs font-mono px-1.5 py-0.5 rounded"
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'rgba(255, 255, 255, 0.35)',
                          }}
                        >
                          {edge.type}
                        </span>
                      </button>
                    ) : null,
                  )}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
