import { useState } from 'react'
import { Link } from 'react-router-dom'
import PublicNav from '../components/PublicNav'
import { forgotPassword } from '../lib/api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await forgotPassword(email)
      // Always show the same success state regardless of whether the email
      // exists - matches the backend's deliberate no-enumeration behavior.
      setSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-sm mx-auto px-6 pt-20">
        <h1 className="text-3xl mb-2">Reset your password</h1>
        {sent ? (
          <p className="text-sm text-muted mt-6">
            If that email is registered, a reset link has been sent. Check
            your inbox — the link expires in 30 minutes.
          </p>
        ) : (
          <>
            <p className="text-sm text-muted mb-8">
              Enter your email and we'll send you a reset link.
            </p>
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
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Sending…' : 'Send reset link'}
              </button>
            </form>
          </>
        )}
        <p className="text-sm text-muted mt-6">
          <Link to="/login" className="text-teal-dark">Back to sign in</Link>
        </p>
      </div>
    </div>
  )
}
