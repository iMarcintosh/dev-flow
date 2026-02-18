import { useState } from 'react'
import { useStartAgent, useAgentRun, useApplyAgentResults } from '@/services/queries'
import { Loader2, Sparkles, X, Check } from 'lucide-react'

interface AgentInputModalProps {
  projectId: string
  onClose: () => void
}

export default function AgentInputModal({ projectId, onClose }: AgentInputModalProps) {
  const [text, setText] = useState('')
  const [runId, setRunId] = useState<string | null>(null)
  
  const startAgent = useStartAgent()
  const { data: agentRun } = useAgentRun(runId || undefined)
  const applyResults = useApplyAgentResults()

  const handleAnalyze = async () => {
    if (!text.trim()) return

    const result = await startAgent.mutateAsync({
      agentName: 'task_creator',
      projectId,
      text,
    })

    setRunId(result.run_id)
  }

  const handleApply = async () => {
    if (!runId) return
    
    await applyResults.mutateAsync(runId)
    onClose()
  }

  const preview = agentRun?.output?.preview || []
  const isRunning = agentRun?.status === 'pending' || agentRun?.status === 'running'
  const isDone = agentRun?.status === 'done'
  const isFailed = agentRun?.status === 'failed'

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">AI Task Creator</h2>
              <p className="text-sm text-muted-foreground">
                Describe what you want to build, and I'll create structured tasks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1 hover:bg-muted rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!runId ? (
            <>
              {/* Input */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Describe your task or feature
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={8}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground resize-none"
                  placeholder="Example: Fix the login bug where users can't authenticate with special characters in their password. We need to update the password validation logic and add proper escaping..."
                />
              </div>

              {/* Examples */}
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Try these examples:</p>
                <div className="grid gap-2">
                  {[
                    'BUG: Dashboard shows outdated metrics',
                    'Add dark mode support to the entire application',
                    'EPIC: Redesign the user profile page with avatar upload',
                  ].map((example) => (
                    <button
                      key={example}
                      onClick={() => setText(example)}
                      className="text-left px-3 py-2 bg-muted hover:bg-muted/70 rounded text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Status */}
              {isRunning && (
                <div className="flex items-center gap-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Analyzing your input...</p>
                    <p className="text-xs text-muted-foreground">
                      This usually takes a few seconds
                    </p>
                  </div>
                </div>
              )}

              {isFailed && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-sm font-medium text-red-500">Analysis failed</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {agentRun?.error_message || 'Something went wrong'}
                  </p>
                </div>
              )}

              {/* Preview */}
              {isDone && preview.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Check className="w-5 h-5 text-green-500" />
                    <h3 className="font-semibold text-foreground">
                      Created {preview.length} {preview.length === 1 ? 'item' : 'items'}
                    </h3>
                  </div>

                  <div className="space-y-3">
                    {preview.map((item: any, index: number) => (
                      <div
                        key={index}
                        className="border border-border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <h4 className="font-medium text-foreground">{item.title}</h4>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              item.type === 'bug'
                                ? 'bg-red-500/10 text-red-500'
                                : item.type === 'story'
                                ? 'bg-blue-500/10 text-blue-500'
                                : item.type === 'epic'
                                ? 'bg-purple-500/10 text-purple-500'
                                : 'bg-green-500/10 text-green-500'
                            }`}
                          >
                            {item.type}
                          </span>
                        </div>
                        {item.description && (
                          <p className="text-sm text-muted-foreground mb-2">{item.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>Priority: {item.priority}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <button
            onClick={onClose}
            className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            Cancel
          </button>

          {!runId ? (
            <button
              onClick={handleAnalyze}
              disabled={!text.trim() || startAgent.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {startAgent.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze with AI
                </>
              )}
            </button>
          ) : isDone ? (
            <button
              onClick={handleApply}
              disabled={applyResults.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              {applyResults.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Import to Board
                </>
              )}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
