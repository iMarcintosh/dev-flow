import { AppLayout } from '@/components/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { User, Mail, Shield, Calendar } from 'lucide-react'

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user)

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
