import { Link, useMatchRoute } from '@tanstack/react-router'
import { LayoutDashboard, Cpu, Settings as SettingsIcon, LogOut, ChevronDown, Users } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import logoHorizontal from '@/assets/images/logos/devflow-logo-horizontal.png'
import { useState, useRef, useEffect } from 'react'

export function Sidebar() {
  const matchRoute = useMatchRoute()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const navigation = [
    { name: 'Board', href: '/board', icon: LayoutDashboard },
    { name: 'Agent Hub', href: '/agents', icon: Cpu },
    { name: 'Teams', href: '/teams', icon: Users },
  ]

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const isActive = (path: string) => {
    return matchRoute({ to: path }) !== false
  }

  return (
    <div className="flex h-screen w-64 flex-col border-r border-border bg-card">
      {/* Logo with subtle glow */}
      <div className="relative flex h-20 items-center justify-center border-b border-border px-6">
        {/* Subtle glow */}
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/5 to-purple-500/5 blur-xl" />
        <img 
          src={logoHorizontal} 
          alt="DevFlow" 
          className="relative w-full h-auto max-h-16 object-contain drop-shadow-lg"
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
                group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors
                ${active
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                }
              `}
            >
              <Icon className={`h-5 w-5 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* User Info + Dropdown + Logout */}
      <div className="border-t border-border p-4" ref={dropdownRef}>
        {/* User Info - Clickable for dropdown */}
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex w-full items-center gap-3 mb-3 rounded-lg px-2 py-2 hover:bg-accent transition-colors"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/20 text-primary text-sm font-medium">
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </p>
            <p className="text-xs text-muted-foreground truncate">{user?.email || 'user@example.com'}</p>
          </div>
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="mb-3 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
            <Link
              to="/settings"
              onClick={() => setIsDropdownOpen(false)}
              className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
            >
              <SettingsIcon className="h-4 w-4" />
              Settings
            </Link>
          </div>
        )}

        {/* Logout Button - Separate */}
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
