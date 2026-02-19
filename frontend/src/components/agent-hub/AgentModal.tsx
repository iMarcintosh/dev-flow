import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { X, Loader2, AlertCircle } from 'lucide-react'
import { customAgentService } from '@/services/custom-agents'
import { toolsService } from '@/services/tools'
import type { CustomAgent, CustomAgentCreate } from '@/types/custom-agent'
import { DEFAULT_AGENT_ICON } from '@/types/custom-agent'
import { useAvailableModels } from '@/services/queries'
import ModelSelector from '@/components/settings/ModelSelector'
import KnowledgeBaseUpload from './KnowledgeBaseUpload'
import { useToast } from '@/hooks/useToast'
import { getErrorMessage, getValidationErrors } from '@/utils/errorHandler'
import { Select } from '@/components/ui/Select'
import { CronSelector } from './CronSelector'

interface AgentModalProps {
  agent?: CustomAgent | null
  onClose: () => void
  onSave: () => void
}

export function AgentModal({ agent, onClose, onSave }: AgentModalProps) {
  const isEdit = !!agent
  const [activeTab, setActiveTab] = useState<'config' | 'tools' | 'schedule' | 'knowledge'>('config')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const toast = useToast()

  const [formData, setFormData] = useState({
    name: agent?.name || '',
    description: agent?.description || '',
    icon: agent?.icon || DEFAULT_AGENT_ICON,
    visibility: agent?.visibility || ('private' as const),
    model_name: agent?.model_name || 'claude-3-haiku-20240307',
    system_prompt: agent?.system_prompt || 'You are a helpful AI assistant.',
    scheduled_prompt: agent?.scheduled_prompt || '',
    temperature: agent?.temperature ?? 0.7,
    max_tokens: agent?.max_tokens,
    top_p: agent?.top_p,
    enabled_tools: agent?.enabled_tools || ([] as string[]),
    trigger: agent?.trigger || 'manual',
    schedule: agent?.schedule || '',
    schedule_enabled: agent?.schedule_enabled ?? true,
  })

  // Fetch available models
  const { data: models, isLoading: modelsLoading } = useAvailableModels()

  // Fetch available tools from backend
  const { data: availableTools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['available-tools'],
    queryFn: toolsService.getAvailableTools,
  })

  const createMutation = useMutation({
    mutationFn: (data: CustomAgentCreate) => customAgentService.createAgent(data),
    onSuccess: () => {
      toast.success('Agent created successfully!')
      onSave()
    },
    onError: (error: any) => {
      const apiError = getErrorMessage(error)
      toast.error(apiError.message, apiError.detail)
      
      // Also set form validation errors if 422
      const validationErrors = getValidationErrors(error)
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors)
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<CustomAgentCreate>) =>
      customAgentService.updateAgent(agent!.id, data),
    onSuccess: () => {
      toast.success('Agent updated successfully!')
      onSave()
    },
    onError: (error: any) => {
      const apiError = getErrorMessage(error)
      toast.error(apiError.message, apiError.detail)
      
      // Also set form validation errors if 422
      const validationErrors = getValidationErrors(error)
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors)
      }
    },
  })

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!formData.system_prompt.trim()) {
      newErrors.system_prompt = 'System prompt is required (min 10 characters)'
    } else if (formData.system_prompt.trim().length < 10) {
      newErrors.system_prompt = 'System prompt must be at least 10 characters'
    }

    if (!formData.model_name) {
      newErrors.model_name = 'Please select a model'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Clear previous errors
    setErrors({})

    // Validate form
    if (!validateForm()) {
      // Show toast for validation errors
      toast.error('Please fix the errors in the form', 'Check the highlighted fields above')
      return
    }

    const data: CustomAgentCreate = {
      ...formData,
      system_prompt: formData.system_prompt.trim() || 'You are a helpful AI assistant.',
      max_tokens: formData.max_tokens || undefined,
      top_p: formData.top_p || undefined,
    }

    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const toggleTool = (toolId: string) => {
    setFormData((prev) => ({
      ...prev,
      enabled_tools: prev.enabled_tools.includes(toolId)
        ? prev.enabled_tools.filter((t) => t !== toolId)
        : [...prev.enabled_tools, toolId],
    }))
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg max-w-3xl w-full h-[85vh] flex flex-col">{/* Fixed height to prevent jumping */}
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold text-foreground">
            {isEdit ? 'Edit Agent' : 'Create New Agent'}
          </h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <div className="flex gap-1 px-6">
            <button
              type="button"
              onClick={() => setActiveTab('config')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'config'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              ⚙️ Configuration
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('tools')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'tools'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              🔧 Tools
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('schedule')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'schedule'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              🕐 Schedule
            </button>
            {isEdit && (
              <button
                type="button"
                onClick={() => setActiveTab('knowledge')}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'knowledge'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                📚 Knowledge Base
              </button>
            )}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === 'config' ? (
            <>
          {/* Error Summary */}
          {Object.keys(errors).length > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-red-800 dark:text-red-300">
                    Please fix the following errors:
                  </h3>
                  <ul className="mt-2 text-sm text-red-700 dark:text-red-400 list-disc list-inside space-y-1">
                    {Object.entries(errors).map(([field, message]) => (
                      <li key={field}>{message}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value })
                  if (errors.name) setErrors({ ...errors, name: '' })
                }}
                required
                className={`w-full px-3 py-2 bg-background border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 ${
                  errors.name ? 'border-red-500' : 'border-border'
                }`}
                placeholder="e.g., Code Review Agent"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.name}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Icon</label>
              <input
                type="text"
                value={formData.icon}
                onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                placeholder="🤖"
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              placeholder="What does this agent do?"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Model Selection */}
          <div>
            <ModelSelector
              value={formData.model_name}
              onChange={(modelId) => {
                setFormData({ ...formData, model_name: modelId })
                if (errors.model_name) setErrors({ ...errors, model_name: '' })
              }}
            models={models || {}}
            label="Model *"
            disabled={modelsLoading}
          />
          {errors.model_name && (
            <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              {errors.model_name}
            </p>
          )}
          </div>

          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              System Prompt <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) => {
                setFormData({ ...formData, system_prompt: e.target.value })
                if (errors.system_prompt) setErrors({ ...errors, system_prompt: '' })
              }}
              required
              rows={6}
              placeholder="You are a helpful assistant that..."
              className={`w-full px-3 py-2 bg-background border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm ${
                errors.system_prompt ? 'border-red-500' : 'border-border'
              }`}
            />
            {errors.system_prompt && (
              <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.system_prompt}
              </p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              Minimum 10 characters. This defines the agent's behavior and personality.
            </p>
          </div>

          {/* Parameters */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Temperature: {formData.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature}
                onChange={(e) =>
                  setFormData({ ...formData, temperature: parseFloat(e.target.value) })
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Max Tokens</label>
              <input
                type="number"
                value={formData.max_tokens || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_tokens: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                placeholder="Auto"
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Top P</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.top_p || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    top_p: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="Auto"
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          {/* Visibility */}
          <Select
            label="Visibility"
            value={formData.visibility}
            onChange={(val) =>
              setFormData({
                ...formData,
                visibility: val as 'private' | 'team' | 'public',
              })
            }
            options={[
              { value: 'private', label: 'Private', description: 'Only you' },
              { value: 'team', label: 'Team', description: 'Team members' },
              { value: 'public', label: 'Public', description: 'Everyone in marketplace' },
            ]}
          />
            </>
          ) : activeTab === 'tools' ? (
            <>
          {/* Tools Tab */}
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Enabled Tools</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Select which tools this agent can use when processing requests.
            </p>
            {toolsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {availableTools.map((tool) => (
                  <label
                    key={tool.id}
                    className="flex items-start gap-3 p-3 bg-background border border-border rounded-lg cursor-pointer hover:border-primary/50 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={formData.enabled_tools.includes(tool.id)}
                      onChange={() => toggleTool(tool.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-foreground text-sm">{tool.name}</div>
                      <div className="text-xs text-muted-foreground">{tool.description}</div>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                          {tool.category}
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
            {formData.enabled_tools.length > 0 && (
              <div className="mt-4 p-3 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-sm text-foreground">
                  <span className="font-medium">{formData.enabled_tools.length}</span> tool(s) enabled
                </p>
              </div>
            )}
          </div>
            </>
          ) : activeTab === 'schedule' ? (
            <>
          {/* Schedule Tab */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Trigger Type</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Choose how this agent should be triggered.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, trigger: 'manual' })}
                  className={`px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                    formData.trigger === 'manual'
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background border-border text-foreground hover:bg-accent'
                  }`}
                >
                  Manual
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ 
                    ...formData, 
                    trigger: 'scheduled',
                    schedule: formData.schedule || '0 * * * *' // Default to "Every Hour"
                  })}
                  className={`px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                    formData.trigger === 'scheduled'
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background border-border text-foreground hover:bg-accent'
                  }`}
                >
                  Scheduled
                </button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {formData.trigger === 'manual' && '✓ Triggered manually or via API'}
                {formData.trigger === 'scheduled' && '✓ Runs automatically on a schedule'}
              </p>
            </div>

            {/* Schedule Configuration */}
            {formData.trigger === 'scheduled' && (
              <div className="space-y-4">
                <div className="border-t border-border pt-4">
                  <h4 className="text-sm font-semibold text-foreground mb-3">Schedule Configuration</h4>
                  <CronSelector
                    value={formData.schedule}
                    onChange={(cron) => setFormData({ ...formData, schedule: cron })}
                  />
                </div>

                {/* Scheduled Prompt Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Scheduled Prompt
                    <span className="text-muted-foreground ml-2">(What should the agent do?)</span>
                  </label>
                  <textarea
                    value={formData.scheduled_prompt}
                    onChange={(e) => setFormData({ ...formData, scheduled_prompt: e.target.value })}
                    rows={3}
                    placeholder='z.B. "Wie ist das aktuelle Wetter in Gelnhausen?"'
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    💡 This prompt will be used every time the agent runs on schedule. Leave empty to use a generic prompt.
                  </p>
                </div>

                {agent?.next_scheduled_run && (
                  <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                    <p className="text-sm text-foreground">
                      <span className="font-medium">Next Run:</span>{' '}
                      {new Date(agent.next_scheduled_run).toLocaleString()}
                    </p>
                    {agent.last_scheduled_run && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Last Run: {new Date(agent.last_scheduled_run).toLocaleString()}
                      </p>
                    )}
                  </div>
                )}

                <div className="text-xs text-muted-foreground space-y-1 p-3 bg-muted/50 rounded-lg">
                  <p>ℹ️ All schedules are in UTC timezone</p>
                  <p>ℹ️ Next run time is calculated automatically after saving</p>
                </div>
              </div>
            )}
          </div>
            </>
          ) : activeTab === 'knowledge' ? (
            /* Knowledge Base Tab */
            <KnowledgeBaseUpload agentId={agent?.id || ''} />
          ) : null}
        </form>

        {/* Footer */}
        {activeTab !== 'knowledge' && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-foreground hover:bg-accent rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEdit ? 'Save Changes' : 'Create Agent'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
