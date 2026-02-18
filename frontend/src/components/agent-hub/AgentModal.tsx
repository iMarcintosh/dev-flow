import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, Loader2 } from 'lucide-react'
import { customAgentService } from '@/services/custom-agents'
import type { CustomAgent, CustomAgentCreate } from '@/types/custom-agent'
import { AVAILABLE_TOOLS, DEFAULT_AGENT_ICON } from '@/types/custom-agent'
import { useAvailableModels } from '@/services/queries'
import ModelSelector from '@/components/settings/ModelSelector'
import KnowledgeBaseUpload from './KnowledgeBaseUpload'

interface AgentModalProps {
  agent?: CustomAgent | null
  onClose: () => void
  onSave: () => void
}

export function AgentModal({ agent, onClose, onSave }: AgentModalProps) {
  const isEdit = !!agent
  const [activeTab, setActiveTab] = useState<'config' | 'knowledge'>('config')

  const [formData, setFormData] = useState({
    name: agent?.name || '',
    description: agent?.description || '',
    icon: agent?.icon || DEFAULT_AGENT_ICON,
    visibility: agent?.visibility || ('private' as const),
    model_name: agent?.model_name || 'claude-3-haiku-20240307',
    system_prompt: agent?.system_prompt || 'You are a helpful AI assistant.',
    temperature: agent?.temperature ?? 0.7,
    max_tokens: agent?.max_tokens,
    top_p: agent?.top_p,
    enabled_tools: agent?.enabled_tools || ([] as string[]),
  })

  // Fetch available models
  const { data: models, isLoading: modelsLoading } = useAvailableModels()

  const createMutation = useMutation({
    mutationFn: (data: CustomAgentCreate) => customAgentService.createAgent(data),
    onSuccess: () => {
      onSave()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<CustomAgentCreate>) =>
      customAgentService.updateAgent(agent!.id, data),
    onSuccess: () => {
      onSave()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
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
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
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
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Model Selection */}
          <ModelSelector
            value={formData.model_name}
            onChange={(modelId) => setFormData({ ...formData, model_name: modelId })}
            models={models || {}}
            label="Model"
            disabled={modelsLoading}
          />

          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              System Prompt
            </label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              required
              rows={6}
              placeholder="You are a helpful assistant that..."
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
            />
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

          {/* Tools */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">
              Enabled Tools
            </label>
            <div className="grid grid-cols-2 gap-3">
              {AVAILABLE_TOOLS.map((tool) => (
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
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Visibility */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Visibility</label>
            <select
              value={formData.visibility}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  visibility: e.target.value as 'private' | 'team' | 'public',
                })
              }
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="private">Private (Only you)</option>
              <option value="team">Team (Team members)</option>
              <option value="public">Public (Marketplace)</option>
            </select>
          </div>
            </>
          ) : (
            /* Knowledge Base Tab */
            <KnowledgeBaseUpload agentId={agent?.id || ''} />
          )}
        </form>

        {/* Footer */}
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
      </div>
    </div>
  )
}
