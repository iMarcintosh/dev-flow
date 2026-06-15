import { Link, useMatchRoute, useNavigate, useRouterState } from '@tanstack/react-router'
import { LayoutDashboard, Cpu, Settings as SettingsIcon, LogOut, ChevronDown, Users, FolderOpen, Check, Plus, Loader2, BookOpen, BarChart3 } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useProjects, useCreateProject } from '@/services/queries'
import logoHorizontal from '@/assets/images/logos/devflow-logo-horizontal.png'
import { useState, useRef, useEffect } from 'react'

export function Sidebar() {
  const matchRoute = useMatchRoute()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const projectDropdownRef = useRef<HTMLDivElement>(null)

  const { data: projects = [] } = useProjects()
  const createProject = useCreateProject()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')

  // Read active project_id from current URL search params (works on any route)
  const routerState = useRouterState()
  const searchParams = routerState.location.search
  const urlParams = new URLSearchParams(searchParams)
  const activeProjectId = urlParams.get('project_id') ?? undefined
  const activeProject = projects.find(p => p.id === activeProjectId) ?? projects[0]

  const navigation = [
    { name: 'Board', href: '/board', icon: LayoutDashboard, keepProject: true },
    { name: 'Agent Hub', href: '/agents', icon: Cpu, keepProject: true },
    { name: 'Teams', href: '/teams', icon: Users, keepProject: false },
    { name: 'Notebook', href: '/notebook', icon: BookOpen, keepProject: true },
    { name: 'Analytics', href: '/analytics', icon: BarChart3, keepProject: false },
  ]

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
      if (projectDropdownRef.current && !projectDropdownRef.current.contains(event.target as Node)) {
        setIsProjectDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return
    const newProject = await createProject.mutateAsync({
      name: newProjectName.trim(),
      description: newProjectDescription.trim() || undefined,
    })
    setNewProjectName('')
    setNewProjectDescription('')
    setShowCreateModal(false)
    setIsProjectDropdownOpen(false)
    navigate({ to: '/board', search: { project_id: newProject.id } })
  }

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
              search={(prev) => ({ ...prev, project_id: item.keepProject ? activeProjectId : undefined })}
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

      {/* Project Switcher */}
      {projects.length > 0 && (
        <div className="border-t border-border px-3 py-3" ref={projectDropdownRef}>
          <button
            onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-accent transition-colors"
          >
            <FolderOpen className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="flex-1 min-w-0 text-left text-foreground truncate">
              {activeProject?.name ?? 'Select project'}
            </span>
            <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform flex-shrink-0 ${isProjectDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isProjectDropdownOpen && (
            <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
              {projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    const currentPath = routerState.location.pathname
                    navigate({ to: currentPath as any, search: { project_id: project.id } })
                    setIsProjectDropdownOpen(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
                >
                  {project.id === activeProject?.id ? (
                    <Check className="h-3.5 w-3.5 text-primary flex-shrink-0" />
                  ) : (
                    <span className="h-3.5 w-3.5 flex-shrink-0" />
                  )}
                  <span className="truncate">{project.name}</span>
                </button>
              ))}
              <div className="border-t border-border">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                >
                  <Plus className="h-3.5 w-3.5 flex-shrink-0" />
                  Neues Projekt
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card border border-border rounded-lg p-6 w-80 shadow-xl">
            <h2 className="text-base font-semibold text-foreground mb-4">Neues Projekt erstellen</h2>
            <form onSubmit={handleCreateProject} className="space-y-3">
              <input
                type="text"
                value={newProjectName}
                onChange={e => setNewProjectName(e.target.value)}
                placeholder="Projektname"
                required
                autoFocus
                className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <textarea
                value={newProjectDescription}
                onChange={e => setNewProjectDescription(e.target.value)}
                placeholder="Beschreibung (optional)"
                rows={2}
                className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              />
              <div className="flex gap-2 pt-1">
                <button
                  type="submit"
                  disabled={!newProjectName.trim() || createProject.isPending}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {createProject.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  Erstellen
                </button>
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); setNewProjectName(''); setNewProjectDescription('') }}
                  className="px-3 py-2 border border-border rounded-lg text-sm text-foreground hover:bg-muted transition-colors"
                >
                  Abbrechen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
