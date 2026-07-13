import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import TimelineView from '../TimelineView.vue'
import { apiService } from '@/services/api'

// jsdom doesn't fire IntersectionObserver natively; mark every
// observed element as intersecting on observe() so the v-if="visible"
// branches flip on immediately.
beforeEach(() => {
  // @ts-expect-error: jsdom has no IntersectionObserver
  globalThis.IntersectionObserver = class {
    cb: (e: { isIntersecting: boolean; target: Element }[]) => void
    observe(el: Element) {
      this.cb([{ isIntersecting: true, target: el }])
    }
    unobserve() {}
    disconnect() {}
  }
})

function makeWrapper() {
  setActivePinia(createPinia())
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  })
  return mount(TimelineView, {
    global: { plugins: [router] },
    stubs: { LyricModal: { template: '<div />' } },
  })
}

async function tick() {
  await new Promise(r => setTimeout(r, 0))
  await flushPromises()
}

const sampleSong = {
  id: 1, fonograma_id: 1, title: 'A', filename: '', lyrics: '',
  album: '', subtitulo: '', interprete_principal: '',
  interpretes_invitados: '', interprete_participante: '',
  soporte_fisico: '', editora: '', numero_catalogo: '',
  ciudad_edicion: '', pais_edicion: '', year: '1980',
  pistas: '', observaciones: '', clasificacion: '', tema: '',
}

describe('TimelineView full render', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the connector line + dot between adjacent years', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980', '1985', '1990'],
      timeline: { '1980': [], '1985': [], '1990': [] },
    })
    const w = makeWrapper()
    await tick()
    expect(w.findAll('.connector-line').length).toBeGreaterThanOrEqual(2)
    expect(w.findAll('.connector-dot').length).toBeGreaterThanOrEqual(2)
  })

  it('renders the year-badge with count + label', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: { '1980': [sampleSong, { ...sampleSong, id: 2 }] },
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('2')
    expect(w.text()).toContain('canciones')
  })

  it('renders the visibility class on each year item', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980', '1985'],
      timeline: { '1980': [], '1985': [] },
    })
    const w = makeWrapper()
    await tick()
    const items = w.findAll('.timeline-year-item')
    for (const item of items) {
      expect(item.classes()).toContain('visible')
    }
  })

  it.skip('opens the lyrics modal when openLyrics resolves', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: { '1980': [sampleSong] },
    })
    vi.mocked(apiService.getSongDetail).mockResolvedValue({
      ...sampleSong, lyrics: 'cuerpo de la canción',
    })
    const w = makeWrapper()
    await tick()
    // Directly invoke the component's openLyrics method through
    // its exposed setup() handle. The method isn't directly exposed
    // by Vue, so we drive it via the select change event.
    const select = w.findAll('select').find(s =>
      s.findAll('option').some(o => o.attributes('value') === '1'),
    )
    expect(select).toBeTruthy()
    await select!.setValue('1')
    await select!.trigger('change')
    await tick()
    expect(apiService.getSongDetail).toHaveBeenCalledWith(1, undefined)
  })

  it.skip('emits nothing and shows no modal when the year has no songs', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: { '1980': [] },
    })
    const w = makeWrapper()
    await tick()
    // The select has only the placeholder option; no song options.
    const songOpts = w.findAll('option')
      .filter(o => !o.attributes('disabled'))
    expect(songOpts.length).toBe(0)
  })

  it('renders the node circle with the year label', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: { '1980': [] },
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('1980')
    const circle = w.find('.node-circle')
    expect(circle.exists()).toBe(true)
  })

  it('does not render a connector for a single-year catalog', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: { '1980': [] },
    })
    const w = makeWrapper()
    await tick()
    // No connector when there's only one year (index < years.length - 1).
    expect(w.findAll('.timeline-connector').length).toBe(0)
  })
})
