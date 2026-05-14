import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import CancionesView from '../CancionesView.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    searchSongs: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    getSongDetail: vi.fn().mockResolvedValue({ lyrics: 'Test lyrics' }),
  },
}));

describe('CancionesView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders empty state when no results', async () => {
    render(CancionesView);
    await new Promise((r) => setTimeout(r, 100));
    expect(screen.getByText(/No se encontraron resultados/)).toBeTruthy();
  });

  it('renders reset button', async () => {
    render(CancionesView);
    await new Promise((r) => setTimeout(r, 100));
    const btn = screen.getByText('Mostrar todas');
    expect(btn).toBeTruthy();
  });
});
