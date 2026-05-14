import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    getSongDetail: vi.fn().mockResolvedValue({}),
    getTimeline: vi.fn().mockResolvedValue({ years: [], timeline: {} }),
    getStats: vi.fn().mockResolvedValue({}),
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
  },
}));
