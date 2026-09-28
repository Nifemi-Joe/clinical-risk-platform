import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../lib/auth'
import * as api from '../lib/api'

function Probe() {
  const { user, login, logout, loading } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.full_name : 'none'}</span>
      <button onClick={() => login('a@example.com', 'password123')}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('starts with no user when there is no stored token', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))
    expect(screen.getByTestId('user').textContent).toBe('none')
  })

  it('login() stores the token and populates the user from a real API round-trip', async () => {
    vi.spyOn(api, 'loginUser').mockResolvedValue({
      access_token: 'tok123', token_type: 'bearer', role: 'patient', full_name: 'Sam Jones', user_id: 2,
    })
    vi.spyOn(api, 'getMe').mockResolvedValue({
      id: 2, email: 'a@example.com', full_name: 'Sam Jones', role: 'patient', doctor_id: 1, is_active: true,
    })

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))

    await userEvent.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('user').textContent).toBe('Sam Jones'))
    expect(localStorage.getItem('token')).toBe('tok123')
  })

  it('logout() clears both the stored token and the user state', async () => {
    localStorage.setItem('token', 'existing-token')
    vi.spyOn(api, 'getMe').mockResolvedValue({
      id: 1, email: 'a@example.com', full_name: 'Existing User', role: 'doctor', doctor_id: null, is_active: true,
    })

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('user').textContent).toBe('Existing User'))

    await userEvent.click(screen.getByText('logout'))

    expect(screen.getByTestId('user').textContent).toBe('none')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('clears an invalid stored token instead of leaving the user stuck logged-in-looking', async () => {
    localStorage.setItem('token', 'expired-or-invalid')
    vi.spyOn(api, 'getMe').mockRejectedValue(new api.ApiError(401, 'Could not validate credentials'))

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))
    expect(screen.getByTestId('user').textContent).toBe('none')
    expect(localStorage.getItem('token')).toBeNull()
  })
})
