import { Link, useMatchRoute } from '@tanstack/react-router'
import { LayoutDashboard, Cpu, Settings, LogOut } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import logoHorizontal from '@/assets/images/logos/devflow-logo-horizontal.png'

export function Sidebar() {
  const matchRoute = useMatchRoute()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)

  const navigation = [
    { name: 'Board', href: '/board', icon: LayoutDashboard },
    { name: 'Agent Hub', href: '/agents', icon: Cpu },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  const isActive = (path: string) => {
    return matchRoute({ to: path }) !== false
  }

  return (
    <div className="flex h-screen w-64 flex-col border-r border-border bg-card">
      {/* Logo with subtle glow */}
      <div className="relative flex h-16 items-center border-b border-border px-4">
        {/* Subtle glow */}
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-purple-500/10 blur-xl" />
        <img 
          src={logoHorizontal} 
          alt="DevFlow" 
          className="relative h-8 w-auto drop-shadow-lg"
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`
                group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all
                ${active
                  ? 'bg-primary/10 text-primary shadow-lg shadow-primary/20'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                }
              `}
            >
              {/* Active item glow */}
              {active && (
                <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-lg blur-sm" />
              )}
              <Icon className={`relative h-5 w-5 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`} />
              <span className="relative">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* User Info + Logout */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/20 text-primary text-sm font-medium">
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </p>
            <p className="text-xs text-muted-foreground truncate">{user?.email || 'user@example.com'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </div>
  )
}
