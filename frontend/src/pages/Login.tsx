import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PublicNav from '../components/PublicNav'
import { useAuth } from '../lib/auth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-sm mx-auto px-6 pt-20">
        <h1 className="text-3xl mb-2">Sign in</h1>
        <p className="text-sm text-muted mb-8">Access your patient, doctor, or admin dashboard.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="field-label">Email</label>
            <input
              type="email"
              required
              className="field-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="field-label">Password</label>
            <input
              type="password"
              required
              className="field-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-clay">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="text-sm text-muted mt-6">
          No account? <Link to="/register" className="text-teal-dark">Register</Link>
        </p>
        <p className="text-sm text-muted mt-2">
          <Link to="/forgot-password" className="text-teal-dark">Forgot your password?</Link>
        </p>
      </div>
    </div>
  )
}
