import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '../auth';
import { apiService } from '@/services/api';

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('starts logged-out', () => {
    const auth = useAuthStore();
    expect(auth.user).toBeNull();
    expect(auth.isAuthenticated).toBe(false);
  });

  it('login writes the token to localStorage and sets user', async () => {
    vi.mocked(apiService.login).mockResolvedValue({
      token: 'tok123',
      user: { id: 1, username: 'admin', email: 'admin@x', role: 'admin' },
    });
    const auth = useAuthStore();
    await auth.login('admin', 'admin123');
    expect(auth.user?.username).toBe('admin');
    expect(auth.user?.role).toBe('admin');
    expect(localStorage.getItem('cenidim_token')).toBe('tok123');
  });

  it('register sets user and writes the token', async () => {
    vi.mocked(apiService.register).mockResolvedValue({
      token: 'reg',
      user: { id: 2, username: 'new', email: 'new@x', role: 'viewer' },
    });
    const auth = useAuthStore();
    await auth.register('new', 'new@x', 'pw');
    expect(auth.user?.username).toBe('new');
    expect(localStorage.getItem('cenidim_token')).toBe('reg');
  });

  it('logout clears user and removes the token', () => {
    localStorage.setItem('cenidim_token', 'X');
    const auth = useAuthStore();
    auth.user = { id: 1, username: 'a', email: 'a@x', role: 'viewer' };
    auth.logout();
    expect(auth.user).toBeNull();
    expect(localStorage.getItem('cenidim_token')).toBeNull();
  });

  it('restoreSession fetches user when a token exists', async () => {
    localStorage.setItem('cenidim_token', 'TOKEN');
    vi.mocked(apiService.getMe).mockResolvedValue({
      id: 5,
      username: 'restored',
      email: 'r@x',
      role: 'editor',
      created_at: '',
    });
    const auth = useAuthStore();
    await auth.restoreSession();
    expect(auth.user?.id).toBe(5);
    expect(auth.user?.username).toBe('restored');
    expect(auth.authLoading).toBe(false);
  });

  it('restoreSession leaves the token when getMe returns null (no exception)', async () => {
    localStorage.setItem('cenidim_token', 'STALE');
    vi.mocked(apiService.getMe).mockResolvedValue(null);
    const auth = useAuthStore();
    await auth.restoreSession();
    // The store keeps the stale token because the API succeeded —
    // a null user just means there's no session. The cleanup path
    // is the catch block (real 401), not the success path.
    expect(auth.user).toBeNull();
    expect(localStorage.getItem('cenidim_token')).toBe('STALE');
    expect(auth.authLoading).toBe(false);
  });

  it('restoreSession is a no-op when no token exists', async () => {
    const auth = useAuthStore();
    await auth.restoreSession();
    expect(auth.user).toBeNull();
    expect(apiService.getMe).not.toHaveBeenCalled();
    expect(auth.authLoading).toBe(false);
  });

  it('refresh updates the user from /me', async () => {
    vi.mocked(apiService.getMe).mockResolvedValue({
      id: 9,
      username: 'refreshed',
      email: 'r@x',
      role: 'admin',
      created_at: '',
    });
    const auth = useAuthStore();
    await auth.refresh();
    expect(auth.user?.username).toBe('refreshed');
  });

  it('refresh is a no-op when getMe returns null', async () => {
    const auth = useAuthStore();
    await auth.refresh();
    expect(auth.user).toBeNull();
  });

  it('computed flags reflect the user role', () => {
    const auth = useAuthStore();
    expect(auth.isAdmin).toBe(false);
    expect(auth.isEditor).toBe(false);
    auth.user = { id: 1, username: 'a', email: 'a@x', role: 'admin' };
    expect(auth.isAdmin).toBe(true);
    expect(auth.isEditor).toBe(true);
    auth.user = { id: 2, username: 'e', email: 'e@x', role: 'editor' };
    expect(auth.isAdmin).toBe(false);
    expect(auth.isEditor).toBe(true);
    auth.user = { id: 3, username: 'v', email: 'v@x', role: 'viewer' };
    expect(auth.isEditor).toBe(false);
  });
});
