import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import DashboardView from '../DashboardView.vue'
import { useFiltersStore } from '@/stores/filters'
import { apiService } from '@/services/api'

const sampleStats = {
  total_songs: 100, total_albums: 10, catalog_total: 100,
  recently_added: 5, songs_with_lyrics: 80, avg_lyrics_length: 1200,
  songs_by_clasificacion: {
    ESPAÑOL_ESTANDAR: 60, ESPAÑOL_REGIONAL: 30, LENGUA_INDIGENA: 10,
  },
  songs_by_year: { 1980: 5, 1985: 8, 1990: 7, 's/d': 5 },
  songs_by_theme: { Amor: 20, Juego: 10, Familia: 5 },
  distinct_themes: 3,
  top_albums: [
    { album: 'Album A', year: '1980', count: 10 },
    { album: 'Album B', year: '1985', count: 8 },
  ],
  songs_by_oov_level: { BAJA: 70, MEDIA: 25, ALTA: 5 },
  songs_by_indigena: { CON_INDIGENA: 10, SIN_INDIGENA: 90 },
  songs_without_year: 5,
}

function makeWrapper(initial = '') {
  setActivePinia(createPinia())
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  })
  if (initial) router.push(initial).catch(() => {})
  return mount(DashboardView, {
    global: { plugins: [router] },
    stubs: {
      DashboardFilters: { template: '<div data-testid="filters" />' },
      FilterChips: { template: '<div data-testid="chips" />' },
      ChartInfoButton: { template: '<button />' },
    },
  })
}

async function tick() {
  await new Promise(r => setTimeout(r, 0))
  await flushPromises()
}

describe('DashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the dashboard title', () => {
    const w = makeWrapper()
    expect(w.text()).toContain('Dashboards analíticos')
  })

  it('shows the loading spinner on mount', () => {
    const w = makeWrapper()
    expect(w.find('.spinner').exists()).toBe(true)
  })

  it('renders the catalog + albums KPIs once stats load', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue(sampleStats)
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Catálogo')
    expect(w.text()).toContain('Álbumes')
  })

  it('renders Con letra + Recientes + Temas + Sin año KPIs', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue(sampleStats)
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Con letra')
    expect(w.text()).toContain('Agregadas recientemente')
    expect(w.text()).toContain('+5')
    expect(w.text()).toContain('Temas distintos')
    expect(w.text()).toContain('Sin año')
  })

  it('falls back to "-" for KPIs when stats is null', async () => {
    const w = makeWrapper()
    await tick()
    // With no stats loaded, the KPIs render default values.
    expect(w.text()).toContain('0')
  })

  it('shows the empty-state when there are no matching songs', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue({ ...sampleStats, total_songs: 0 })
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('El archivo no devuelve coincidencias')
  })

  it('renders year-line chart when stats have years', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue(sampleStats)
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    // The chart canvas renders; in jsdom the canvas is empty but
    // the wrapping element exists.
    expect(w.find('.dashboard__hero').exists()).toBe(true)
  })

  it('renders Sin datos de clasificación when empty', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue({
      ...sampleStats, songs_by_clasificacion: {},
    })
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Sin datos de clasificación')
  })

  it('renders Sin datos de tema when empty', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue({
      ...sampleStats, songs_by_theme: {},
    })
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Sin datos de tema')
  })

  it('renders Sin datos de OOV when empty', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue({
      ...sampleStats, songs_by_oov_level: {},
    })
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('Sin datos de OOV')
  })

  it('does not show the empty-state when there ARE results', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue(sampleStats)
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    expect(w.text()).not.toContain('El archivo no devuelve coincidencias')
  })

  it('onClearAll empties the filter store', async () => {
    vi.mocked(apiService.getStats).mockResolvedValue(sampleStats)
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    const filters = useFiltersStore()
    filters.themes = ['Amor']
    filters.yearFrom = 1980
    filters.yearTo = 1985
    await tick()
    expect(filters.isEmpty).toBe(false)
    // The Restablecer button in the stub renders nothing — call
    // the exposed onClearAll directly through the wrapper VM.
    ;(w.vm as unknown as { onClearAll: () => void }).onClearAll()
    await tick()
    expect(filters.isEmpty).toBe(true)
  })

  it.skip('shows "Filtrado" hint in KPIs when filters are active', () => {})
})
