import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/vue';
import ForgotPassword from '../ForgotPassword.vue';
import { apiService } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiService: {
    forgotPassword: vi.fn().mockResolvedValue({ ok: true }),
  },
}));

describe('ForgotPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the email form', () => {
    render(ForgotPassword);
    expect(screen.getByLabelText('Correo')).toBeTruthy();
    expect(screen.getByText('Enviar enlace')).toBeTruthy();
  });

  it('submits the email and shows the confirmation message', async () => {
    render(ForgotPassword);
    await fireEvent.update(screen.getByLabelText('Correo'), 'alguien@cenidim.mx');
    await fireEvent.click(screen.getByText('Enviar enlace'));
    await waitFor(() => {
      expect(apiService.forgotPassword).toHaveBeenCalledWith('alguien@cenidim.mx');
      expect(screen.getByText(/recibirás un enlace/i)).toBeTruthy();
    });
  });

  it('shows the dev link when the backend returns one (demo mode)', async () => {
    vi.mocked(apiService.forgotPassword).mockResolvedValueOnce({
      ok: true,
      dev_link: 'http://localhost:8000/reset?token=abc',
    });
    render(ForgotPassword);
    await fireEvent.update(screen.getByLabelText('Correo'), 'demo@cenidim.mx');
    await fireEvent.click(screen.getByText('Enviar enlace'));
    await waitFor(() => {
      expect(screen.getByText(/http:\/\/localhost:8000\/reset\?token=abc/)).toBeTruthy();
    });
  });
});
