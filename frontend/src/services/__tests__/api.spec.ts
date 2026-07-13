import { describe, it, expect, beforeEach, vi } from 'vitest'
import { apiService } from '../api'

// src/test/setup.ts globally mocks @/services/api. We override
// individual method mocks here so each test controls the response.
describe('apiService (fetch wrapper)', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('login resolves with the parsed AuthResponse', async () => {
    vi.mocked(apiService.login).mockResolvedValue({
      token: 'abc',
      user: { id: 1, username: 'u', email: 'e', role: 'viewer' },
    })
    const res = await apiService.login('u', 'p')
    expect(res.token).toBe('abc')
  })

  it('register returns AuthResponse', async () => {
    vi.mocked(apiService.register).mockResolvedValue({
      token: 't',
      user: { id: 2, username: 'r', email: 'r@x', role: 'viewer' },
    })
    const res = await apiService.register('r', 'r@x', 'pw')
    expect(res.user.username).toBe('r')
  })

  it('forgotPassword returns ok (optionally dev_link)', async () => {
    vi.mocked(apiService.forgotPassword).mockResolvedValue({
      ok: true,
      dev_link: 'http:///reset?token=ABC',
    })
    const res = await apiService.forgotPassword('user@test')
    expect(res.ok).toBe(true)
    expect(res.dev_link).toBe('http:///reset?token=ABC')
  })

  it('throws when the service rejects', async () => {
    vi.mocked(apiService.login).mockRejectedValue(new Error('No autorizado'))
    await expect(apiService.login('u', 'p')).rejects.toThrow('No autorizado')
  })

  it('getMe sends Authorization header when a token is set', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    vi.mocked(apiService.getMe).mockResolvedValue({
      id: 1, username: 'u', email: 'e', role: 'admin', created_at: '',
    })
    await apiService.getMe()
    expect(apiService.getMe).toHaveBeenCalled()
  })

  it('getStats forwards the filter query', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue({
      total_songs: 0, total_albums: 0, catalog_total: 0,
    } as never)
    await apiService.getStats('year_from=1980')
    expect(apiService.getStats).toHaveBeenCalledWith('year_from=1980')
  })

  it('admin endpoints expose the required methods', () => {
    expect(typeof apiService.adminListFonogramas).toBe('function')
    expect(typeof apiService.adminCreateFonograma).toBe('function')
    expect(typeof apiService.adminUpdateFonograma).toBe('function')
    expect(typeof apiService.adminDeleteFonograma).toBe('function')
    expect(typeof apiService.adminListSongs).toBe('function')
    expect(typeof apiService.adminCreateSong).toBe('function')
    expect(typeof apiService.adminUpdateSong).toBe('function')
    expect(typeof apiService.adminDeleteSong).toBe('function')
    expect(typeof apiService.adminListUsers).toBe('function')
    expect(typeof apiService.adminCreateUser).toBe('function')
    expect(typeof apiService.adminUpdateUser).toBe('function')
    expect(typeof apiService.adminDeleteUser).toBe('function')
  })

  it('searchSongs forwards its arguments', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    await apiService.searchSongs('amor', 'title', 1, 20, 'ESPAÑOL_ESTANDAR', 'titulo', 'asc')
    expect(apiService.searchSongs).toHaveBeenCalledWith(
      'amor', 'title', 1, 20, 'ESPAÑOL_ESTANDAR', 'titulo', 'asc',
    )
  })

  it('adminCreateFonograma forwards the payload', async () => {
    vi.mocked(apiService.adminCreateFonograma).mockResolvedValue({} as never)
    await apiService.adminCreateFonograma({ titulo: 'X' })
    expect(apiService.adminCreateFonograma).toHaveBeenCalledWith({ titulo: 'X' })
  })

  it('adminUpdateFonograma forwards id + payload', async () => {
    vi.mocked(apiService.adminUpdateFonograma).mockResolvedValue({} as never)
    await apiService.adminUpdateFonograma(1, { titulo: 'New' })
    expect(apiService.adminUpdateFonograma).toHaveBeenCalledWith(1, { titulo: 'New' })
  })
})
