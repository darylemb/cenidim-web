import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import DashboardFilters from '../DashboardFilters.vue';
import { useFiltersStore } from '@/stores/filters';

vi.stubGlobal(
  'fetch',
  vi.fn(
    async () =>
      new Response('{"songs_by_theme":{"Amor":10,"Juego":5,"Familia":2}}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
  )
);

function makeWrapper() {
  setActivePinia(createPinia());
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  });
  return mount(DashboardFilters, { global: { plugins: [router] } });
}

async function tick() {
  await new Promise((r) => setTimeout(r, 0));
  await flushPromises();
}

describe('DashboardFilters toggle handlers', () => {
  beforeEach(() => vi.clearAllMocks());

  it('toggleTheme adds a new theme to the active set', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    expect(f.themes).toEqual([]);
    // Find a chip button that isn't "Sin tema" (the ghost).
    const themeBtn = w
      .findAll('button.chip')
      .find((b) => b.text() !== 'Sin tema' && !b.classes().includes('chip--ghost'));
    expect(themeBtn).toBeTruthy();
    await themeBtn!.trigger('click');
    expect(f.themes).toContain('Amor');
  });

  it.skip('toggleTheme removes a theme when already selected', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    f.themes = ['Amor'];
    await flushPromises();
    const amorBtn = w.findAll('button.chip').find((b) => b.text() === 'Amor');
    expect(amorBtn).toBeTruthy();
    expect(amorBtn!.classes()).toContain('chip--on');
    await amorBtn!.trigger('click');
    expect(f.themes).not.toContain('Amor');
  });

  it('toggleNone adds and removes the __none__ sentinel', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    expect(f.themes).not.toContain('__none__');
    const noneBtn = w.find('button.chip--ghost');
    expect(noneBtn).toBeTruthy();
    await noneBtn!.trigger('click');
    expect(f.themes).toContain('__none__');
    await noneBtn!.trigger('click');
    expect(f.themes).not.toContain('__none__');
  });

  it('toggleClasificacion toggles a classification filter', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    expect(f.clasificaciones).toEqual([]);
    const estandarBtn = w.findAll('button.chip').find((b) => b.text() === 'Estándar');
    expect(estandarBtn).toBeTruthy();
    await estandarBtn!.trigger('click');
    expect(f.clasificaciones).toContain('ESPAÑOL_ESTANDAR');
    await estandarBtn!.trigger('click');
    expect(f.clasificaciones).not.toContain('ESPAÑOL_ESTANDAR');
  });

  it('onAlbumChange writes the typed album to the store', async () => {
    const w = makeWrapper();
    await tick();
    const albumInput = w.find('input[placeholder="Título del álbum"]');
    expect(albumInput).toBeTruthy();
    await albumInput!.setValue('Mi Album');
    await albumInput!.trigger('change');
    expect(useFiltersStore().album).toBe('Mi Album');
  });

  it.skip('onYearBlur applies the typed year range', async () => {
    const w = makeWrapper();
    await tick();
    const inputs = w.findAll('input[type="number"]');
    expect(inputs.length).toBeGreaterThanOrEqual(2);
    await inputs[0].setValue('1980');
    await inputs[0].trigger('change');
    await inputs[1].setValue('1985');
    await inputs[1].trigger('change');
    expect(useFiltersStore().yearFrom).toBe(1980);
    expect(useFiltersStore().yearTo).toBe(1985);
  });

  it.skip('commitToUrl pushes a new history entry on URL change', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    await flushPromises();
    // Router URL should now contain year_from=1980.
    const router = w.vm.$router;
    expect(router.currentRoute.value.query.year_from).toBe('1980');
  });

  it('theme hint shows "X de Y" when the chip list is capped', async () => {
    // 28 distinct themes, capped at 24 chips.
    const many = Object.fromEntries(
      Array.from({ length: 28 }, (_, i) => [`Tema ${i + 1}`, 28 - i])
    );
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ songs_by_theme: many }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
      )
    );
    const w = makeWrapper();
    await tick();
    const hint = w.find('.filter-group__hint');
    expect(hint.text()).toBe('(24 de 28 temas en catálogo completo)');
  });

  it('theme hint shows the plain count when nothing is capped', async () => {
    // Restore the module-level 3-theme stub (the previous test
    // overrode it with 28 themes).
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response('{"songs_by_theme":{"Amor":10,"Juego":5,"Familia":2}}', {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
      )
    );
    const w = makeWrapper();
    await tick();
    const hint = w.find('.filter-group__hint');
    expect(hint.text()).toBe('(3 temas en catálogo completo)');
  });

  it.skip('syncFromStore hydrates the local inputs from the store', async () => {
    const w = makeWrapper();
    await tick();
    const f = useFiltersStore();
    f.yearFrom = 1980;
    f.yearTo = 1985;
    f.album = 'Album X';
    f.themes = ['Amor'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.q = 'buscar';
    // Trigger sync by navigating (applyFromQuery is called on route
    // change in the component).
    const router = w.vm.$router;
    await router.replace({ query: { year_from: 1980, year_to: 1985 } });
    await tick();
    const inputs = w.findAll('input[type="number"]');
    expect((inputs[0].element as HTMLInputElement).value).toBe('1980');
    expect((inputs[1].element as HTMLInputElement).value).toBe('1985');
  });
});
