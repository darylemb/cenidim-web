import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import CancionesView from '../CancionesView.vue';

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
});
