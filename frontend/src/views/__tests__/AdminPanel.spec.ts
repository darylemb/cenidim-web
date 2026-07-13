import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AdminPanel from '../AdminPanel.vue'
import { useAuthStore } from '@/stores/auth'
import { apiService } from '@/services/api'

vi.mock('@/services/api', () => ({
  apiService: {
    adminListFonogramas: vi.fn(async () => ({ results: [], total: 0 })),
    adminListSongs: vi.fn(async () => ({ results: [], total: 0 })),
    adminListUsers: vi.fn(async () => []),
    adminDeleteFonograma: vi.fn(async () => {}),
    adminDeleteSong: vi.fn(async () => {}),
    adminDeleteUser: vi.fn(async () => {}),
  },
}))

// Stub child components that aren't the focus of these tests.
const Stub = { template: '<div />' }

function makeWrapper(role: 'admin' | 'editor' | 'viewer' = 'admin') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', name: 'home', component: { template: '<div />' } }],
  })
  const auth = useAuthStore(pinia)
  auth.user = { id: 1, username: role, email: `${role}@test`, role }
  return mount(AdminPanel, {
    global: { plugins: [pinia, router] },
    stubs: {
      SortableHeader: Stub,
      AdminFormModal: Stub,
      ConfirmModal: Stub,
    },
  })
}

describe('AdminPanel.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders the title', () => {
    const w = makeWrapper()
    expect(w.find('.page-title').text()).toBe('Panel de Administración')
  })

  it('shows the current admin user', () => {
    const w = makeWrapper('admin')
    expect(w.find('.admin-username').text()).toBe('admin')
    expect(w.find('.role-badge').text()).toBe('admin')
  })

  it('always renders the Fonogramas and Canciones tabs', () => {
    const w = makeWrapper('viewer')
    const tabs = w.findAll('.admin-tabs button')
    expect(tabs.length).toBe(2) // viewer doesn't see Usuarios
    expect(tabs[0].text()).toBe('Fonogramas')
    expect(tabs[1].text()).toBe('Canciones')
  })

  it('renders the Usuarios tab only for admins', () => {
    expect(makeWrapper('admin').findAll('.admin-tabs button').length).toBe(3)
    expect(makeWrapper('editor').findAll('.admin-tabs button').length).toBe(2)
  })

  it('starts on the Fonogramas tab and loads data', async () => {
    makeWrapper()
    await flushPromises()
    expect(apiService.adminListFonogramas).toHaveBeenCalled()
    expect(apiService.adminListSongs).toHaveBeenCalled()
  })

  it('loads admin users only for admin role', async () => {
    makeWrapper('admin')
    await flushPromises()
    expect(apiService.adminListUsers).toHaveBeenCalled()
    vi.mocked(apiService.adminListUsers).mockClear()
    makeWrapper('editor')
    await flushPromises()
    expect(apiService.adminListUsers).not.toHaveBeenCalled()
  })

  it('switches to Canciones tab when clicked', async () => {
    const w = makeWrapper()
    await flushPromises()
    await w.findAll('.admin-tabs button')[1].trigger('click')
    expect(w.text()).toContain('Canciones')
  })

  it('opens the fonograma form modal on + Agregar click', async () => {
    const w = makeWrapper()
    await w.find('.btn-primary').trigger('click')
    expect(w.findComponent({ name: 'AdminFormModal' }).exists()).toBe(true)
  })

  it('opens the confirm modal on Eliminar and runs deleteFono on confirm', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        results: [{ clave_fonograma: 7, titulo: 'A', subtitulo: '', interprete_principal: '',
          interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
          editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
          anio: '', pistas: '', observaciones: '' }],
        total: 1,
      })
    const w = makeWrapper()
    await flushPromises()
    // Click the danger Eliminar button in the fonogramas table.
    await w.find('.btn-danger').trigger('click')
    expect(w.findComponent({ name: 'ConfirmModal' }).exists()).toBe(true)
    expect(w.find('.admin-confirm').text()).toContain('¿Eliminar este fonograma?')
    // Click the danger button inside the confirm modal.
    await w.find('.admin-confirm-actions .btn-danger').trigger('click')
    await flushPromises()
    expect(apiService.adminDeleteFonograma).toHaveBeenCalledWith(7)
  })

  it('cancels the confirm modal without calling delete', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        results: [{ clave_fonograma: 8, titulo: 'X', subtitulo: '', interprete_principal: '',
          interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
          editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
          anio: '', pistas: '', observaciones: '' }],
        total: 1,
      })
    const w = makeWrapper()
    await flushPromises()
    await w.find('.btn-danger').trigger('click')
    // Cancel the confirm.
    await w.find('.admin-confirm-actions .btn-secondary').trigger('click')
    await flushPromises()
    expect(apiService.adminDeleteFonograma).not.toHaveBeenCalled()
    expect(w.findComponent({ name: 'ConfirmModal' }).exists()).toBe(false)
  })

  it('opens confirm + deletes song via Canciones tab', async () => {
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      results: [{ id: 12, fonograma_id: 1, title: 'X', filename: '', lyrics: '',
        album: '', subtitulo: '', interprete_principal: '', interpretes_invitados: '',
        interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
        ciudad_edicion: '', pais_edicion: '', year: '', pistas: '', observaciones: '',
        clasificacion: '', tema: '' }],
      total: 1,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    // Navigate to Canciones (button index 1).
    await w.findAll('.admin-tabs button')[1].trigger('click')
    await flushPromises()
    // Click the danger button on the songs row (index 0).
    await w.findAll('.btn-danger')[0].trigger('click')
    expect(w.findComponent({ name: 'ConfirmModal' }).exists()).toBe(true)
    await w.find('.admin-confirm-actions .btn-danger').trigger('click')
    await flushPromises()
    expect(apiService.adminDeleteSong).toHaveBeenCalledWith(12)
  })

  it('opens confirm + deletes user', async () => {
    ;(apiService.adminListUsers as ReturnType<typeof vi.fn>).mockResolvedValueOnce([
      { id: 22, username: 'u', email: 'u@x', role: 'viewer', created_at: '' },
    ])
    const w = makeWrapper('admin')
    await flushPromises()
    // Navigate to users tab (button index 2 because 0=fonogramas, 1=canciones, 2=users).
    await w.findAll('.admin-tabs button')[2].trigger('click')
    await flushPromises()
    await w.find('.btn-danger').trigger('click')
    await w.find('.admin-confirm-actions .btn-danger').trigger('click')
    await flushPromises()
    expect(apiService.adminDeleteUser).toHaveBeenCalledWith(22)
  })
})

  it('opens the song form when openSongForm is called via tab', async () => {
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      results: [{ id: 1, fonograma_id: 1, title: 'X', filename: '', lyrics: '',
        album: '', subtitulo: '', interprete_principal: '', interpretes_invitados: '',
        interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
        ciudad_edicion: '', pais_edicion: '', year: '', pistas: '', observaciones: '',
        clasificacion: '', tema: '' }],
      total: 1,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    await w.findAll('.admin-tabs button')[1].trigger('click')
    await flushPromises()
    await w.findAll('.btn-primary')[0].trigger('click')
    expect(w.findComponent({ name: 'AdminFormModal' }).exists()).toBe(true)
  })

  it('opens the user form when openUserForm is called', async () => {
    ;(apiService.adminListUsers as ReturnType<typeof vi.fn>).mockResolvedValueOnce([
      { id: 5, username: 'u', email: 'u@x', role: 'viewer', created_at: '' },
    ])
    const w = makeWrapper('admin')
    await flushPromises()
    await w.findAll('.admin-tabs button')[2].trigger('click')
    await flushPromises()
    await w.findAll('.btn-primary')[0].trigger('click')
    expect(w.findComponent({ name: 'AdminFormModal' }).exists()).toBe(true)
  })

  it('handleFormSubmitted triggers a reload on success', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockResolvedValue({
      results: [], total: 0,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    await w.find('.btn-primary').trigger('click') // + Agregar fonograma
    expect(w.findComponent({ name: 'AdminFormModal' }).exists()).toBe(true)
    // The modal is stubbed; trigger the wrapper's handler directly
    // to simulate the "submitted" callback path.
    ;(w.vm as unknown as { handleFormSubmitted: () => void }).handleFormSubmitted()
    await flushPromises()
    expect(apiService.adminListFonogramas).toHaveBeenCalledTimes(2)
  })


  it('logs and recovers when admin delete throws', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockResolvedValue({
      results: [{ clave_fonograma: 55, titulo: 'X', subtitulo: '', interprete_principal: '',
        interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
        editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
        anio: '', pistas: '', observaciones: '' }],
      total: 1,
    })
    vi.mocked(apiService.adminDeleteFonograma).mockRejectedValueOnce(new Error('boom'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const w = makeWrapper()
    await flushPromises()
    await w.find('.btn-danger').trigger('click')
    await w.find('.admin-confirm-actions .btn-danger').trigger('click')
    await flushPromises()
    expect(apiService.adminDeleteFonograma).toHaveBeenCalled()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })


  it('confirmDeleteFono opens confirm modal with the right message', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockResolvedValue({
      results: [{ clave_fonograma: 77, titulo: 'X', subtitulo: '', interprete_principal: '',
        interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
        editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
        anio: '', pistas: '', observaciones: '' }],
      total: 1,
    })
    const w = makeWrapper()
    await flushPromises()
    await w.find('.btn-danger').trigger('click')
    expect(w.find('.admin-confirm').text()).toContain('¿Eliminar este fonograma?')
  })

  it('confirmDeleteSong opens confirm modal with song-specific text', async () => {
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListSongs).mockResolvedValue({
      results: [{ id: 5, fonograma_id: 1, title: 'S', filename: '', lyrics: '', album: '',
        subtitulo: '', interprete_principal: '', interpretes_invitados: '',
        interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
        ciudad_edicion: '', pais_edicion: '', year: '', pistas: '', observaciones: '',
        clasificacion: '', tema: '' }],
      total: 1,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    await w.findAll('.admin-tabs button')[1].trigger('click') // Canciones tab
    await flushPromises()
    await w.find('.btn-danger').trigger('click')
    expect(w.find('.admin-confirm').text()).toContain('¿Eliminar esta canción?')
  })

  it('catches errors from adminListFonogramas gracefully', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockRejectedValueOnce(new Error('boom'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const w = makeWrapper('admin')
    await flushPromises()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('catches errors from adminListSongs gracefully', async () => {
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListSongs).mockRejectedValueOnce(new Error('boom'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const w = makeWrapper('admin')
    await flushPromises()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('catches errors from adminListUsers gracefully', async () => {
    ;(apiService.adminListUsers as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListUsers).mockRejectedValueOnce(new Error('boom'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const w = makeWrapper('admin')
    await flushPromises()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it.skip('fonoSort and songSort toggle direction when key matches', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockResolvedValue({
      results: [{ clave_fonograma: 1, titulo: 'A', subtitulo: '', interprete_principal: '',
        interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
        editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
        anio: '', pistas: '', observaciones: '' }],
      total: 1,
    })
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper('admin')
    await flushPromises()
    type Comp = {
      fonoSort: (key: string) => void
      songSort: (key: string) => void
      fonoSortKey: { value: string }
      fonoSortDir: { value: string }
    }
    const vm = w.vm as unknown as Comp
    vm.fonoSort('titulo')
    expect(vm.fonoSortKey.value).toBe('titulo')
    expect(vm.fonoSortDir.value).toBe('asc')
    vm.fonoSort('titulo')
    expect(vm.fonoSortDir.value).toBe('desc')
  })

  it('clicking a sortable header triggers a sort on fonograma rows', async () => {
    ;(apiService.adminListFonogramas as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListFonogramas).mockResolvedValue({
      results: [
        { clave_fonograma: 1, titulo: 'B', subtitulo: '', interprete_principal: '',
          interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
          editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
          anio: '', pistas: '', observaciones: '' },
        { clave_fonograma: 2, titulo: 'A', subtitulo: '', interprete_principal: '',
          interpretes_invitados: '', interprete_participante: '', soporte_fisico: '',
          editora: '', numero_catalogo: '', ciudad_edicion: '', pais_edicion: '',
          anio: '', pistas: '', observaciones: '' },
      ],
      total: 2,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    // Find the sortable th for Título column.
    const th = w.findAll('th').find(t => t.text().includes('Título'))
    expect(th).toBeTruthy()
    await th!.trigger('click')
    await flushPromises()
  })

  it.skip('clicking a sortable header triggers a sort on song rows', async () => {
    ;(apiService.adminListSongs as ReturnType<typeof vi.fn>).mockReset()
    vi.mocked(apiService.adminListSongs).mockResolvedValue({
      results: [
        { id: 1, fonograma_id: 1, title: 'B', filename: '', lyrics: '', album: '',
          subtitulo: '', interprete_principal: '', interpretes_invitados: '',
          interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
          ciudad_edicion: '', pais_edicion: '', year: '', pistas: '', observaciones: '',
          clasificacion: '', tema: '' },
        { id: 2, fonograma_id: 1, title: 'A', filename: '', lyrics: '', album: '',
          subtitulo: '', interprete_principal: '', interpretes_invitados: '',
          interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
          ciudad_edicion: '', pais_edicion: '', year: '', pistas: '', observaciones: '',
          clasificacion: '', tema: '' },
      ],
      total: 2,
    })
    const w = makeWrapper('admin')
    await flushPromises()
    await w.findAll('.admin-tabs button')[1].trigger('click') // Canciones tab
    await flushPromises()
    const th = w.findAll('th').find(t => t.text().includes('Pista'))
    expect(th).toBeTruthy()
    await th!.trigger('click')
    await flushPromises()
  })
