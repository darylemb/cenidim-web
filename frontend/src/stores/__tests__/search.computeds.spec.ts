import { describe, it, expect, beforeEach, vi } from 'vitest';
import { flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { apiService } from '@/services/api';
import { useSearchStore } from '../search';

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn(),
  },
}));

describe('search store computeds', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('hasResults is false when results are empty', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 });
    const s = useSearchStore();
    expect(s.hasResults).toBe(false);
    await s.performSearch('q');
    expect(s.hasResults).toBe(false);
  });

  it('hasResults is true when results have length', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: [
        {
          id: 1,
          fonograma_id: 1,
          title: 'A',
          filename: '',
          lyrics: '',
          album: '',
          subtitulo: '',
          interprete_principal: '',
          interpretes_invitados: '',
          interprete_participante: '',
          soporte_fisico: '',
          editora: '',
          numero_catalogo: '',
          ciudad_edicion: '',
          pais_edicion: '',
          year: '',
          pistas: '',
          observaciones: '',
          clasificacion: '',
          tema: '',
        },
      ],
      total: 1,
    });
    const s = useSearchStore();
    await s.performSearch('q');
    expect(s.hasResults).toBe(true);
  });

  it('isLoading reflects the loading state', async () => {
    let resolvePromise: (v: unknown) => void = () => {};
    vi.mocked(apiService.searchSongs).mockImplementation(
      () =>
        new Promise((r) => {
          resolvePromise = r;
        })
    );
    const s = useSearchStore();
    expect(s.isLoading).toBe(false);
    const p = s.performSearch('q');
    expect(s.isLoading).toBe(true);
    resolvePromise({ results: [], total: 0 });
    await p;
    expect(s.isLoading).toBe(false);
  });

  it('totalPages rounds up partial pages', () => {
    const s = useSearchStore();
    // 21 results / 10 per page = 3 pages (ceil).
    s.total = 21;
    s.limit = 10;
    expect(s.totalPages).toBe(3);
    // Exact multiple returns the exact value.
    s.total = 20;
    s.limit = 10;
    expect(s.totalPages).toBe(2);
    // Zero returns zero.
    s.total = 0;
    expect(s.totalPages).toBe(0);
  });

  it('performSearch with explicit args updates each field', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 });
    const s = useSearchStore();
    await s.performSearch('hola', 'title', 2, 50, 'ESPAÑOL_ESTANDAR', 'title', 'desc');
    expect(s.query).toBe('hola');
    expect(s.field).toBe('title');
    expect(s.page).toBe(2);
    expect(s.limit).toBe(50);
    expect(s.clasificacion).toBe('ESPAÑOL_ESTANDAR');
    expect(s.orderBy).toBe('title');
    expect(s.orderDir).toBe('desc');
  });

  it('performSearch stores the api response', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({
      results: [
        {
          id: 1,
          fonograma_id: 1,
          title: 'A',
          filename: '',
          lyrics: '',
          album: '',
          subtitulo: '',
          interprete_principal: '',
          interpretes_invitados: '',
          interprete_participante: '',
          soporte_fisico: '',
          editora: '',
          numero_catalogo: '',
          ciudad_edicion: '',
          pais_edicion: '',
          year: '',
          pistas: '',
          observaciones: '',
          clasificacion: '',
          tema: '',
        },
        {
          id: 2,
          fonograma_id: 1,
          title: 'B',
          filename: '',
          lyrics: '',
          album: '',
          subtitulo: '',
          interprete_principal: '',
          interpretes_invitados: '',
          interprete_participante: '',
          soporte_fisico: '',
          editora: '',
          numero_catalogo: '',
          ciudad_edicion: '',
          pais_edicion: '',
          year: '',
          pistas: '',
          observaciones: '',
          clasificacion: '',
          tema: '',
        },
      ],
      total: 2,
    });
    const s = useSearchStore();
    await s.performSearch('q');
    expect(s.results.length).toBe(2);
    expect(s.total).toBe(2);
  });

  it('resetSearch resets query + field + triggers a refresh of results', async () => {
    vi.mocked(apiService.searchSongs).mockResolvedValue({ results: [], total: 0 });
    const s = useSearchStore();
    s.query = 'amigo';
    s.field = 'title';
    s.clasificacion = 'ESPAÑOL_REGIONAL';
    s.page = 3;
    s.limit = 50;
    s.orderBy = 'title';
    s.orderDir = 'desc';
    s.resetSearch();
    expect(s.query).toBe('');
    expect(s.field).toBe('all');
    expect(s.clasificacion).toBe('');
    expect(s.page).toBe(1);
    await flushPromises();
    expect(apiService.searchSongs).toHaveBeenCalled();
  });
});
