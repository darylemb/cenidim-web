import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import TimelineView from '../TimelineView.vue'
import { apiService } from '@/services/api'

beforeEach(() => {
  // @ts-expect-error: jsdom has no IntersectionObserver
  globalThis.IntersectionObserver = class {
    cb: (e: { isIntersecting: boolean; target: Element }[]) => void
    observe(el: Element) { this.cb([{ isIntersecting: true, target: el }]) }
    unobserve() {}
    disconnect() {}
  }
})

function makeWrapperWithRichData() {
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

describe('TimelineView full template coverage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the full timeline with multiple years + songs + connectors + badge', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1975', '1980', '1985'],
      timeline: {
        '1975': [
          { id: 1, fonograma_id: 1, title: 'Cancion A', filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1975', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
          { id: 2, fonograma_id: 1, title: 'Cancion B', filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1975', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
          { id: 3, fonograma_id: 1, title: 'Cancion C', filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1975', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
        ],
        '1980': [
          { id: 4, fonograma_id: 1, title: 'Cancion D', filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1980', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
        ],
        '1985': [],
      },
    })
    const w = makeWrapperWithRichData()
    await new Promise(r => setTimeout(r, 50))
    await new Promise(r => setTimeout(r, 0))

    // Verify the full timeline rendered with all branches:
    // - Three years → 2 connectors (between 0-1 and 1-2)
    expect(w.findAll('.timeline-connector').length).toBe(2)
    // - Year badge with count = 3 for 1975
    const years = w.findAll('.timeline-year-item')
    expect(years.length).toBe(3)
    // - First year badge count is 3 (1975 has 3 songs)
    expect(years[0].find('.badge-count').text()).toBe('3')
    // - All years are visible
    for (const y of years) {
      expect(y.classes()).toContain('visible')
    }
    // - Node circles show the year
    const nodeYears = w.findAll('.node-year').map(n => n.text())
    expect(nodeYears).toEqual(['1975', '1980', '1985'])
    // - Each year has the song selector
    expect(w.findAll('.timeline-select').length).toBe(3)
  })

  it('renders long song titles truncated to 32 chars + ellipsis', async () => {
    const longTitle = 'a'.repeat(50)
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: {
        '1980': [
          { id: 1, fonograma_id: 1, title: longTitle, filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1980', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
        ],
      },
    })
    const w = makeWrapperWithRichData()
    await new Promise(r => setTimeout(r, 50))
    await new Promise(r => setTimeout(r, 0))
    const songOption = w.findAll('.timeline-select option').find(o =>
      o.attributes('value') === '1',
    )
    expect(songOption).toBeTruthy()
    // title.length > 35 → truncated to 32 chars + '...'
    const text = songOption!.text()
    expect(text.length).toBe(35) // 32 chars + '...'
    expect(text.endsWith('...')).toBe(true)
  })

  it('handles selecting a song that exists in the timeline', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: ['1980'],
      timeline: {
        '1980': [
          { id: 1, fonograma_id: 1, title: 'A', filename: '', lyrics: '', album: '',
            subtitulo: '', interprete_principal: '', interpretes_invitados: '',
            interprete_participante: '', soporte_fisico: '', editora: '', numero_catalogo: '',
            ciudad_edicion: '', pais_edicion: '', year: '1980', pistas: '', observaciones: '',
            clasificacion: '', tema: '' },
        ],
      },
    })
    const w = makeWrapperWithRichData()
    await new Promise(r => setTimeout(r, 50))
    await new Promise(r => setTimeout(r, 0))
    const select = w.findAll('.timeline-select').find(s =>
      s.findAll('option').some(o => o.attributes('value') === '1'),
    )
    expect(select).toBeTruthy()
    // Trigger the change event.
    select!.element.value = '1'
    await select!.trigger('change')
    // The selectedSong in the component should now be set;
    // the LyricModal stub renders into the DOM.
    await new Promise(r => setTimeout(r, 0))
  })

  it('renders the intro paragraph + summary at the bottom', async () => {
    vi.mocked(apiService.getTimeline).mockResolvedValue({
      years: [],
      timeline: {},
    })
    const w = makeWrapperWithRichData()
    await new Promise(r => setTimeout(r, 50))
    await new Promise(r => setTimeout(r, 0))
    expect(w.text()).toContain('Cronología Musical')
    expect(w.text()).toContain('Explora el archivo')
  })
})
