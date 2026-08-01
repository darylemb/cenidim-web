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

  it('restoreSession clears the token when getMe returns null (server 401)', async () => {
    localStorage.setItem('cenidim_token', 'STALE');
    vi.mocked(apiService.getMe).mockResolvedValue(null);
    const auth = useAuthStore();
    await auth.restoreSession();
    // A null from getMe now means an explicit 401/403: the server
    // rejected the token, so we wipe it. 5xx / network errors take
    // the other branch (catch) and preserve the cache.
    expect(auth.user).toBeNull();
    expect(localStorage.getItem('cenidim_token')).toBeNull();
    expect(auth.authLoading).toBe(false);
  });

  it('restoreSession keeps the token + user cache when getMe throws (5xx / network)', async () => {
    localStorage.setItem('cenidim_token', 'GOOD');
    localStorage.setItem(
      'cenidim_user',
      JSON.stringify({ id: 7, username: 'cached', email: 'c@x', role: 'editor' })
    );
    vi.mocked(apiService.getMe).mockRejectedValue(new Error('HTTP error! status: 503'));
    const auth = useAuthStore();
    await auth.restoreSession();
    // A transient backend failure must not log the user out. The
    // cached user stays in the store and the token stays in
    // localStorage; the next restoreSession (or refresh) will retry.
    expect(auth.user?.username).toBe('cached');
    expect(localStorage.getItem('cenidim_token')).toBe('GOOD');
    expect(auth.authLoading).toBe(false);
  });

  it('restoreSession hydrates the user synchronously from the localStorage cache', () => {
    localStorage.setItem('cenidim_token', 'TKN');
    localStorage.setItem(
      'cenidim_user',
      JSON.stringify({ id: 11, username: 'warm', email: 'w@x', role: 'admin' })
    );
    const auth = useAuthStore();
    // Read it before /auth/me has had a chance to return.
    expect(auth.user?.username).toBe('warm');
    expect(auth.isAuthenticated).toBe(true);
    expect(auth.isAdmin).toBe(true);
  });

  it('login persists the user to localStorage', async () => {
    vi.mocked(apiService.login).mockResolvedValue({
      token: 'tok',
      user: { id: 1, username: 'admin', email: 'admin@x', role: 'admin' },
    });
    const auth = useAuthStore();
    await auth.login('admin', 'admin123');
    const cached = JSON.parse(localStorage.getItem('cenidim_user') || 'null');
    expect(cached?.username).toBe('admin');
  });

  it('logout clears the user cache as well as the token', () => {
    localStorage.setItem('cenidim_token', 'X');
    localStorage.setItem(
      'cenidim_user',
      JSON.stringify({ id: 1, username: 'a', email: 'a@x', role: 'viewer' })
    );
    const auth = useAuthStore();
    auth.user = { id: 1, username: 'a', email: 'a@x', role: 'viewer' };
    auth.logout();
    expect(auth.user).toBeNull();
    expect(localStorage.getItem('cenidim_token')).toBeNull();
    expect(localStorage.getItem('cenidim_user')).toBeNull();
  });

  it('refresh swallows 5xx / network errors and keeps the cache', async () => {
    localStorage.setItem(
      'cenidim_user',
      JSON.stringify({ id: 4, username: 'keep', email: 'k@x', role: 'editor' })
    );
    const auth = useAuthStore();
    expect(auth.user?.username).toBe('keep');
    vi.mocked(apiService.getMe).mockRejectedValue(new Error('HTTP error! status: 502'));
    await auth.refresh();
    expect(auth.user?.username).toBe('keep');
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
