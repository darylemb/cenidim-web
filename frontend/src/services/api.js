/**
 * api.js
 * Service for Go/Gin API calls.
 *
 * Uses native fetch promises.
 * Routes use /api to align with the configured proxy.
 */

const BASE_URL = '/api';

function authHeaders() {
  const token = localStorage.getItem('cenidim_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const apiService = {
  /**
   * Search songs in the backend with pagination.
   * @param {string} query Text to search
   * @param {string} field Field to search (default "all")
   * @param {number} page Current page number (default 1)
   * @param {number} limit Number of items per page (default 20)
   * @returns {Promise<Object>} Object with "results" array and "total" count
   */
  searchSongs: async (
    query = '',
    field = 'all',
    page = 1,
    limit = 20,
    clasificacion = '',
    orderBy = 'id',
    orderDir = 'asc'
  ) => {
    try {
      const params = new URLSearchParams({
        query: query,
        field: field,
        page: Number(page),
        limit: Number(limit),
        order_by: orderBy,
        order_dir: orderDir,
      });
      if (clasificacion) {
        params.set('clasificacion', clasificacion);
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

  /**
   * Get the song detail and lyrics by its ID.
   * @param {number} songId The song ID
   * @returns {Promise<Object>} Song detail
   */
  getSongDetail: async (songId) => {
    try {
      const response = await fetch(`${BASE_URL}/song/${encodeURIComponent(songId)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error getting song with ID ${songId}:`, error);
      throw error;
    }
  },
  /**
   * Get songs grouped by year for the timeline view.
   * @returns {Promise<Object>} Object with "years" array and "timeline" map
   */
  getTimeline: async () => {
    try {
      const response = await fetch(`${BASE_URL}/timeline`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting timeline:', error);
      throw error;
    }
  },

  // ── Auth ──────────────────────────────────────────────────────────────
  login: async (username, password) => {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Login failed');
    return data;
  },

  register: async (username, email, password) => {
    const response = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Registration failed');
    return data;
  },

  getMe: async () => {
    const response = await fetch(`${BASE_URL}/auth/me`, {
      headers: { ...authHeaders() },
    });
    if (!response.ok) return null;
    return response.json();
  },

  // ── Admin – Fonogramas ────────────────────────────────────────────────
  adminListFonogramas: async (page = 1, limit = 20) => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas?page=${page}&limit=${limit}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminGetFonograma: async (id) => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateFonograma: async (payload) => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateFonograma: async (id, payload) => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteFonograma: async (id) => {
    const response = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  // ── Admin – Songs ─────────────────────────────────────────────────────
  adminListSongs: async (fonogramaId = '', page = 1, limit = 50) => {
    const q = fonogramaId ? `&fonograma_id=${fonogramaId}` : '';
    const response = await fetch(`${BASE_URL}/admin/songs?page=${page}&limit=${limit}${q}`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateSong: async (payload) => {
    const response = await fetch(`${BASE_URL}/admin/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateSong: async (id, payload) => {
    const response = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteSong: async (id) => {
    const response = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  // ── Admin – Users ─────────────────────────────────────────────────────
  adminListUsers: async () => {
    const response = await fetch(`${BASE_URL}/admin/users`, {
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminCreateUser: async (payload) => {
    const response = await fetch(`${BASE_URL}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminUpdateUser: async (id, payload) => {
    const response = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },

  adminDeleteUser: async (id) => {
    const response = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Error');
    return data;
  },
};
