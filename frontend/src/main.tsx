import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter, createRootRoute, createRoute } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import LoginPage from './components/auth/LoginPage'
import RegisterPage from './components/auth/RegisterPage'
import BoardPage from './components/board/BoardPage'
import AgentHubPage from './components/agent-hub/AgentHubPage'
import SettingsPage from './components/settings/SettingsPage'

const queryClient = new QueryClient()

const rootRoute = createRootRoute()

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => {
    window.location.href = '/login'
    return null
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
})

const agentsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agents',
  component: AgentHubPage,
})

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  registerRoute,
  boardRoute,
  agentsRoute,
  settingsRoute,
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
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
