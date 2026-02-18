import { useState } from 'react'
import { Eye, EyeOff, Key, Check, X, Loader2 } from 'lucide-react'
import { useApiKeyStatus, useTestApiKey, useUpdateApiKey, useDeleteApiKey } from '@/services/queries'

type Provider = 'anthropic' | 'openai' | 'openrouter'

interface ProviderConfig {
  name: string
  displayName: string
  placeholder: string
  icon: string
}

const PROVIDERS: Record<Provider, ProviderConfig> = {
  anthropic: {
    name: 'anthropic',
    displayName: 'Anthropic (Claude)',
    placeholder: 'sk-ant-api03_...',
    icon: '🔮'
  },
  openai: {
    name: 'openai',
    displayName: 'OpenAI (GPT)',
    placeholder: 'sk-...',
    icon: '🤖'
  },
  openrouter: {
    name: 'openrouter',
    displayName: 'OpenRouter',
    placeholder: 'sk-or-...',
    icon: '🔀'
  }
}

interface ApiKeyInputProps {
  provider: Provider
  status: 'personal' | 'global' | 'none'
  maskedKey: string | null
}

function ApiKeyInput({ provider, status, maskedKey }: ApiKeyInputProps) {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [testResult, setTestResult] = useState<{ valid: boolean; error: string | null } | null>(null)

  const testMutation = useTestApiKey()
  const updateMutation = useUpdateApiKey()
  const deleteMutation = useDeleteApiKey()

  const config = PROVIDERS[provider]

  const handleTest = async () => {
    if (!apiKey.trim()) return
    
    setTestResult(null)
    const result = await testMutation.mutateAsync({
      provider,
      api_key: apiKey
    })
    setTestResult(result)
  }

  const handleSave = async () => {
    if (!apiKey.trim()) return
    
    try {
      await updateMutation.mutateAsync({
        provider,
        api_key: apiKey
      })
      setApiKey('')
      setTestResult(null)
    } catch (error) {
      console.error('Failed to save API key:', error)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Remove your personal ${config.displayName} API key?\n\nYou will fall back to the global key if available.`)) {
      return
    }
    
    try {
      await deleteMutation.mutateAsync(provider)
    } catch (error) {
      console.error('Failed to delete API key:', error)
    }
  }

  const getStatusBadge = () => {
    if (status === 'personal') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-primary/10 text-primary text-xs font-medium">
          <Key className="h-3 w-3" />
          Using personal key
        </span>
      )
    } else if (status === 'global') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-500/10 text-blue-500 text-xs font-medium">
          🌐 Using global fallback
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-muted text-muted-foreground text-xs font-medium">
          <X className="h-3 w-3" />
          Not configured
        </span>
      )
    }
  }

  return (
    <div className="border border-border rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
            <span className="text-lg">{config.icon}</span>
            {config.displayName}
          </h3>
          {maskedKey && status === 'personal' && (
            <p className="text-xs text-muted-foreground mt-1">
              Current: <code className="bg-muted px-1 py-0.5 rounded">{maskedKey}</code>
            </p>
          )}
        </div>
        {getStatusBadge()}
      </div>

      {/* Input */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">
          New API Key:
        </label>
        <div className="relative">
          <input
            type={showKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={config.placeholder}
            className="w-full px-3 py-2 pr-10 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm text-foreground"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`p-2 rounded-lg text-xs ${
          testResult.valid 
            ? 'bg-green-500/10 text-green-500 border border-green-500/20' 
            : 'bg-red-500/10 text-red-500 border border-red-500/20'
        }`}>
          {testResult.valid ? (
            <span className="flex items-center gap-1">
              <Check className="h-3 w-3" />
              API key is valid!
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <X className="h-3 w-3" />
              {testResult.error || 'Invalid API key'}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleTest}
          disabled={!apiKey.trim() || testMutation.isPending}
          className="px-3 py-1.5 text-sm text-foreground bg-accent hover:bg-accent/80 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          {testMutation.isPending ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Testing...
            </>
          ) : (
            'Test'
          )}
        </button>
        
        <button
          onClick={handleSave}
          disabled={!apiKey.trim() || updateMutation.isPending || (testResult && !testResult.valid)}
          className="px-3 py-1.5 text-sm text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          {updateMutation.isPending ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Saving...
            </>
          ) : (
            'Save'
          )}
        </button>

        {status === 'personal' && (
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="ml-auto px-3 py-1.5 text-sm text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          >
            {deleteMutation.isPending ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </button>
        )}
      </div>

      {/* Success message */}
      {updateMutation.isSuccess && (
        <div className="p-2 rounded-lg bg-green-500/10 text-green-500 text-xs border border-green-500/20">
          ✓ API key saved successfully!
        </div>
      )}

      {deleteMutation.isSuccess && (
        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 text-xs border border-blue-500/20">
          ✓ API key deleted. Now using {status === 'global' ? 'global fallback' : 'no key'}.
        </div>
      )}
    </div>
  )
}

export function APIKeysSection() {
  const { data, isLoading } = useApiKeyStatus()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const getKeyStatus = (provider: Provider) => {
    const key = data?.keys.find(k => k.provider === provider)
    return {
      status: key?.status || 'none',
      maskedKey: key?.masked_key || null
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">API Keys</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure your personal API keys for different AI providers. Keys are encrypted and stored securely.
        </p>
      </div>

      <div className="space-y-4">
        {(['anthropic', 'openai', 'openrouter'] as Provider[]).map(provider => {
          const { status, maskedKey } = getKeyStatus(provider)
          return (
            <ApiKeyInput
              key={provider}
              provider={provider}
              status={status as 'personal' | 'global' | 'none'}
              maskedKey={maskedKey}
            />
          )
        })}
      </div>

      <div className="bg-muted/50 border border-border rounded-lg p-4 text-xs text-muted-foreground">
        <p className="font-medium mb-1">🔒 Security & Privacy</p>
        <ul className="list-disc list-inside space-y-1">
          <li>All API keys are encrypted using Fernet encryption before storage</li>
          <li>Keys are only decrypted when needed for API calls</li>
          <li>If you don't set a personal key, the global fallback key is used</li>
          <li>You can delete your personal key anytime to revert to the global key</li>
        </ul>
      </div>
    </div>
  )
}
