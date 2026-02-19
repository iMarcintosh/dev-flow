import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown, Check } from 'lucide-react'

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
  const [openUpward, setOpenUpward] = useState(false)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const [searchQuery, setSearchQuery] = useState('')

  const buttonRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Get currently selected model
  const selectedModel = Object.values(models)
    .flat()
    .find(m => m.id === value)

  // Filter models across all providers
  const filteredModels = Object.entries(models).reduce((acc, [provider, list]) => {
    const filtered = list.filter(m =>
      !searchQuery ||
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.description?.toLowerCase().includes(searchQuery.toLowerCase())
    )
    if (filtered.length > 0) acc[provider] = filtered
    return acc
  }, {} as Record<string, Model[]>)

  // Calculate dropdown position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom
      const spaceAbove = rect.top
      const dropdownHeight = 384 // max-h-96

      setDropdownPosition({ top: rect.bottom, left: rect.left, width: rect.width })
      setOpenUpward(spaceBelow < dropdownHeight && spaceAbove > spaceBelow)
    }
  }, [isOpen])

  // Reset search when closing
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('')
    }
  }, [isOpen])

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        !containerRef.current?.contains(event.target as Node) &&
        !dropdownRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

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

  const totalFiltered = Object.values(filteredModels).flat().length

  return (
    <div className="relative" ref={containerRef}>
      <label className="block text-sm font-medium text-gray-300 mb-2">
        {label}
      </label>

      {/* Selected Value Display */}
      <button
        ref={buttonRef}
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

      {/* Dropdown - rendered via Portal */}
      {isOpen && createPortal(
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-[998] backdrop-blur-[2px]"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown panel */}
          <div
            ref={dropdownRef}
            className="fixed z-[999] bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-96 overflow-y-auto"
            style={{
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              ...(openUpward
                ? { bottom: `${window.innerHeight - dropdownPosition.top + (buttonRef.current?.getBoundingClientRect().height ?? 0) + 8}px` }
                : { top: `${dropdownPosition.top + 8}px` }
              )
            }}
          >
            {/* Search input */}
            <div className="p-2 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full px-3 py-1.5 bg-gray-700 rounded-md text-sm text-white placeholder:text-gray-400 focus:outline-none"
                onClick={e => e.stopPropagation()}
              />
            </div>

            {totalFiltered === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-400">No models found.</div>
            ) : (
              Object.entries(filteredModels).map(([provider, modelList]) => (
                <div key={provider} className="border-b border-gray-700 last:border-0">
                  {/* Provider Header */}
                  <div className="px-4 py-2 bg-gray-900 text-xs font-semibold text-gray-400 uppercase tracking-wide sticky top-[46px] z-10">
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
                        {value === model.id ? (
                          <Check className="w-4 h-4 text-indigo-500" />
                        ) : (
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
              ))
            )}
          </div>
        </>,
        document.body
      )}
    </div>
  )
}
