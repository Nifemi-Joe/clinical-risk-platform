import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const links = [
  { to: '/data', label: 'Data & methodology' },
  { to: '/reports', label: 'Reports' },
  { to: '/documentation', label: 'Documentation' },
]

export default function PublicNav() {
  const { user } = useAuth()
  const location = useLocation()

  return (
    <header className="border-b border-border">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="font-serif text-lg tracking-tight">
          Clinical Risk Platform
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={
                location.pathname === l.to
                  ? 'text-ink border-b border-teal pb-0.5'
                  : 'text-muted hover:text-ink transition-colors'
              }
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          {user ? (
            <Link to="/dashboard" className="btn-primary text-sm py-2 px-4">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm text-muted hover:text-ink transition-colors">
                Sign in
              </Link>
              <Link to="/register" className="btn-primary text-sm py-2 px-4">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
