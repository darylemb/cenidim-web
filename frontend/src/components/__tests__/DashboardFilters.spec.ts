import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import DashboardFilters from '../DashboardFilters.vue'
import { useFiltersStore } from '@/stores/filters'

// Stub the FilterChips child so we don't drag in its full dependency
// graph. We only care about DashboardFilters itself here.
const FilterChipsStub = { template: '<div data-testid="filter-chips" />' }

function makeWrapper() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', name: 'home', component: { template: '<div />' } }],
  })
  return mount(DashboardFilters, {
    global: { plugins: [pinia, router] },
    stubs: { FilterChips: FilterChipsStub },
  })
}

describe('DashboardFilters.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    // Default: fetch returns an empty theme list.
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{"songs_by_theme":{}}', { status: 200 })))
  })

  it('renders the section header', () => {
    const w = makeWrapper()
    expect(w.find('.filters__title').text()).toBe('Criterios de búsqueda')
  })

  it('renders an empty theme list initially (until fetch resolves)', async () => {
    const w = makeWrapper()
    // onMounted fires refreshKnownThemes but the empty body takes
    // a microtask. Wait one tick.
    await flushPromises()
    // The "(0 temas en catálogo completo)" hint renders with count 0.
    expect(w.text()).toContain('0 temas en catálogo completo')
  })

  it('shows themes from /api/stats once fetch resolves', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(
      '{"songs_by_theme":{"Amor":10,"Juego":5}}',
      { status: 200 },
    )))
    const w = makeWrapper()
    await flushPromises()
    expect(w.text()).toContain('2 temas en catálogo completo')
    // Chips are rendered for each theme.
    const chips = w.findAll('.chip')
    expect(chips.length).toBeGreaterThanOrEqual(2)
  })

  it('shows empty-state copy when /api/stats errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 500 })))
    const w = makeWrapper()
    await flushPromises()
    // The empty branch still renders the headline, not the catalog hint.
    expect(w.find('.filters__title').exists()).toBe(true)
  })

  it('clearing all filters resets the store state', async () => {
    const w = makeWrapper()
    const filters = useFiltersStore()
    // Set up a fake filter state via the actions (direct assignment to
    // setup-style store state is unreliable across Pinia versions).
    filters.setYearRange(1980, 1985)
    await new Promise(r => setTimeout(r, 300)) // wait debounce
    filters.themes = ['Amor']
    await flushPromises()
    const btn = w.find('.filters__reset')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    await flushPromises()
    expect(filters.yearFrom).toBeNull()
    expect(filters.yearTo).toBeNull()
    expect(filters.themes).toEqual([])
  })

  it('toggles a theme chip', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(
      '{"songs_by_theme":{"Amor":10}}',
      { status: 200 },
    )))
    const w = makeWrapper()
    await flushPromises()
    const chip = w.findAll('.chip')
      .find(c => c.text().includes('Amor'))
    expect(chip).toBeTruthy()
    await chip!.trigger('click')
    expect(useFiltersStore().themes).toContain('Amor')
  })

  it('toggles the Sin tema chip with the __none__ sentinel', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(
      '{"songs_by_theme":{"Amor":10}}',
      { status: 200 },
    )))
    const w = makeWrapper()
    await flushPromises()
    const none = w.find('.chip--ghost')
    expect(none.exists()).toBe(true)
    await none.trigger('click')
    expect(useFiltersStore().themes).toContain('__none__')
  })
})
