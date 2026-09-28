import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { deactivateUser, listAllUsers, UserOut } from '../lib/api'

export default function AdminDashboard() {
  const [users, setUsers] = useState<UserOut[]>([])
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    listAllUsers().then((u) => {
      setUsers(u)
      setLoading(false)
    })
  }

  useEffect(load, [])

  async function handleDeactivate(id: number) {
    await deactivateUser(id)
    load()
  }

  const counts = users.reduce(
    (acc, u) => ({ ...acc, [u.role]: (acc[u.role] || 0) + 1 }),
    {} as Record<string, number>
  )

  return (
    <Layout title="Admin dashboard">
      <div className="grid grid-cols-3 gap-4 mb-8">
        {(['patient', 'doctor', 'admin'] as const).map((role) => (
          <div key={role} className="card">
            <div className="data-label mb-1 capitalize">{role}s</div>
            <div className="text-2xl font-serif">{counts[role] || 0}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="data-label mb-3">All users</div>
        {loading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted border-b border-border">
                <th className="py-2 font-normal">Name</th>
                <th className="py-2 font-normal">Email</th>
                <th className="py-2 font-normal">Role</th>
                <th className="py-2 font-normal">Status</th>
                <th className="py-2 font-normal"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-border last:border-0">
                  <td className="py-2">{u.full_name}</td>
                  <td className="py-2 text-muted">{u.email}</td>
                  <td className="py-2 capitalize">{u.role}</td>
                  <td className="py-2">
                    <span className={u.is_active ? 'text-teal-dark' : 'text-clay'}>
                      {u.is_active ? 'Active' : 'Deactivated'}
                    </span>
                  </td>
                  <td className="py-2 text-right">
                    {u.is_active && u.role !== 'admin' && (
                      <button
                        onClick={() => handleDeactivate(u.id)}
                        className="text-xs text-clay hover:underline"
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}
