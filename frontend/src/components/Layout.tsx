import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuth } from '../lib/auth'

export default function Layout({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-border flex flex-col justify-between py-6">
        <div>
          <Link to="/" className="block px-6 font-serif text-lg mb-8">
            Clinical Risk Platform
          </Link>
          <div className="px-6 mb-6">
            <div className="text-sm font-medium">{user?.full_name}</div>
            <div className="data-label">{user?.role}</div>
          </div>
          <nav className="flex flex-col gap-1 px-3 text-sm">
            <Link to="/dashboard" className="px-3 py-2 rounded-sm bg-teal-light text-teal-dark font-medium">
              Dashboard
            </Link>
            <Link to="/reports" className="px-3 py-2 rounded-sm text-muted hover:bg-teal-light hover:text-ink transition-colors">
              Reports
            </Link>
            <Link to="/data" className="px-3 py-2 rounded-sm text-muted hover:bg-teal-light hover:text-ink transition-colors">
              Data &amp; methodology
            </Link>
            <Link to="/documentation" className="px-3 py-2 rounded-sm text-muted hover:bg-teal-light hover:text-ink transition-colors">
              Documentation
            </Link>
          </nav>
        </div>
        <button
          onClick={logout}
          className="mx-6 flex items-center gap-2 text-sm text-muted hover:text-clay transition-colors"
        >
          <LogOut size={15} /> Sign out
        </button>
      </aside>
      <main className="flex-1 min-w-0">
        <div className="max-w-5xl mx-auto px-8 py-10">
          <h1 className="text-2xl mb-8">{title}</h1>
          {children}
        </div>
      </main>
    </div>
  )
}
