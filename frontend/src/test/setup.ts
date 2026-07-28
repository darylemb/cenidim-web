import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock the api module for tests that don't need the real service.
// The factory uses vi.fn()s that return safe defaults so tests that
// only call a subset of methods (e.g. login + getMe in the auth
// store test) don't have to mock every method individually.
//
// Tests that need the *real* apiService (e.g. api.spec.ts) should
// `vi.doUnmock('@/services/api')` at the top of the file. In Vitest
// this doesn't bypass an earlier vi.mock; instead the cleanest path
// is to refactor those tests to use `vi.mocked(apiService.methodName)`
// patterns once the methods exist on this mock.
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
      catalog_total: 100,
      songs_by_year: {},
      songs_by_clasificacion: {},
      songs_by_theme: {},
      distinct_themes: 0,
      top_albums: [],
      songs_by_oov_level: {},
      songs_by_indigena: {},
      songs_without_year: 0,
    }),
    getWordCloud: vi.fn().mockResolvedValue({
      words: [],
      totalWords: 0,
      excludedStopWords: 0,
    }),
    login: vi.fn().mockResolvedValue({
      token: 'mock-token',
      user: { id: 1, username: 'mock', email: 'mock@test', role: 'admin' },
    }),
    register: vi.fn().mockResolvedValue({
      token: 'mock-token',
      user: { id: 2, username: 'mock', email: 'mock@test', role: 'viewer' },
    }),
    getMe: vi.fn().mockResolvedValue({
      id: 1,
      username: 'mock',
      email: 'mock@test',
      role: 'admin',
      created_at: '',
    }),
    forgotPassword: vi.fn().mockResolvedValue({ ok: true }),
    adminListFonogramas: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    adminGetFonograma: vi.fn().mockResolvedValue({}),
    adminCreateFonograma: vi.fn().mockResolvedValue({}),
    adminUpdateFonograma: vi.fn().mockResolvedValue({}),
    adminDeleteFonograma: vi.fn().mockResolvedValue(undefined),
    adminListSongs: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    adminCreateSong: vi.fn().mockResolvedValue({}),
    adminUpdateSong: vi.fn().mockResolvedValue({ message: 'Song updated' }),
    adminDeleteSong: vi.fn().mockResolvedValue(undefined),
    adminListUsers: vi.fn().mockResolvedValue([]),
    adminCreateUser: vi.fn().mockResolvedValue({
      user: { id: 1, username: 'new', email: 'new@test', role: 'viewer' },
    }),
    adminUpdateUser: vi.fn().mockResolvedValue({ message: 'User updated' }),
    adminDeleteUser: vi.fn().mockResolvedValue(undefined),
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
