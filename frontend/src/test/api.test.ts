import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError, loginUser, myPredictions } from '../lib/api'

describe('API client', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends no Authorization header when there is no token', async () => {
    ;(fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ access_token: 'abc', token_type: 'bearer', role: 'patient', full_name: 'Test', user_id: 1 }),
    })

    await loginUser('a@example.com', 'password123')

    const [, options] = (fetch as any).mock.calls[0]
    expect(options.headers.Authorization).toBeUndefined()
  })

  it('attaches the stored bearer token to authenticated requests', async () => {
    localStorage.setItem('token', 'my-real-token')
    ;(fetch as any).mockResolvedValue({ ok: true, status: 200, json: async () => [] })

    await myPredictions()

    const [url, options] = (fetch as any).mock.calls[0]
    expect(url).toBe('/api/predictions/mine')
    expect(options.headers.Authorization).toBe('Bearer my-real-token')
  })

  it('throws ApiError with the server-provided status and detail on failure', async () => {
    ;(fetch as any).mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Incorrect email or password' }),
    })

    await expect(loginUser('a@example.com', 'wrong')).rejects.toMatchObject({
      status: 401,
      message: 'Incorrect email or password',
    })
  })

  it('ApiError is a real Error subclass usable in normal catch blocks', () => {
    const err = new ApiError(403, 'Forbidden')
    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(403)
  })
})
