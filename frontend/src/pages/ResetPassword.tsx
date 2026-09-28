import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import PublicNav from '../components/PublicNav'
import { resetPassword } from '../lib/api'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirm) {
      setError("Passwords don't match")
      return
    }
    setLoading(true)
    setError(null)
    try {
      await resetPassword(token, password)
      setDone(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: any) {
      setError(err.message || 'Reset link is invalid or expired')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen">
        <PublicNav />
        <div className="max-w-sm mx-auto px-6 pt-20">
          <p className="text-sm text-clay">
            No reset token found in the link. Request a new one from the{' '}
            <Link to="/forgot-password" className="text-teal-dark">reset page</Link>.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-sm mx-auto px-6 pt-20">
        <h1 className="text-3xl mb-2">Choose a new password</h1>
        {done ? (
          <p className="text-sm text-teal-dark mt-6">Password updated. Redirecting to sign in…</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 mt-8">
            <div>
              <label className="field-label">New password (8+ characters)</label>
              <input
                type="password"
                required
                minLength={8}
                className="field-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="field-label">Confirm new password</label>
              <input
                type="password"
                required
                className="field-input"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-clay">{error}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Updating…' : 'Update password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
