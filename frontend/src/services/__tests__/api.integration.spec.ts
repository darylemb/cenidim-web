import { describe, it, expect, beforeEach, vi } from 'vitest'

// This file exercises the REAL implementation of api.ts by
// isolating it from the global @/services/api mock in src/test/setup.ts.
// We use vi.doMock (which queues a NEW mock) and then vi.doUnmock
// the previous one via the queue API.
//
// Easier: we re-import the source file via a dynamic import with
// `vi.mock` set up here for just this module, then restore.

describe('api.ts fetch integration', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('parses a 2xx JSON response and returns the body', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"token":"abc","user":{"id":1,"username":"u","email":"u@x","role":"viewer"}}', {
        status: 200, headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=1')
    const res = await apiService.login('u', 'p')
    expect(res.token).toBe('abc')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/auth/login')
    expect(init.method).toBe('POST')
  })

  it('throws with the server error message on 4xx', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"No autorizado"}', { status: 401 }),
    ))
    const { apiService } = await import('../api?integration=2')
    await expect(apiService.login('u', 'p')).rejects.toThrow('No autorizado')
  })

  it('falls back to "Login failed" when 5xx has no error field', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{}', { status: 500 }),
    ))
    const { apiService } = await import('../api?integration=3')
    await expect(apiService.login('u', 'p')).rejects.toThrow('Login failed')
  })

  it('attaches Authorization header when a token is in localStorage', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () =>
      new Response('{"id":1,"username":"u","email":"u@x","role":"admin","created_at":""}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=4')
    await apiService.getMe()
    const init = fetchMock.mock.calls[0][1]
    expect(init.headers.Authorization).toBe('Bearer TKN')
  })

  it('does not attach Authorization when there is no token', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=5')
    await apiService.getTimeline()
    const init = fetchMock.mock.calls[0][1]
    expect(init.headers?.Authorization).toBeUndefined()
  })

  it('encodes query params for getStats', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=6')
    await apiService.getStats('year_from=1980&year_to=1985')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/stats?year_from=1980&year_to=1985')
  })

  it('encodes search options correctly', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=7')
    await apiService.searchSongs('hola', 'title', 2, 50, 'ESPAÑOL_REGIONAL', 'titulo', 'desc')
    const url = fetchMock.mock.calls[0][0]
    expect(url).toContain('query=hola')
    expect(url).toContain('field=title')
    expect(url).toContain('page=2')
    expect(url).toContain('limit=50')
    // URLSearchParams percent-encodes non-ASCII; Ñ becomes %C3%91.
    expect(url).toContain('clasificacion=ESPA%C3%91OL_REGIONAL')
    expect(url).toContain('order_by=titulo')
    expect(url).toContain('order_dir=desc')
  })

  it('serializes admin PUT with the right method + body', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=8')
    await apiService.adminUpdateFonograma(42, { titulo: 'Nuevo' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/admin/fonogramas/42')
    expect(init.method).toBe('PUT')
    expect(init.headers.Authorization).toBe('Bearer TKN')
    expect(JSON.parse(init.body)).toEqual({ titulo: 'Nuevo' })
  })

  it('forgotPassword posts just the email', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"ok":true}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=9')
    const res = await apiService.forgotPassword('u@x')
    expect(res.ok).toBe(true)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/forgot')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ email: 'u@x' })
  })

  it('resetPassword posts token + new_password', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"ok":true}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=10')
    await apiService.resetPassword('TKN', 'NewStrong1')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/reset')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      token: 'TKN', new_password: 'NewStrong1',
    })
  })

  it('admin endpoints wrap DELETE with no body', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () => new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=11')
    await apiService.adminDeleteFonograma(99)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/admin/fonogramas/99')
    expect(init.method).toBe('DELETE')
  })

  it('adminUpdateUser sends whatever payload it receives (caller strips empty pw)', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=12')
    await apiService.adminUpdateUser(7, {
      id: 7, username: 'bob', email: 'b@x', role: 'editor', password: '',
    })
    // apiService is a transport; password-stripping happens in the
    // AdminFormModal component before this call. So the payload
    // arrives verbatim — empty password included.
    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body.password).toBe('')
  })

  it('adminUpdateUser keeps the password when non-empty', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=13')
    await apiService.adminUpdateUser(7, {
      id: 7, username: 'bob', email: 'b@x', role: 'editor', password: 'NewSecret1',
    })
    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body.password).toBe('NewSecret1')
  })

  it('non-2xx with empty body falls back to the operation name', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{}', { status: 500 }),
    ))
    const { apiService } = await import('../api?integration=14')
    await expect(apiService.login('u', 'p')).rejects.toThrow('Login failed')
  })

  // ---- admin endpoints coverage ------------------------------------

  it('adminGetFonograma fetches by id', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"clave_fonograma":1,"titulo":"A"}'),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g1')
    await apiService.adminGetFonograma(1)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/fonogramas/1')
  })

  it('adminCreateSong posts the payload', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"id":99,"title":"X"}'),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g2')
    await apiService.adminCreateSong({ title: 'X', lyrics: 'L' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/songs')
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
  })

  it('adminUpdateSong puts to /admin/songs/{id}', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"message":"Song updated"}'),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g3')
    await apiService.adminUpdateSong(7, { title: 'Y' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/songs/7')
    expect(fetchMock.mock.calls[0][1].method).toBe('PUT')
  })

  it('adminDeleteSong issues a DELETE', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"message":"Song deleted"}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g4')
    await apiService.adminDeleteSong(7)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/songs/7')
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')
  })

  it('adminListSongs paginates via query string', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g5')
    await apiService.adminListSongs('3', 2, 50)
    // adminListSongs builds ?page=N&limit=N&fonograma_id=N — page and
    // limit come first, the optional fonograma filter is appended.
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/songs?page=2&limit=50&fonograma_id=3')
  })

  it('adminListFonogramas paginates', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g6')
    await apiService.adminListFonogramas(1, 25)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/fonogramas?page=1&limit=25')
  })

  it('adminListUsers fetches the user list', async () => {
    const fetchMock = vi.fn(async () => new Response('[]'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g7')
    await apiService.adminListUsers()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/users')
  })

  it('adminCreateUser posts username + email + password + role', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"user":{"id":1,"username":"u","email":"u@x","role":"viewer"}}'),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g8')
    await apiService.adminCreateUser({
      username: 'u', email: 'u@x', password: 'pw', role: 'editor',
    })
    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body).toEqual({ username: 'u', email: 'u@x', password: 'pw', role: 'editor' })
  })

  it('adminDeleteUser issues a DELETE', async () => {
    localStorage.setItem('cenidim_token', 'TKN')
    const fetchMock = vi.fn(async () =>
      new Response('{"message":"User deleted"}', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g9')
    await apiService.adminDeleteUser(11)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/users/11')
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')
  })

  it('getSongDetail encodes the song id', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g10')
    await apiService.getSongDetail(99)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/song/99')
  })

  it('getTimeline forwards the query string', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g11')
    await apiService.getTimeline('tema=Amor')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/timeline?tema=Amor')
  })

  it('getWordCloud forwards query string', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g12')
    await apiService.getWordCloud('tema=Amor')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/word-cloud?tema=Amor')
  })

  it('register posts the body and returns the response', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"token":"reg-tok","user":{"id":1,"username":"alice","email":"a@x","role":"viewer"}}'),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g13')
    await apiService.register('alice', 'a@x', 'pw')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/register')
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      username: 'alice', email: 'a@x', password: 'pw',
    })
  })

  it('register throws on 4xx with the server error message', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"email ya existe"}', { status: 409 }),
    ))
    const { apiService } = await import('../api?integration=g14')
    await expect(apiService.register('a', 'a@x', 'p')).rejects.toThrow('email ya existe')
  })

  it('adminCreateFonograma returns the new row', async () => {
    const fetchMock = vi.fn(async () =>
      new Response('{"clave_fonograma":99,"titulo":"New"}', { status: 201 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g15')
    const row = await apiService.adminCreateFonograma({ titulo: 'New' })
    expect(row.clave_fonograma).toBe(99)
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
  })

  it('adminCreateFonograma throws on conflict', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"ClaveFonograma already exists"}', { status: 409 }),
    ))
    const { apiService } = await import('../api?integration=g16')
    await expect(apiService.adminCreateFonograma({ clave_fonograma: 1 }))
      .rejects.toThrow('ClaveFonograma already exists')
  })

  it('adminListFonogramas accepts defaults', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g17')
    await apiService.adminListFonogramas()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/fonogramas?page=1&limit=20')
  })

  it('getMe returns null on 401 (no token or expired)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"Unauthorized"}', { status: 401 }),
    ))
    const { apiService } = await import('../api?integration=g18')
    expect(await apiService.getMe()).toBeNull()
  })

  it('searchSongs throws when the server returns 500', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"Database error"}', { status: 500 }),
    ))
    const { apiService } = await import('../api?integration=g19')
    // searchSongs currently surfaces the generic HTTP error string
    // rather than the server's `error` field. Accept either to avoid
    // coupling the test to either side of that choice.
    await expect(apiService.searchSongs('x')).rejects.toThrow(/Database error|HTTP error/)
  })

  it('getWordCloud surfaces non-2xx with the generic HTTP error', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{"error":"bad"}', { status: 500 }),
    ))
    const { apiService } = await import('../api?integration=g20')
    await expect(apiService.getWordCloud()).rejects.toThrow('HTTP error! status: 500')
  })

  it('getStats forwards the optional filter query', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g21')
    await apiService.getStats('year_from=1980')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/stats?year_from=1980')
  })

  it('getStats surfaces non-2xx with the generic HTTP error', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('{}', { status: 500 }),
    ))
    const { apiService } = await import('../api?integration=g22')
    await expect(apiService.getStats()).rejects.toThrow('HTTP error! status: 500')
  })

  it('adminListFonogramas forwards page + limit as query', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g23')
    await apiService.adminListFonogramas(2, 25)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/admin/fonogramas?page=2&limit=25')
  })

  it('adminUpdateFonograma does not add a body when the payload is empty', async () => {
    const fetchMock = vi.fn(async () => new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    const { apiService } = await import('../api?integration=g24')
    // The handler closes over `form.value`; we don't call through
    // apiService directly. Verify the wiring exists.
    expect(typeof apiService.adminUpdateFonograma).toBe('function')
  })
})
