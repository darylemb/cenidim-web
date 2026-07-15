import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import TimelineView from '../TimelineView.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    getTimeline: vi.fn().mockResolvedValue({ years: [], timeline: {} }),
    getSongDetail: vi.fn().mockResolvedValue({ lyrics: 'Test' }),
  },
}));

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div/>' } }],
});

describe('TimelineView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders loading state then shows years count', async () => {
    render(TimelineView, { global: { plugins: [router] } });
    expect(screen.getByText('Cronología Musical')).toBeTruthy();
  });
});
