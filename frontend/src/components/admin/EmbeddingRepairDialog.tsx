import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { RefreshCw, AlertCircle, CheckCircle, Info, X } from 'lucide-react'
import { api } from '@/services/api'

interface EmbeddingHealth {
  total_items: number
  items_with_embedding: number
  items_missing_embedding: number
  health_percentage: number
  status: 'healthy' | 'needs_repair'
  missing_items: Array<{
    id: string
    title: string
    project_id: string
  }>
}

interface RepairResult {
  success: boolean
  message: string
  items_queued?: number
  projects_queued?: number
}

export function EmbeddingRepairDialog() {
  const [isOpen, setIsOpen] = useState(false)

  const { data: health, isLoading: healthLoading, refetch } = useQuery<EmbeddingHealth>({
    queryKey: ['embedding-health'],
    queryFn: async () => {
      const response = await api.get('/api/admin/embedding-health')
      return response.data
    },
    enabled: isOpen,
  })

  const repairMutation = useMutation<RepairResult, Error>({
    mutationFn: async () => {
      const response = await api.post('/api/admin/repair-embeddings')
      return response.data
    },
    onSuccess: () => {
      setTimeout(() => refetch(), 2000)
    },
  })

  const handleRepair = () => {
    repairMutation.mutate()
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
      >
        <RefreshCw className="w-5 h-5" />
        Embedding Health
      </button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Embedding Health & Repair</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Check and repair item embeddings for better AI performance
            </p>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4 overflow-y-auto">
          {healthLoading && (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {health && (
            <>
              {/* Status Card */}
              <div className="p-4 border rounded-lg bg-card">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-lg">System Health</h3>
                    <p className="text-sm text-muted-foreground">
                      {health.total_items} total items
                    </p>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      health.status === 'healthy'
                        ? 'bg-green-500/10 text-green-500 border border-green-500/20'
                        : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                    }`}
                  >
                    {health.status === 'healthy' ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" />
                        Healthy
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Needs Repair
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Coverage</span>
                    <span className="font-medium">{health.health_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        health.health_percentage === 100 ? 'bg-green-500' : 'bg-yellow-500'
                      }`}
                      style={{ width: `${health.health_percentage}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{health.items_with_embedding} with embeddings</span>
                    <span>{health.items_missing_embedding} missing</span>
                  </div>
                </div>
              </div>

              {/* Missing Items List */}
              {health.items_missing_embedding > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Missing Embeddings</h4>
                  <div className="max-h-[200px] overflow-y-auto space-y-1 border rounded-lg p-2">
                    {health.missing_items.map((item) => (
                      <div
                        key={item.id}
                        className="text-sm p-2 bg-muted/50 rounded flex items-center gap-2"
                      >
                        <AlertCircle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                        <span className="truncate flex-1">{item.title}</span>
                      </div>
                    ))}
                    {health.items_missing_embedding > health.missing_items.length && (
                      <div className="text-xs text-muted-foreground text-center p-2">
                        +{health.items_missing_embedding - health.missing_items.length} more
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Info Alert */}
              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg flex gap-2">
                <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-500">
                  Embeddings enable semantic search in chat. Items without embeddings won't appear in AI search.
                </p>
              </div>

              {/* Success Message */}
              {repairMutation.isSuccess && repairMutation.data && (
                <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg flex gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-green-500">
                    <p>{repairMutation.data.message}</p>
                    {repairMutation.data.items_queued !== undefined && (
                      <p className="font-medium mt-1">
                        {repairMutation.data.items_queued} items queued for re-indexing
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Error Message */}
              {repairMutation.isError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-500">Error: {repairMutation.error.message}</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        {health && (
          <div className="px-6 py-4 border-t border-border flex gap-2">
            <button
              onClick={handleRepair}
              disabled={health.items_missing_embedding === 0 || repairMutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {repairMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Repairing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Repair Embeddings
                </>
              )}
            </button>
            <button
              onClick={() => refetch()}
              disabled={healthLoading}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${healthLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

