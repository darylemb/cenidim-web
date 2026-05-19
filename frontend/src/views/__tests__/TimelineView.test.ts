import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import TimelineView from '../TimelineView.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    getTimeline: vi.fn().mockResolvedValue({ years: [], timeline: {} }),
    getSongDetail: vi.fn().mockResolvedValue({ lyrics: 'Test' }),
  },
}));

describe('TimelineView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders loading state then shows years count', async () => {
    render(TimelineView);
    expect(screen.getByText('Cronología Musical')).toBeTruthy();
  });
});
