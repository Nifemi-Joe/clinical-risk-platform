import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { getMe, loginUser, registerUser, UserOut } from './api'

interface AuthContextValue {
  user: UserOut | null
  loading: boolean
  login: (email: string, password: string) => Promise<UserOut>
  register: (data: {
    email: string
    password: string
    full_name: string
    role: 'patient' | 'doctor'
    doctor_id?: number | null
  }) => Promise<UserOut>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const res = await loginUser(email, password)
    localStorage.setItem('token', res.access_token)
    const me = await getMe()
    setUser(me)
    return me
  }

  async function register(data: {
    email: string
    password: string
    full_name: string
    role: 'patient' | 'doctor'
    doctor_id?: number | null
  }) {
    const res = await registerUser(data)
    localStorage.setItem('token', res.access_token)
    const me = await getMe()
    setUser(me)
    return me
  }

  function logout() {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
