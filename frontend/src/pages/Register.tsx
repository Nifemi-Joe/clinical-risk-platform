import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PublicNav from '../components/PublicNav'
import { useAuth } from '../lib/auth'
import { listDoctors, UserOut } from '../lib/api'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState<'patient' | 'doctor'>('patient')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [doctorId, setDoctorId] = useState<number | ''>('')
  const [doctors, setDoctors] = useState<UserOut[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (role === 'patient') listDoctors().then(setDoctors).catch(() => setDoctors([]))
  }, [role])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register({
        email, password, full_name: fullName, role,
        doctor_id: role === 'patient' ? Number(doctorId) : undefined,
      })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-sm mx-auto px-6 pt-16 pb-20">
        <h1 className="text-3xl mb-2">Register</h1>
        <p className="text-sm text-muted mb-8">
          Admin accounts are created by an existing admin, not through self-registration.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="field-label">I am a</label>
            <div className="flex gap-2">
              {(['patient', 'doctor'] as const).map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setRole(r)}
                  className={`flex-1 px-3 py-2 rounded-sm text-sm border capitalize ${
                    role === r ? 'border-teal bg-teal-light text-teal-dark' : 'border-border text-muted'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="field-label">Full name</label>
            <input required className="field-input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="field-label">Email</label>
            <input type="email" required className="field-input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="field-label">Password (8+ characters)</label>
            <input
              type="password"
              required
              minLength={8}
              className="field-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {role === 'patient' && (
            <div>
              <label className="field-label">Your doctor</label>
              <select required className="field-input" value={doctorId} onChange={(e) => setDoctorId(Number(e.target.value))}>
                <option value="" disabled>Select a doctor…</option>
                {doctors.map((d) => (
                  <option key={d.id} value={d.id}>{d.full_name}</option>
                ))}
              </select>
              {doctors.length === 0 && (
                <p className="text-xs text-muted mt-1.5">No doctors registered yet — register a doctor account first.</p>
              )}
            </div>
          )}
          {error && <p className="text-sm text-clay">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="text-sm text-muted mt-6">
          Already registered? <Link to="/login" className="text-teal-dark">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
