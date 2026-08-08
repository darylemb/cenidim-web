/**
 * api.ts
 * Service for Go/Gin API calls.
 *
 * Uses native fetch promises.
 * Routes use /api to align with the configured proxy.
 */

import type {
  Song,
  Stats,
  TimelineData,
  SearchResponse,
  User,
  PaginatedResponse,
  AuthResponse,
} from '@/types';

const BASE_URL = '/api';

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('cenidim_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const apiService = {
  searchSongs: async (
    query = '',
    field = 'all',
    page = 1,
    limit = 20,
    clasificacion = '',
    orderBy = 'id',
    orderDir = 'asc',
    hasLyrics = false
  ): Promise<SearchResponse> => {
    try {
      const params = new URLSearchParams({
        query: query,
        field: field,
        page: String(page),
        limit: String(limit),
        order_by: orderBy,
        order_dir: orderDir,
      });
      if (clasificacion) {
        params.set('clasificacion', clasificacion);
      }
      if (hasLyrics) {
        params.set('has_lyrics', 'true');
      }
      const response = await fetch(`${BASE_URL}/search?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error searching songs:', error);
      throw error;
    }
  },

  getSongDetail: async (songId: number, signal?: AbortSignal): Promise<Song | null> => {
    try {
      const response = await fetch(`${BASE_URL}/song/${encodeURIComponent(songId)}`, { signal });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return null;
      console.error(`Error getting song with ID ${songId}:`, error);
      throw error;
    }
  },

  getTimeline: async (filterQuery = '', signal?: AbortSignal): Promise<TimelineData> => {
    try {
      const url = filterQuery ? `${BASE_URL}/timeline?${filterQuery}` : `${BASE_URL}/timeline`;
      const response = await fetch(url, { signal });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') throw error;
      console.error('Error getting timeline:', error);
      throw error;
    }
  },

  getStats: async (filterQuery = '', signal?: AbortSignal): Promise<Stats> => {
    try {
      const url = filterQuery ? `${BASE_URL}/stats?${filterQuery}` : `${BASE_URL}/stats`;
      const response = await fetch(url, {
        headers: { ...authHeaders() },
        signal,
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') throw error;
      console.error('Error getting stats:', error);
      throw error;
    }
  },

  getWordCloud: async (
    filterQuery: string = '',
    signal?: AbortSignal
  ): Promise<{
    words: { text: string; size: number }[];
    totalWords: number;
    excludedStopWords?: number;
  }> => {
    try {
      const url = filterQuery ? `${BASE_URL}/word-cloud?${filterQuery}` : `${BASE_URL}/word-cloud`;
      const response = await fetch(url, { signal });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') throw error;
      console.error('Error getting word cloud:', error);
      throw error;
    }
  },

  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Login failed');
    return data;
  },

  /**
   * Forgot password — sends a recovery link to the given email.
   * Always returns ok (the backend doesn't reveal whether the email
   * exists, to prevent user enumeration). In demo mode the link is
   * also returned in the response body when `EMAIL_DEMO=1` is set on
   * the backend.
   */
  forgotPassword: async (email: string): Promise<{ ok: true; dev_link?: string }> => {
    const response = await fetch(`${BASE_URL}/auth/forgot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo enviar el enlace');
    return data;
  },

  /**
   * Reset password using a one-shot token from the email link.
   * Returns ok on success; throws the server error on 4xx.
   */
  resetPassword: async (token: string, newPassword: string): Promise<{ ok: true }> => {
    const response = await fetch(`${BASE_URL}/auth/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo restablecer la contraseña');
    return data;
  },

  register: async (username: string, email: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Registration failed');
    return data;
  },

  getMe: async (): Promise<User | null> => {
    let response: Response;
    try {
      response = await fetch(`${BASE_URL}/auth/me`, {
        headers: { ...authHeaders() },
      });
    } catch (networkError) {
      // Network failure (offline, DNS, CORS, …). Surface as an error
      // so callers can keep their cache. Only an explicit 401/403
      // from the server should invalidate the session.
      throw networkError;
    }
    if (response.status === 401 || response.status === 403) {
      // Server explicitly rejected the credentials.
      return null;
    }
    if (!response.ok) {
      // 5xx, rate-limit, etc — the session may still be valid; the
      // caller should keep the cached user and retry later.
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  adminListFonogramas: async (page = 1, limit = 20): Promise<PaginatedResponse<Song>> => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas?page=${page}&limit=${limit}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminGetFonograma: async (id: number): Promise<Song> => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateFonograma: async (payload: Partial<Song>): Promise<Song> => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateFonograma: async (id: number, payload: Partial<Song>): Promise<Song> => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteFonograma: async (id: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error('Error');
  },

  adminListSongs: async (
    fonogramaId = '',
    page = 1,
    limit = 50
  ): Promise<PaginatedResponse<Song>> => {
    const q = fonogramaId ? `&fonograma_id=${fonogramaId}` : '';
    const response = await fetch(`${BASE_URL}/admin/songs?page=${page}&limit=${limit}${q}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateSong: async (payload: Partial<Song>): Promise<Song> => {
    const response = await fetch(`${BASE_URL}/admin/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateSong: async (id: number, payload: Partial<Song>): Promise<Song> => {
    const response = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteSong: async (id: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error('Error');
  },

  adminListUsers: async (): Promise<User[]> => {
    const response = await fetch(`${BASE_URL}/admin/users`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateUser: async (payload: {
    username: string;
    email: string;
    password: string;
    role?: string;
  }): Promise<User> => {
    const response = await fetch(`${BASE_URL}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateUser: async (id: number, payload: Partial<User>): Promise<User> => {
    const response = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteUser: async (id: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error('Error');
  },
};
