import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useFiltersStore } from '../filters';

describe('useFiltersStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('starts empty', () => {
    const s = useFiltersStore();
    expect(s.isEmpty).toBe(true);
    expect(s.active).toHaveLength(0);
    expect(s.queryString).toBe('');
  });

  it('applyFromQuery populates state from URL params', () => {
    const s = useFiltersStore();
    s.applyFromQuery({
      theme: 'AMOR,NAVIDAD',
      year_from: '1990',
      year_to: '2010',
      clasificacion: 'ESPAÑOL_ESTANDAR',
      album: 'Album Foo',
      q: 'corazón',
    });
    expect(s.themes).toEqual(['AMOR', 'NAVIDAD']);
    expect(s.yearFrom).toBe(1990);
    expect(s.yearTo).toBe(2010);
    expect(s.clasificaciones).toEqual(['ESPAÑOL_ESTANDAR']);
    expect(s.album).toBe('Album Foo');
    expect(s.q).toBe('corazón');
  });

  it('applyFromQuery drops invalid year_from > year_to', () => {
    const s = useFiltersStore();
    s.applyFromQuery({ year_from: '2020', year_to: '1990' });
    expect(s.yearFrom).toBeNull();
    expect(s.yearTo).toBeNull();
  });

  it('applyFromQuery drops invalid integer values', () => {
    const s = useFiltersStore();
    s.applyFromQuery({ year_from: 'not-a-number' });
    expect(s.yearFrom).toBeNull();
  });

  it('toQuery round-trips through applyFromQuery', () => {
    const s = useFiltersStore();
    s.themes = ['AMOR'];
    s.yearFrom = 2000;
    s.yearTo = 2010;
    s.clasificaciones = ['LENGUA_INDIGENA'];
    s.album = 'X';
    s.q = 'foo';
    const q = s.toQuery();
    // The toQuery return type is LocationQueryRaw; cast to LocationQuery for the round-trip.
    const s2 = useFiltersStore();
    s2.applyFromQuery(q as unknown as Record<string, string>);
    expect(s2.themes).toEqual(['AMOR']);
    expect(s2.yearFrom).toBe(2000);
    expect(s2.yearTo).toBe(2010);
    expect(s2.clasificaciones).toEqual(['LENGUA_INDIGENA']);
    expect(s2.album).toBe('X');
    expect(s2.q).toBe('foo');
  });

  it('clear resets all filters', () => {
    const s = useFiltersStore();
    s.themes = ['AMOR'];
    s.yearFrom = 2000;
    s.q = 'foo';
    s.clear();
    expect(s.isEmpty).toBe(true);
  });

  it('active exposes one chip per filter with onRemove handlers', () => {
    const s = useFiltersStore();
    s.themes = ['AMOR', 'NAVIDAD'];
    s.yearFrom = 1990;
    s.yearTo = 2010;
    s.q = 'corazón';
    expect(s.active.map((c) => c.key)).toEqual(['theme:AMOR', 'theme:NAVIDAD', 'year', 'q']);
    s.active[0].onRemove();
    expect(s.themes).toEqual(['NAVIDAD']);
  });

  it('setQ debounces updates', () => {
    vi.useFakeTimers();
    const s = useFiltersStore();
    s.setQ('first');
    s.setQ('second');
    s.setQ('third');
    expect(s.q).toBe('');
    vi.runAllTimers();
    expect(s.q).toBe('third');
    vi.useRealTimers();
  });

  it('setYearRange debounces updates', () => {
    vi.useFakeTimers();
    const s = useFiltersStore();
    s.setYearRange(1990, 2010);
    s.setYearRange(2000, 2050);
    expect(s.yearFrom).toBeNull();
    vi.runAllTimers();
    expect(s.yearFrom).toBe(2000);
    expect(s.yearTo).toBe(2050);
    vi.useRealTimers();
  });
});
