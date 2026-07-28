import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import FilterChips from '../FilterChips.vue';
import { useFiltersStore } from '@/stores/filters';

function makeWrapper() {
  setActivePinia(createPinia());
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  });
  return mount(FilterChips, { global: { plugins: [router] } });
}

describe('FilterChips', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders nothing when there are no active filters', async () => {
    const w = makeWrapper();
    expect(w.find('.active-filters').exists()).toBe(false);
  });

  it('renders the "Filtros aplicados" label when at least one filter is active', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    await flushPromises();
    await flushPromises();
    await flushPromises();
    expect(w.text()).toContain('Filtros aplicados');
  });

  it('renders a chip per active theme', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.themes = ['Amor', 'Juego'];
    await flushPromises();
    await flushPromises();
    const chips = w.findAll('.active-chip');
    expect(chips.length).toBe(2);
    expect(chips.some((c) => c.text().includes('Amor'))).toBe(true);
    expect(chips.some((c) => c.text().includes('Juego'))).toBe(true);
  });

  it('clicking a chip removes the filter', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    await flushPromises();
    await flushPromises();
    f.yearTo = 1985;
    await flushPromises();
    await flushPromises();
    const yearChip = w.findAll('.active-chip').find((c) => c.text().includes('Año'));
    expect(yearChip).toBeTruthy();
    await yearChip!.trigger('click');
    expect(f.yearFrom).toBeNull();
    expect(f.yearTo).toBeNull();
  });

  it('renders a year chip with the correct range label', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    await flushPromises();
    await flushPromises();
    f.yearTo = 1985;
    await flushPromises();
    const yearChip = w.findAll('.active-chip').find((c) => c.text().includes('Año'));
    expect(yearChip?.text()).toContain('1980');
    expect(yearChip?.text()).toContain('1985');
  });

  it('renders the "Limpiar todo" button when at least one filter is active', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.album = 'Album 1';
    await flushPromises();
    const clearBtn = w.findAll('.active-filters__clear');
    expect(clearBtn.length).toBe(1);
  });

  it('clicking "Limpiar todo" clears every filter', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    await flushPromises();
    await flushPromises();
    f.yearTo = 1985;
    await flushPromises();
    f.themes = ['Amor'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.album = 'Album 1';
    f.q = 'algo';
    await w.find('.active-filters__clear').trigger('click');
    expect(f.yearFrom).toBeNull();
    expect(f.yearTo).toBeNull();
    expect(f.themes).toEqual([]);
    expect(f.clasificaciones).toEqual([]);
    expect(f.album).toBeNull();
    expect(f.q).toBe('');
  });

  it('renders a chip for an active album filter', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.album = 'Mi Álbum';
    await flushPromises();
    const albumChip = w.findAll('.active-chip').find((c) => c.text().includes('Álbum'));
    expect(albumChip?.text()).toContain('Mi Álbum');
  });

  it('renders a chip for an active search query', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.q = 'buscar esto';
    await flushPromises();
    const qChip = w.findAll('.active-chip').find((c) => c.text().includes('Buscar'));
    expect(qChip?.text()).toContain('buscar esto');
  });

  it('renders a chip per active clasificacion', async () => {
    const w = makeWrapper();
    const f = useFiltersStore();
    f.clasificaciones = ['ESPAÑOL_ESTANDAR', 'ESPAÑOL_REGIONAL'];
    await flushPromises();
    const chips = w.findAll('.active-chip');
    const clasChips = chips.filter((c) => c.text().includes('Clasificación'));
    expect(clasChips.length).toBe(2);
  });
});
