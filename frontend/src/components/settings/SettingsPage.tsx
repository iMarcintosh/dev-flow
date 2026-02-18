import { AppLayout } from '@/components/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { User, Mail, Shield, Calendar, Cpu, RefreshCw, Save, Loader2 } from 'lucide-react'
import { useAvailableModels, useUpdateUserPreferences, useRefreshModels } from '@/services/queries'
import ModelSelector from './ModelSelector'
import { useState, useEffect } from 'react'

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user)
  const { data: modelsData, isLoading: modelsLoading } = useAvailableModels()
  const updatePreferences = useUpdateUserPreferences()
  const refreshModels = useRefreshModels()
  
  // Local state for preferences
  const [taskCreatorModel, setTaskCreatorModel] = useState('')
  const [chatAgentModel, setChatAgentModel] = useState('')
  const [hasChanges, setHasChanges] = useState(false)

  // Initialize from user data
  useEffect(() => {
    if (user?.preferred_models) {
      setTaskCreatorModel(user.preferred_models.task_creator || 'claude-3-haiku-20240307')
      setChatAgentModel(user.preferred_models.chat_agent || 'claude-3-haiku-20240307')
    } else {
      setTaskCreatorModel('claude-3-haiku-20240307')
      setChatAgentModel('claude-3-haiku-20240307')
    }
  }, [user])

  // Track changes
  useEffect(() => {
    const currentTask = user?.preferred_models?.task_creator || 'claude-3-haiku-20240307'
    const currentChat = user?.preferred_models?.chat_agent || 'claude-3-haiku-20240307'
    setHasChanges(
      taskCreatorModel !== currentTask || chatAgentModel !== currentChat
    )
  }, [taskCreatorModel, chatAgentModel, user])

  const handleSave = async () => {
    try {
      await updatePreferences.mutateAsync({
        task_creator: taskCreatorModel,
        chat_agent: chatAgentModel
      })
    } catch (error) {
      console.error('Failed to save preferences:', error)
    }
  }

  const handleRefreshModels = async () => {
    try {
      await refreshModels.mutateAsync()
    } catch (error) {
      console.error('Failed to refresh models:', error)
    }
  }

  if (!user) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </AppLayout>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="border-b border-border bg-card">
          <div className="max-w-4xl mx-auto px-8 py-6">
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
            <p className="text-muted-foreground mt-2">
              Manage your account settings and preferences
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-8 py-8">
          {/* Profile Section */}
          <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-6 flex items-center gap-2">
              <User className="w-5 h-5" />
              Profile Information
            </h2>

            <div className="space-y-4">
              {/* Avatar */}
              <div className="flex items-center gap-4">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/20 text-primary text-2xl font-bold">
                  {user.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Profile Picture</p>
                  <p className="text-xs text-muted-foreground mt-1">Click to change (coming soon)</p>
                </div>
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={user.full_name || 'Not set'}
                  disabled
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg text-foreground"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Email Address
                </label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg text-foreground"
                />
              </div>

              {/* Status Badges */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Account Status
                </label>
                <div className="flex gap-2">
                  {user.is_verified ? (
                    <span className="px-3 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full text-sm">
                      ✓ Verified
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 rounded-full text-sm">
                      ⚠ Not Verified
                    </span>
                  )}
                  {user.is_active ? (
                    <span className="px-3 py-1 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded-full text-sm">
                      ● Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded-full text-sm">
                      ● Inactive
                    </span>
                  )}
                </div>
              </div>

              {/* Account Created */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Member Since
                </label>
                <input
                  type="text"
                  value={user.created_at ? formatDate(user.created_at) : 'Unknown'}
                  disabled
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg text-foreground"
                />
              </div>
            </div>
          </div>

          {/* Security Section */}
          <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-6 flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Security
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Password
                </label>
                <button className="px-4 py-2 bg-background border border-border text-foreground rounded-lg hover:bg-accent transition-colors">
                  Change Password (coming soon)
                </button>
              </div>
            </div>
          </div>

          {/* AI Model Preferences Section */}
          <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                  <Cpu className="w-5 h-5" />
                  AI Model Preferences
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Choose which AI models to use for different agents
                </p>
              </div>
              <button
                onClick={handleRefreshModels}
                disabled={refreshModels.isPending}
                className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {refreshModels.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Refresh Models
              </button>
            </div>

            {modelsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                <span className="ml-3 text-gray-400">Loading available models...</span>
              </div>
            ) : modelsData ? (
              <div className="space-y-6">
                {/* Task Creator Model */}
                <ModelSelector
                  label="Task Creator Agent"
                  value={taskCreatorModel}
                  onChange={setTaskCreatorModel}
                  models={modelsData}
                />

                {/* Chat Agent Model */}
                <ModelSelector
                  label="Chat Agent"
                  value={chatAgentModel}
                  onChange={setChatAgentModel}
                  models={modelsData}
                />

                {/* Save Button */}
                {hasChanges && (
                  <div className="pt-4 border-t border-gray-700">
                    <button
                      onClick={handleSave}
                      disabled={updatePreferences.isPending}
                      className="w-full px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {updatePreferences.isPending ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="w-5 h-5" />
                          Save Preferences
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* API Key Status */}
                <div className="pt-4 border-t border-gray-700">
                  <p className="text-sm font-medium text-gray-300 mb-3">API Key Status</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="px-3 py-2 bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                        <span className="text-xs text-gray-400">Anthropic</span>
                      </div>
                    </div>
                    <div className="px-3 py-2 bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-gray-600"></div>
                        <span className="text-xs text-gray-400">OpenAI</span>
                      </div>
                    </div>
                    <div className="px-3 py-2 bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-gray-600"></div>
                        <span className="text-xs text-gray-400">OpenRouter</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Configure API keys in your .env file to enable additional providers
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                Failed to load models. Please try refreshing.
              </div>
            )}
          </div>

          {/* Preferences Section */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">Preferences</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-foreground font-medium">Dark Mode</p>
                  <p className="text-sm text-muted-foreground">Currently enabled by default</p>
                </div>
                <div className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-sm">
                  Active
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-foreground font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive updates about your projects</p>
                </div>
                <label className="relative inline-flex items-center cursor-not-allowed">
                  <input type="checkbox" className="sr-only peer" disabled />
                  <div className="w-11 h-6 bg-background border border-border rounded-full peer-checked:bg-primary"></div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
