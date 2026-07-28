import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@/types';
import { apiService } from '@/services/api';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const authLoading = ref(true);

  const isAuthenticated = computed(() => user.value !== null);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const isEditor = computed(() => user.value?.role === 'admin' || user.value?.role === 'editor');
  const userRole = computed(() => user.value?.role ?? null);

  async function restoreSession() {
    const token = localStorage.getItem('cenidim_token');
    if (!token) {
      authLoading.value = false;
      return;
    }
    try {
      const u = await apiService.getMe();
      user.value = u;
    } catch {
      localStorage.removeItem('cenidim_token');
    } finally {
      authLoading.value = false;
    }
  }

  async function login(username: string, password: string) {
    const data = await apiService.login(username, password);
    localStorage.setItem('cenidim_token', data.token);
    user.value = data.user;
  }

  async function register(username: string, email: string, password: string) {
    const data = await apiService.register(username, email, password);
    localStorage.setItem('cenidim_token', data.token);
    user.value = data.user;
  }

  function logout() {
    localStorage.removeItem('cenidim_token');
    user.value = null;
  }

  // Refresh re-fetches the current user from /auth/me using the JWT in
  // localStorage.
  async function refresh() {
    const u = await apiService.getMe();
    if (u) {
      user.value = u;
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
