import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import CancionesView from '../CancionesView.vue';
import { apiService } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    getSongDetail: vi.fn().mockResolvedValue({ lyrics: 'Test lyrics' }),
  },
}));

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div/>' } }],
});

describe('CancionesView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('renders empty state when no results', async () => {
    render(CancionesView, { global: { plugins: [router] } });
    await waitFor(
      () => {
        expect(screen.getByText(/No se encontraron canciones/)).toBeTruthy();
      },
      { timeout: 1000 }
    );
  });

  it('toggle "Solo con letra" refetches with has_lyrics=true', async () => {
    render(CancionesView, { global: { plugins: [router] } });
    await waitFor(
      () => {
        expect(apiService.searchSongs).toHaveBeenCalled();
      },
      { timeout: 1000 }
    );
    const checkbox = screen.getByLabelText('Solo con letra') as HTMLInputElement;
    await fireEvent.click(checkbox);
    const lastCall = (apiService.searchSongs as ReturnType<typeof vi.fn>).mock.calls.at(-1);
    expect(lastCall?.[7]).toBe(true);
  });

  it('honours ?has_lyrics=1 deep-link from the dashboard KPI', async () => {
    const deepRouter = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div/>' } }],
    });
    await deepRouter.push({ path: '/', query: { has_lyrics: '1' } });
    render(CancionesView, { global: { plugins: [deepRouter] } });
    await waitFor(
      () => {
        expect(apiService.searchSongs).toHaveBeenCalled();
      },
      { timeout: 1000 }
    );
    const lastCall = (apiService.searchSongs as ReturnType<typeof vi.fn>).mock.calls.at(-1);
    expect(lastCall?.[7]).toBe(true);
  });
});
