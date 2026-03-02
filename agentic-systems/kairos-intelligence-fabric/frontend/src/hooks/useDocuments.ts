import { useState, useEffect, useCallback } from 'react'
import type { Document, IngestionStatus } from '@/types/document'
import { fetchDocuments, uploadDocument, triggerIngestion, getIngestionStatus } from '@/utils/api'

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true)
      const data = await fetchDocuments()
      setDocuments(data.documents)
    } catch (err) {
      console.error('Failed to load documents:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const upload = useCallback(
    async (file: File) => {
      const result = await uploadDocument(file)
      await loadDocuments()
      return result
    },
    [loadDocuments],
  )

  const ingest = useCallback(
    async (docId: string): Promise<IngestionStatus | null> => {
      await triggerIngestion(docId)

      // Poll for completion
      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 2000))
        const status = await getIngestionStatus(docId)
        if (status.status === 'completed' || status.status === 'error') {
          await loadDocuments()
          return status
        }
      }
      return null
    },
    [loadDocuments],
  )

  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  // Re-fetch documents when graph is reset
  useEffect(() => {
    const handler = () => { loadDocuments() }
    window.addEventListener('kairos:graph-reset', handler)
    return () => window.removeEventListener('kairos:graph-reset', handler)
  }, [loadDocuments])

  return { documents, loading, upload, ingest, reload: loadDocuments }
}
