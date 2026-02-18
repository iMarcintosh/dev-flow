import { useState } from 'react'
import { ChevronDown, Check, Loader2 } from 'lucide-react'

interface Model {
  id: string
  name: string
  description: string
  provider: string
  context_window: number
  cost_tier: string
  pricing?: {
    prompt?: string
    completion?: string
  }
}

interface ModelSelectorProps {
  value: string
  onChange: (modelId: string) => void
  models: Record<string, Model[]>
  label: string
  disabled?: boolean
}

export default function ModelSelector({ 
  value, 
  onChange, 
  models, 
  label,
  disabled = false 
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Get currently selected model
  const selectedModel = Object.values(models)
    .flat()
    .find(m => m.id === value)

  // Count models per provider
  const providerCounts = Object.entries(models).reduce((acc, [provider, modelList]) => {
    if (modelList.length > 0) {
      acc[provider] = modelList.length
    }
    return acc
  }, {} as Record<string, number>)

  const getCostColor = (tier: string) => {
    switch (tier) {
      case 'low': return 'text-green-500'
      case 'medium': return 'text-yellow-500'
      case 'high': return 'text-orange-500'
      case 'highest': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getCostLabel = (tier: string) => {
    switch (tier) {
      case 'low': return '💰'
      case 'medium': return '💰💰'
      case 'high': return '💰💰💰'
      case 'highest': return '💰💰💰💰'
      default: return ''
    }
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        {label}
      </label>
      
      {/* Selected Value Display */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-left flex items-center justify-between hover:border-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="flex-1">
          {selectedModel ? (
            <div>
              <div className="text-white font-medium">{selectedModel.name}</div>
              <div className="text-xs text-gray-400 mt-1">
                {selectedModel.provider} • {getCostLabel(selectedModel.cost_tier)} {selectedModel.cost_tier}
              </div>
            </div>
          ) : (
            <div className="text-gray-400">Select a model...</div>
          )}
        </div>
        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-96 overflow-y-auto">
            {Object.entries(models).map(([provider, modelList]) => {
              if (modelList.length === 0) return null
              
              return (
                <div key={provider} className="border-b border-gray-700 last:border-0">
                  {/* Provider Header */}
                  <div className="px-4 py-2 bg-gray-900 text-xs font-semibold text-gray-400 uppercase tracking-wide sticky top-0 z-10">
                    {provider === 'anthropic' && '📦 Anthropic (Direct)'}
                    {provider === 'openai' && '📦 OpenAI (Direct)'}
                    {provider === 'openrouter' && '🌐 OpenRouter (Unified)'}
                    <span className="ml-2 text-gray-500">({modelList.length})</span>
                  </div>

                  {/* Models */}
                  {modelList.map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => {
                        onChange(model.id)
                        setIsOpen(false)
                      }}
                      className="w-full px-4 py-3 hover:bg-gray-700 transition-colors text-left flex items-start gap-3"
                    >
                      <div className="flex-shrink-0 mt-1">
                        {value === model.id && (
                          <Check className="w-4 h-4 text-indigo-500" />
                        )}
                        {value !== model.id && (
                          <div className="w-4 h-4" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-medium">{model.name}</div>
                        {model.description && (
                          <div className="text-xs text-gray-400 mt-1">{model.description}</div>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs">
                          <span className={getCostColor(model.cost_tier)}>
                            {getCostLabel(model.cost_tier)} {model.cost_tier}
                          </span>
                          {model.context_window > 0 && (
                            <span className="text-gray-500">
                              {(model.context_window / 1000).toFixed(0)}k context
                            </span>
                          )}
                          {model.pricing?.prompt && (
                            <span className="text-gray-500">
                              ${(parseFloat(model.pricing.prompt) * 1000000).toFixed(2)}/1M tokens
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
