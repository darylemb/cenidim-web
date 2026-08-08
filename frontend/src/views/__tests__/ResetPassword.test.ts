import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/vue';
import { createRouter, createMemoryHistory } from 'vue-router';
import ResetPassword from '../ResetPassword.vue';
import { apiService } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiService: {
    resetPassword: vi.fn().mockResolvedValue({ ok: true }),
  },
}));

function makeRouter(token?: string) {
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/reset', component: { template: '<div/>' } }],
  });
}

describe('ResetPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('warns when there is no valid token', async () => {
    const router = makeRouter();
    await router.push('/reset');
    render(ResetPassword, { global: { plugins: [router] } });
    expect(screen.getByText(/enlace de recuperación no es válido/i)).toBeTruthy();
  });

  it('submits the new password when passwords match', async () => {
    const router = makeRouter();
    await router.push('/reset?token=abc123');
    render(ResetPassword, { global: { plugins: [router] } });
    await fireEvent.update(screen.getByLabelText('Nueva contraseña'), 'nueva-clave-123');
    await fireEvent.update(screen.getByLabelText('Repite la contraseña'), 'nueva-clave-123');
    await fireEvent.click(screen.getByText('Guardar contraseña'));
    await waitFor(() => {
      expect(apiService.resetPassword).toHaveBeenCalledWith('abc123', 'nueva-clave-123');
      expect(screen.getByText(/se actualizó correctamente/i)).toBeTruthy();
    });
  });

  it('rejects when passwords do not match', async () => {
    const router = makeRouter();
    await router.push('/reset?token=abc123');
    render(ResetPassword, { global: { plugins: [router] } });
    await fireEvent.update(screen.getByLabelText('Nueva contraseña'), 'clave-uno-123');
    await fireEvent.update(screen.getByLabelText('Repite la contraseña'), 'clave-dos-456');
    await fireEvent.click(screen.getByText('Guardar contraseña'));
    expect(screen.getByText(/no coinciden/i)).toBeTruthy();
    expect(apiService.resetPassword).not.toHaveBeenCalled();
  });
});
