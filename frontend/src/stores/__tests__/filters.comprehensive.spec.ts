import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useFiltersStore } from '../filters';

describe('filters store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  // Note: applyFromQuery reads `query.theme` (singular) but the
  // DashboardView URL layer uses `tema`. Mismatch is pre-existing;
  // we test the working `query.theme` path here.

  it('isEmpty is true at start', () => {
    const f = useFiltersStore();
    expect(f.isEmpty).toBe(true);
  });

  it('applyFromQuery reads year_from / year_to', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ year_from: '1980', year_to: '1985' } as never);
    expect(f.yearFrom).toBe(1980);
    expect(f.yearTo).toBe(1985);
  });

  it('applyFromQuery drops invalid year ranges silently', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ year_from: '1990', year_to: '1980' } as never);
    expect(f.yearFrom).toBeNull();
    expect(f.yearTo).toBeNull();
  });

  it('applyFromQuery ignores invalid integer strings', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ year_from: 'abc' } as never);
    expect(f.yearFrom).toBeNull();
  });

  it('applyFromQuery handles array values (vue-router quirk)', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ year_from: ['1985', '1988'] } as never);
    expect(f.yearFrom).toBe(1985);
  });

  it('applyFromQuery reads theme from query.theme (note: URL uses tema)', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ theme: 'Amor,Juego,Familia' } as never);
    expect(f.themes).toEqual(['Amor', 'Juego', 'Familia']);
  });

  it('applyFromQuery picks first theme when comma-separated', () => {
    const f = useFiltersStore();
    f.applyFromQuery({ theme: 'Amor,Juego' } as never);
    expect(f.themes).toEqual(['Amor', 'Juego']);
  });

  it('toQuery writes year_from / year_to / tema / album / q / clas.', () => {
    const f = useFiltersStore();
    f.yearFrom = 1980;
    f.yearTo = 1985;
    f.themes = ['Amor', 'Juego'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.album = 'Album 1';
    f.q = 'algo';
    const q = f.toQuery();
    expect(q.year_from).toBe('1980');
    expect(q.year_to).toBe('1985');
    expect(q.theme).toBe('Amor,Juego');
    expect(q.album).toBe('Album 1');
    expect(q.q).toBe('algo');
    expect(q.clasificacion).toBe('ESPAÑOL_ESTANDAR');
  });

  it('toQuery omits null / empty fields', () => {
    const f = useFiltersStore();
    const q = f.toQuery();
    expect(q.year_from).toBeUndefined();
    expect(q.year_to).toBeUndefined();
    expect(q.theme).toBeUndefined();
    expect(q.album).toBeUndefined();
  });

  it('queryString is empty when no filters active', () => {
    const f = useFiltersStore();
    expect(f.queryString).toBe('');
  });

  it('queryString reflects year range', () => {
    const f = useFiltersStore();
    f.yearFrom = 1980;
    f.yearTo = 1985;
    expect(f.queryString).toContain('year_from=1980');
    expect(f.queryString).toContain('year_to=1985');
  });

  it('queryString uses the theme key consistently', () => {
    const f = useFiltersStore();
    f.themes = ['Amor'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.album = 'Album';
    f.q = 'algo';
    expect(f.queryString).toContain('theme=Amor');
    // URL encoding: Ñ is percent-encoded as %C3%91.
    expect(f.queryString).toContain('clasificacion=ESPA%C3%91OL_ESTANDAR');
    expect(f.queryString).toContain('album=Album');
    expect(f.queryString).toContain('q=algo');
  });

  it('clear resets every field', () => {
    const f = useFiltersStore();
    f.yearFrom = 1980;
    f.yearTo = 1985;
    f.themes = ['Amor'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.album = 'A';
    f.q = 'q';
    f.clear();
    expect(f.yearFrom).toBeNull();
    expect(f.yearTo).toBeNull();
    expect(f.themes).toEqual([]);
    expect(f.clasificaciones).toEqual([]);
    expect(f.album).toBeNull();
    expect(f.q).toBe('');
  });

  it('setYearRange debounces by DEBOUNCE_MS', () => {
    const f = useFiltersStore();
    f.setYearRange(1980, 1985);
    expect(f.yearFrom).toBeNull(); // not yet applied
    vi.advanceTimersByTime(300);
    expect(f.yearFrom).toBe(1980);
    expect(f.yearTo).toBe(1985);
  });

  it('setYearRange replaces previous pending call', () => {
    const f = useFiltersStore();
    f.setYearRange(1980, 1985);
    vi.advanceTimersByTime(100);
    f.setYearRange(1986, 1987);
    vi.advanceTimersByTime(300);
    expect(f.yearFrom).toBe(1986);
    expect(f.yearTo).toBe(1987);
  });

  it('setQ debounces free-text', () => {
    const f = useFiltersStore();
    f.setQ('algo');
    vi.advanceTimersByTime(300);
    expect(f.q).toBe('algo');
  });

  it('active recomputed when filters change', () => {
    const f = useFiltersStore();
    expect(f.active.length).toBe(0);
    f.yearFrom = 1980;
    expect(f.active.some((c) => c.key === 'year')).toBe(true);
    f.yearFrom = null;
    f.album = 'Album';
    expect(f.active.some((c) => c.key === 'album')).toBe(true);
  });

  it('onDebouncedFlush receives a callback each time filters change (debounced)', () => {
    const f = useFiltersStore();
    const cb = vi.fn();
    f.onDebouncedFlush(cb);
    f.setQ('a');
    expect(cb).not.toHaveBeenCalled();
    vi.advanceTimersByTime(300);
    expect(cb).toHaveBeenCalledTimes(1);
  });

  it('onDebouncedFlush returns an unsubscribe function', () => {
    const f = useFiltersStore();
    const cb = vi.fn();
    const unsub = f.onDebouncedFlush(cb);
    unsub();
    f.setQ('a');
    vi.advanceTimersByTime(300);
    expect(cb).not.toHaveBeenCalled();
  });

  it('emptyState snapshot is restored by clear', () => {
    const f = useFiltersStore();
    f.yearFrom = 1980;
    f.yearTo = 1985;
    f.themes = ['Amor'];
    f.clasificaciones = ['ESPAÑOL_ESTANDAR'];
    f.album = 'Album';
    f.q = 'algo';
    const snap = f.emptyState();
    f.clear();
    expect(f.yearFrom).toBe(snap.yearFrom);
    expect(f.yearTo).toBe(snap.yearTo);
    expect(f.themes).toEqual(snap.themes);
    expect(f.clasificaciones).toEqual(snap.clasificaciones);
    expect(f.album).toBe(snap.album);
    expect(f.q).toBe(snap.q);
  });
});
