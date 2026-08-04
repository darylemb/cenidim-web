import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@/types';
import { apiService } from '@/services/api';

const USER_CACHE_KEY = 'cenidim_user';

function readCachedUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_CACHE_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function writeCachedUser(u: User | null): void {
  if (u) {
    localStorage.setItem(USER_CACHE_KEY, JSON.stringify(u));
  } else {
    localStorage.removeItem(USER_CACHE_KEY);
  }
}

export const useAuthStore = defineStore('auth', () => {
  // Hydrate the user from the localStorage cache synchronously so the
  // first paint of a guarded route already sees the user as
  // authenticated, even before /auth/me has a chance to return. This
  // is what stops the "I get bounced back to /login when I navigate
  // around in admin mode" symptom: a transient 5xx / network blip
  // from /auth/me no longer wipes the in-memory user, and the
  // explicit 401 path is the only one that clears the cache.
  const user = ref<User | null>(readCachedUser());
  const authLoading = ref(true);

  const isAuthenticated = computed(() => user.value !== null);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const isEditor = computed(() => user.value?.role === 'admin' || user.value?.role === 'editor');
  const userRole = computed(() => user.value?.role ?? null);

  async function restoreSession() {
    const token = localStorage.getItem('cenidim_token');
    if (!token) {
      user.value = null;
      writeCachedUser(null);
      authLoading.value = false;
      return;
    }
    try {
      const u = await apiService.getMe();
      if (u) {
        user.value = u;
        writeCachedUser(u);
      } else {
        // Explicit 401/403: the server rejected the token. Wipe
        // everything so the next navigation lands on /login.
        localStorage.removeItem('cenidim_token');
        user.value = null;
        writeCachedUser(null);
      }
    } catch {
      // 5xx / network blip: keep whatever we have in the cache. The
      // next guarded navigation will retry /auth/me and only an
      // explicit 401 will clear the session.
    } finally {
      authLoading.value = false;
    }
  }

  async function login(username: string, password: string) {
    const data = await apiService.login(username, password);
    localStorage.setItem('cenidim_token', data.token);
    user.value = data.user;
    writeCachedUser(data.user);
  }

  async function register(username: string, email: string, password: string) {
    const data = await apiService.register(username, email, password);
    localStorage.setItem('cenidim_token', data.token);
    user.value = data.user;
    writeCachedUser(data.user);
  }

  function logout() {
    localStorage.removeItem('cenidim_token');
    user.value = null;
    writeCachedUser(null);
  }

  // Refresh re-fetches the current user from /auth/me using the JWT in
  // localStorage. Network / 5xx errors are swallowed so the cached
  // user is preserved.
  async function refresh() {
    try {
      const u = await apiService.getMe();
      if (u) {
        user.value = u;
        writeCachedUser(u);
      }
    } catch {
      // keep the cache
    }
  }

  return {
    user,
    authLoading,
    isAuthenticated,
    isAdmin,
    isEditor,
    userRole,
    restoreSession,
    login,
    register,
    logout,
    refresh,
  };
});
