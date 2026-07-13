import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import TimelineView from '../TimelineView.vue'
import { apiService } from '@/services/api'

// jsdom doesn't trigger IntersectionObserver natively; stub it on
// the window so the timeline's year-items become visible and the
// summary + select elements render.
beforeEach(() => {
  const ioInstances: { observe: ReturnType<typeof vi.fn>; disconnect: ReturnType<typeof vi.fn> }[] = []
  // @ts-expect-error: monkey-patching for tests
  globalThis.IntersectionObserver = class {
    cb: (entries: { isIntersecting: boolean; target: Element }[]) => void
    constructor(cb: (entries: { isIntersecting: boolean; target: Element }[]) => void) {
      this.cb = cb
      ioInstances.push(this)
    }
    observe(el: Element) {
      // Mark every element as intersecting immediately so the
      // v-if="visible" branches flip on.
      this.cb([{ isIntersecting: true, target: el }])
    }
    unobserve() {}
    disconnect() {}
  }
  // store reference so a test can trigger a re-fire if needed
  ;(globalThis as { __ioInstances?: unknown[] }).__ioInstances = ioInstances
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

const sampleYear = '1980'
const sampleSong = {
  id: 1, fonograma_id: 1, title: 'A', filename: '', lyrics: '',
  album: '', subtitulo: '', interprete_principal: '',
  interpretes_invitados: '', interprete_participante: '',
  soporte_fisico: '', editora: '', numero_catalogo: '',
  ciudad_edicion: '', pais_edicion: '', year: sampleYear,
  pistas: '', observaciones: '', clasificacion: '', tema: '',
}

describe('TimelineView', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the intro', () => {
    const w = makeWrapper()
    expect(w.text()).toContain('Cronología Musical')
  })

  it('shows no song options when no years are returned', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({ years: [], timeline: {} })
    const w = makeWrapper()
    await tick()
    // No years → no per-year selects → no options at all.
    expect(w.findAll('option').length).toBe(0)
  })

  it('renders year selects with song options when years have songs', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: [sampleYear],
      timeline: { [sampleYear]: [sampleSong] },
    })
    const w = makeWrapper()
    await tick()
    const songOpts = w.findAll('option')
      .filter(o => !o.attributes('disabled'))
      .filter(o => o.text() !== 'Seleccionar pista')
    expect(songOpts.length).toBeGreaterThanOrEqual(1)
    expect(songOpts.some(o => o.text() === 'A')).toBe(true)
  })

  it('renders the summary block with year count + tracks total', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: [sampleYear, '1985'],
      timeline: {
        [sampleYear]: [sampleSong, { ...sampleSong, id: 2 }],
        '1985': [],
      },
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('2')
  })

  it.skip('selecting a song calls getSongDetail (deferred — covered in integration)', () => {})

  it('renders the year header for each year returned', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980', '1985', '1990'],
      timeline: {
        '1980': [], '1985': [], '1990': [],
      },
    })
    const w = makeWrapper()
    await tick()
    expect(w.text()).toContain('1980')
    expect(w.text()).toContain('1985')
    expect(w.text()).toContain('1990')
  })
})
