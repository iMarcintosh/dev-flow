import { useState, FormEvent } from 'react'
import { useNavigate, Link } from '@tanstack/react-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { RegisterData } from '@/types'
import logoLarge from '@/assets/images/logos/devflow-logo-large.png'
import { Starfield } from './Starfield'

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const userData: RegisterData = {
        email,
        password,
        full_name: fullName || undefined,
      }
      const { data } = await api.post('/api/auth/register', userData)
      
      setAuth(data.user, data.access_token)
      
      navigate({ to: '/board', search: { project_id: undefined } })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 relative">
      {/* Animated Starfield Background */}
      <Starfield />
      
      <div className="w-full max-w-md relative z-10">
        {/* Logo with glow */}
        <div className="text-center mb-2 relative">
          <div className="relative inline-block">
            {/* Smaller, tighter glow effect */}
            <div className="absolute inset-0 blur-2xl bg-gradient-to-r from-violet-500 via-purple-500 to-pink-500 animate-glow-pulse" />
            <img 
              src={logoLarge} 
              alt="DevFlow Logo" 
              className="relative w-64 h-auto mx-auto mb-1 drop-shadow-2xl"
            />
          </div>
          <p className="text-muted-foreground text-sm mb-2">Create your account</p>
        </div>

        {/* Register card with glow */}
        <div className="relative">
          {/* Card glow effect */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg blur opacity-20 animate-subtle-glow" />
          <div className="relative bg-card border border-border rounded-lg p-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-foreground mb-2">
                Full Name (Optional)
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                Password (min. 8 characters)
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                required
                minLength={8}
                disabled={loading}
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-2 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="relative w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-50 group overflow-hidden"
            >
              {/* Button glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity blur-xl" />
              <span className="relative">{loading ? 'Creating account...' : 'Sign Up'}</span>
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </div>
          </div>
        </div>
      </div>
    </div>
  )
}
