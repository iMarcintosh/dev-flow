import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter, createRootRoute, createRoute, redirect } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import LoginPage from './components/auth/LoginPage'
import RegisterPage from './components/auth/RegisterPage'
import BoardPage from './components/board/BoardPage'
import AgentHubPage from './components/agent-hub/AgentHubPage'
import AgentChatPage from './components/agent-chat/AgentChatPage'
import SettingsPage from './components/settings/SettingsPage'
import TeamManagementPage from './components/teams/TeamManagementPage'
import { ToastProvider } from './hooks/useToast'

const queryClient = new QueryClient()

const rootRoute = createRootRoute()

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    throw redirect({ to: '/login' })
  },
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: RegisterPage,
})

const boardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/board',
  component: BoardPage,
  validateSearch: (search: Record<string, unknown>) => ({
    project_id: search.project_id as string | undefined,
  }),
})

const agentsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agents',
  component: AgentHubPage,
})

const chatRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/chat',
  component: AgentChatPage,
  validateSearch: (search: Record<string, unknown>) => ({
    agent_id: search.agent_id as string | undefined,
    conversation_id: search.conversation_id as string | undefined,
    project_id: search.project_id as string | undefined,
  }),
})

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})

const teamsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/teams',
  component: TeamManagementPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  registerRoute,
  boardRoute,
  agentsRoute,
  chatRoute,
  settingsRoute,
  teamsRoute,
])

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
