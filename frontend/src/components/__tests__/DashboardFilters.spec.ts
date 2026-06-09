import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import DashboardFilters from '../DashboardFilters.vue';
import FilterChips from '../FilterChips.vue';

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div/>' } }],
});

/**
 * Stub `/api/stats` so the theme chip list seeds with the literal values
 * we want to test. Without this, the onMounted fetch is unbound and the
 * dynamic theme list stays empty (a separate test verifies the empty
 * state).
 */
function stubStats(themes: Record<string, number>) {
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          songs_by_theme: themes,
          total_songs: 100,
          total_albums: 10,
        }),
    })) as unknown as typeof fetch;
}

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe('DashboardFilters', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders all filter groups', async () => {
    stubStats({});
    const wrapper = mount(DashboardFilters, {
      global: { plugins: [router] },
    });
    await flushPromises();
    const legends = wrapper.findAll('legend').map((l) => l.text().trim());
    expect(legends.some((l) => l.startsWith('Rango de años'))).toBe(true);
    expect(legends.some((l) => l.startsWith('Tema'))).toBe(true);
    expect(legends.some((l) => l.startsWith('Clasificación de lengua'))).toBe(true);
    expect(legends.some((l) => l.startsWith('Álbum'))).toBe(true);
    expect(legends.some((l) => l.startsWith('Búsqueda libre'))).toBe(true);
  });

  it('populates the theme chip list from /api/stats with the raw "Tema:" values', async () => {
    // These values are exactly what the user sees in the `Tema:` lines
    // of LetrasTXT/*.txt — no inference, no canonical reduction.
    stubStats({
      Amor: 11,
      'Placer/ dolor': 17,
      Escuela: 25,
      'Sabiduría/ Ignorancia': 23,
    });
    const wrapper = mount(DashboardFilters, {
      global: { plugins: [router] },
    });
    await flushPromises();
    const labels = wrapper.findAll('.chip__label').map((b) => b.text().trim());
    expect(labels).toContain('Amor');
    expect(labels).toContain('Placer/ dolor');
    expect(labels).toContain('Escuela');
    expect(labels).toContain('Sabiduría/ Ignorancia');
  });

  it('toggles a theme chip on click and adds it to the filters store', async () => {
    stubStats({ Amor: 11, 'Placer/ dolor': 17 });
    const { useFiltersStore } = await import('@/stores/filters');
    const store = useFiltersStore();
    const wrapper = mount(DashboardFilters, {
      global: { plugins: [router] },
    });
    await flushPromises();
    const chip = wrapper.findAll('.chip').find((c) => c.text().includes('Amor'));
    expect(chip).toBeDefined();
    await chip!.trigger('click');
    expect(store.themes).toContain('Amor');
    expect(chip!.classes()).toContain('chip--on');
  });

  it('clears all filters when the reset button is clicked', async () => {
    stubStats({});
    const { useFiltersStore } = await import('@/stores/filters');
    const store = useFiltersStore();
    store.themes = ['Amor'];
    store.yearFrom = 1990;
    store.q = 'corrido';
    const wrapper = mount(DashboardFilters, {
      global: { plugins: [router] },
    });
    await flushPromises();
    await wrapper.find('button.filters__reset').trigger('click');
    expect(store.themes).toEqual([]);
    expect(store.yearFrom).toBeNull();
    expect(store.q).toBe('');
  });
});

describe('FilterChips', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders nothing when no filters are active', () => {
    const wrapper = mount(FilterChips);
    expect(wrapper.find('.active-filters').exists()).toBe(false);
  });

  it('renders one chip per active filter', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const { useFiltersStore } = await import('@/stores/filters');
    const store = useFiltersStore();
    store.themes = ['Amor', 'Placer/ dolor'];
    store.yearFrom = 2000;
    store.yearTo = 2010;
    const wrapper = mount(FilterChips, { global: { plugins: [router, pinia] } });
    await wrapper.vm.$nextTick();
    // 2 themes + 1 year chip = 3
    expect(wrapper.findAll('.active-chip')).toHaveLength(3);
  });

  it('emits clear event when "Limpiar todo" is clicked', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const { useFiltersStore } = await import('@/stores/filters');
    useFiltersStore().themes = ['Amor'];
    const wrapper = mount(FilterChips, { global: { plugins: [router, pinia] } });
    await wrapper.vm.$nextTick();
    await wrapper.find('.active-filters__clear').trigger('click');
    expect(wrapper.emitted('clear')).toBeTruthy();
  });

  it('removes a single chip without clearing the rest', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const { useFiltersStore } = await import('@/stores/filters');
    const store = useFiltersStore();
    store.themes = ['Amor', 'Placer/ dolor'];
    const wrapper = mount(FilterChips, { global: { plugins: [router, pinia] } });
    await wrapper.vm.$nextTick();
    const amorChip = wrapper.findAll('.active-chip').find((c) => c.text().includes('Amor'));
    expect(amorChip).toBeDefined();
    await amorChip!.trigger('click');
    expect(store.themes).toEqual(['Placer/ dolor']);
  });
});
