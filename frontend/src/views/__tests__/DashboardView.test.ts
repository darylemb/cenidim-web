import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import DashboardView from '../DashboardView.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    getStats: vi.fn().mockResolvedValue({
      total_songs: 100,
      total_albums: 10,
      catalog_total: 100,
      recently_added: 5,
      songs_with_lyrics: 80,
      avg_lyrics_length: 1200,
      songs_by_clasificacion: {},
      songs_by_year: {},
      songs_by_theme: {},
      distinct_themes: 0,
      top_albums: [],
      songs_by_oov_level: {},
      songs_by_indigena: {},
      songs_without_year: 0,
    }),
    getTimeline: vi.fn().mockResolvedValue({ years: [], timeline: {} }),
  },
}));

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div/>' } }],
});

describe('DashboardView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders dashboard title', () => {
    render(DashboardView, { global: { plugins: [router] } });
    expect(screen.getByText('Dashboards analíticos')).toBeTruthy();
  });

  it('renders the filters section', () => {
    render(DashboardView, { global: { plugins: [router] } });
    expect(screen.getByText('Criterios de búsqueda')).toBeTruthy();
  });
});
