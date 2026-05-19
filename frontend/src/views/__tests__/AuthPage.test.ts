import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import AuthPage from '../AuthPage.vue';

vi.mock('@/services/api', () => ({
  apiService: {
    login: vi.fn().mockResolvedValue({
      token: 'fake',
      user: { id: 1, username: 'test', email: 't@t.com', role: 'admin' },
    }),
    register: vi.fn().mockResolvedValue({
      token: 'fake',
      user: { id: 1, username: 'test', email: 't@t.com', role: 'admin' },
    }),
    getMe: vi.fn().mockResolvedValue(null),
  },
}));

describe('AuthPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('renders login and register tabs', () => {
    render(AuthPage);
    expect(screen.getByText('Iniciar Sesión')).toBeTruthy();
    expect(screen.getByText('Registrarse')).toBeTruthy();
  });

  it('renders login form fields', () => {
    render(AuthPage);
    expect(screen.getByLabelText('Usuario')).toBeTruthy();
    expect(screen.getByLabelText('Contraseña')).toBeTruthy();
  });

  it('switches to register mode when clicking register tab', async () => {
    const { getByText } = render(AuthPage);
    await getByText('Registrarse').click();
    expect(screen.getByLabelText('Correo')).toBeTruthy();
  });
});
