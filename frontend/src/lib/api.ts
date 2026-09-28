// In dev, Vite's server.proxy forwards /api -> localhost:8000 (see
// vite.config.ts). In production, set VITE_API_URL at build time to the
// full backend URL if frontend and backend are deployed to different
// hosts/domains (e.g. Vercel + Render) - falls back to the same-origin
// '/api' path for a single-host deployment behind nginx (see
// docker/nginx.conf), which is what docker-compose uses.
const BASE = import.meta.env.VITE_API_URL || '/api'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail || 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// --- Types matching api/schemas.py exactly ---

export interface TokenResponse {
  access_token: string
  token_type: string
  role: 'admin' | 'doctor' | 'patient'
  full_name: string
  user_id: number
}

export interface UserOut {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'doctor' | 'patient'
  doctor_id: number | null
  is_active: boolean
}

export interface Contributor {
  feature: string
  contribution: number
}

export interface FeatureContribution {
  feature: string
  label: string
  patient_value: string
  contribution: number
  direction: 'increased' | 'decreased' | 'had no effect on'
  magnitude: 'strong' | 'moderate' | 'slight'
}

export interface MethodologySummary {
  model_family: string
  attribution_method: string
  preprocessing: string
  trained_on: string
  performance_summary: string
  selection_rationale: string
  limitations: string[]
}

export interface PredictionResponse {
  disease: string
  model: string
  probability: number
  risk_band: 'low' | 'below-average' | 'elevated' | 'high'
  calibration_context: string
  feature_contributions: FeatureContribution[]
  top_contributors: Contributor[]
  methodology: MethodologySummary
  disclaimer: string
}

export interface PredictionRecord {
  id: number
  patient_id: number
  disease: string
  model_used: string
  probability: number
  created_at: string
}

export interface MessageOut {
  id: number
  sender_id: number
  sender_name: string
  recipient_id: number
  body: string
  read: boolean
  created_at: string
}

// --- Auth ---

export const registerUser = (data: {
  email: string
  password: string
  full_name: string
  role: 'patient' | 'doctor'
  doctor_id?: number | null
}) => request<TokenResponse>('/auth/register', { method: 'POST', body: JSON.stringify(data) })

export const loginUser = (email: string, password: string) =>
  request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })

export const getMe = () => request<UserOut>('/auth/me')

export const forgotPassword = (email: string) =>
  request<{ message: string }>('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) })

export const resetPassword = (token: string, new_password: string) =>
  request<{ message: string }>('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password }) })

export const listDoctors = () => request<UserOut[]>('/users/doctors')

// --- Users (admin) ---

export const listAllUsers = () => request<UserOut[]>('/users')
export const deactivateUser = (userId: number) =>
  request(`/users/${userId}/deactivate`, { method: 'PATCH' })
export const myPatients = () => request<UserOut[]>('/users/my-patients')

// --- Predictions ---

export const predictHeart = (data: Record<string, number>) =>
  request<PredictionResponse>('/predict/heart', { method: 'POST', body: JSON.stringify(data) })

export const predictBreastCancer = (data: Record<string, number>) =>
  request<PredictionResponse>('/predict/breast-cancer', { method: 'POST', body: JSON.stringify(data) })

export const predictDiabetes = (data: Record<string, number>) =>
  request<PredictionResponse>('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) })

export const myPredictions = () => request<PredictionRecord[]>('/predictions/mine')
export const patientPredictions = (patientId: number) =>
  request<PredictionRecord[]>(`/predictions/patient/${patientId}`)

// --- Messaging ---

export const sendMessage = (recipientId: number, body: string) =>
  request<MessageOut>('/messages', { method: 'POST', body: JSON.stringify({ recipient_id: recipientId, body }) })

export const getThread = (otherUserId: number) =>
  request<MessageOut[]>(`/messages/thread/${otherUserId}`)

// --- Reports & models ---

export const getModels = () => request<Record<string, { model: string; selection_rationale: string }>>('/models')
export const getReportsSummary = () => request<Record<string, any[]>>('/reports/summary')
