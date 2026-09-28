import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './lib/auth'

// Route-level code splitting: each page is its own chunk, loaded on
// navigation rather than all bundled into the initial JS payload. The
// heaviest dependency (recharts) only loads when someone actually visits
// Landing or Reports, not on every page load.
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const PatientDashboard = lazy(() => import('./pages/PatientDashboard'))
const DoctorDashboard = lazy(() => import('./pages/DoctorDashboard'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const Reports = lazy(() => import('./pages/Reports'))
const Documentation = lazy(() => import('./pages/Documentation'))
const DataMethodology = lazy(() => import('./pages/DataMethodology'))

function PageFallback() {
  return <div className="min-h-screen flex items-center justify-center text-sm text-muted">Loading…</div>
}

function ProtectedRoute({ children, roles }: { children: JSX.Element; roles?: string[] }) {
  const { user, loading } = useAuth()
  if (loading) return <PageFallback />
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

export default function App() {
  const { user } = useAuth()

  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/documentation" element={<Documentation />} />
        <Route path="/data" element={<DataMethodology />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              {user?.role === 'doctor' ? (
                <DoctorDashboard />
              ) : user?.role === 'admin' ? (
                <AdminDashboard />
              ) : (
                <PatientDashboard />
              )}
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  )
}
