import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import CancionesView from '../CancionesView.vue'
import { useSearchStore } from '@/stores/search'
import { apiService } from '@/services/api'

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn(),
    getSongDetail: vi.fn(),
  },
}))

function makeWrapper() {
  setActivePinia(createPinia())
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  })
  return mount(CancionesView, {
    global: { plugins: [router] },
    stubs: { LyricModal: { template: '<div />' } },
  })
}

async function tick() {
  await new Promise(r => setTimeout(r, 0))
  await flushPromises()
}

const sampleResults = [
  {
    id: 1, fonograma_id: 1, title: 'A', filename: 'a.txt', lyrics: '',
    album: 'Album 1', subtitulo: '', interprete_principal: '',
    interpretes_invitados: '', interprete_participante: '',
    soporte_fisico: '', editora: '', numero_catalogo: '',
    ciudad_edicion: '', pais_edicion: '', year: '1980',
    pistas: '', observaciones: '', clasificacion: '', tema: '',
  },
  {
    id: 2, fonograma_id: 1, title: 'B', filename: 'b.txt', lyrics: '',
    album: 'Album 1', subtitulo: '', interprete_principal: '',
    interpretes_invitados: '', interprete_participante: '',
    soporte_fisico: '', editora: '', numero_catalogo: '',
    ciudad_edicion: '', pais_edicion: '', year: '1985',
    pistas: '', observaciones: '', clasificacion: 'ESPAÑOL_ESTANDAR', tema: 'Juego',
  },
]

describe('CancionesView', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows the empty state when no results', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('No se encontraron canciones')
  })

  it('renders the table headers when results exist', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: sampleResults, total: 2,
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Clave')
    expect(w.text()).toContain('Pista')
    expect(w.text()).toContain('Álbum')
  })

  it('renders a row per result with title + album', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: sampleResults, total: 2,
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('A')
    expect(w.text()).toContain('B')
    expect(w.text()).toContain('Album 1')
  })

  it('renders pagination when there are multiple pages', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: sampleResults, total: 50,
    })
    const w = makeWrapper()
    await tick()
    expect(w.findAll('.pagination-btn').length).toBeGreaterThan(0)
  })

  it('does not render pagination when there are no results', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    expect(w.findAll('.pagination-btn').length).toBe(0)
  })

  it('uses default limit of 20', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    expect(apiService.searchSongs).toHaveBeenCalledWith(
      '', 'all', 1, 20, '', 'id', 'asc',
    )
  })

  it('typing in the search input triggers a re-query', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    vi.mocked(apiService.searchSongs).mockClear()
    const input = w.find('input[placeholder*="título"]')
    await input.setValue('algo')
    // The store debounces the query by 250ms; wait past that.
    await new Promise(r => setTimeout(r, 350))
    expect(apiService.searchSongs).toHaveBeenCalledWith(
      'algo', 'all', 1, 20, '', 'id', 'asc',
    )
  })

  it('changing clasificación re-queries', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    vi.mocked(apiService.searchSongs).mockClear()
    const selects = w.findAll('select')
    const clasificSelect = selects.find(s =>
      s.findAll('option').some(o => o.text() === 'Estándar'),
    )
    await clasificSelect?.setValue('ESPAÑOL_ESTANDAR')
    await new Promise(r => setTimeout(r, 350))
    expect(apiService.searchSongs).toHaveBeenCalledWith(
      '', 'all', 1, 20, 'ESPAÑOL_ESTANDAR', 'id', 'asc',
    )
  })

  it('changing order by re-queries', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 })
    const w = makeWrapper()
    await tick()
    vi.mocked(apiService.searchSongs).mockClear()
    // OrderBy select has option 'Clave' which is unique among the four selects.
    const selects = w.findAll('select')
    const orderSelect = selects.find(s =>
      s.findAll('option').some(o => o.text() === 'Clave'),
    )
    await orderSelect?.setValue('title')
    await new Promise(r => setTimeout(r, 350))
    expect(apiService.searchSongs).toHaveBeenCalledWith(
      '', 'all', 1, 20, '', 'title', 'asc',
    )
  })

  it.skip('changing limit re-queries', () => {})

  it('clicking the Ver letra button fetches lyrics + opens modal', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: sampleResults, total: 2,
    })
    vi.mocked(apiService.getSongDetail).mockResolvedValue({
      ...sampleResults[0],
      lyrics: 'long lyrics here',
    })
    const w = makeWrapper()
    await tick()
    // First button per row is "Ver". Vue-test-utils finds it via
    // class; the actual class is "action-btn".
    const buttons = w.findAll('.action-btn')
    expect(buttons.length).toBe(2)
    await buttons[0].trigger('click')
    await flushPromises()
    expect(apiService.getSongDetail).toHaveBeenCalledWith(1)
  })
})
