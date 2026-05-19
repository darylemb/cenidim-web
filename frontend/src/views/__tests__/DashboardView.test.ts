import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import DashboardView from '../DashboardView.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    getStats: vi.fn().mockResolvedValue({
      total_songs: 100,
      total_albums: 10,
      recently_added: 5,
      songs_with_lyrics: 80,
      avg_lyrics_length: 1200,
      songs_by_clasificacion: {},
      songs_by_year: {},
      top_albums: [],
      songs_by_oov_level: {},
      songs_by_indigena: {},
    }),
  },
}));

describe('DashboardView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders dashboard title', async () => {
    render(DashboardView);
    expect(screen.getByText('Dashboards Analíticos')).toBeTruthy();
  });

  it('renders KPI cards', async () => {
    render(DashboardView);
    await new Promise((r) => setTimeout(r, 100));
    expect(screen.getByText(/Total de Álbumes/)).toBeTruthy();
    expect(screen.getByText(/Total de Canciones/)).toBeTruthy();
  });
});
