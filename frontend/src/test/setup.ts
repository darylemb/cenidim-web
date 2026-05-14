import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    getSongDetail: vi.fn().mockResolvedValue({}),
    getTimeline: vi.fn().mockResolvedValue({ years: [], timeline: {} }),
    getStats: vi.fn().mockResolvedValue({
      total_songs: 100,
      total_albums: 10,
      recently_added: 5,
      songs_with_lyrics: 80,
      avg_lyrics_length: 1200,
    }),
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
  },
}));

const mockChartInstance = {
  destroy: vi.fn(),
  update: vi.fn(),
  resize: vi.fn(),
  resizeHandler: null,
};

vi.mock('chart.js', () => {
  const MockChart: any = vi.fn(() => mockChartInstance);
  (MockChart as any).register = vi.fn();
  (MockChart as any).unregister = vi.fn();
  (MockChart as any).registerables = [];

  return {
    Chart: MockChart,
    CategoryScale: vi.fn(),
    LinearScale: vi.fn(),
    BarElement: vi.fn(),
    Title: vi.fn(),
    Tooltip: vi.fn(),
    Legend: vi.fn(),
    ArcElement: vi.fn(),
    LineElement: vi.fn(),
    PointElement: vi.fn(),
    RadialLinearScale: vi.fn(),
  };
});

vi.mock('vue-chartjs', () => ({
  Bar: vi.fn().mockReturnValue({ $el: document.createElement('div') }),
  Doughnut: vi.fn().mockReturnValue({ $el: document.createElement('div') }),
  Line: vi.fn().mockReturnValue({ $el: document.createElement('div') }),
  PolarArea: vi.fn().mockReturnValue({ $el: document.createElement('div') }),
}));
