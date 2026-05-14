import type {
  SearchResponse,
  Song,
  Stats,
  TimelineData,
  User,
  Fonograma,
  AuthResponse,
  PaginatedResponse,
} from '@/types';

const BASE_URL = '/api';

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('cenidim_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const apiService = {
  async searchSongs(
    query = '',
    field = 'all',
    page = 1,
    limit = 20,
    clasificacion = '',
    orderBy = 'id',
    orderDir: 'asc' | 'desc' = 'asc'
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query,
      field,
      page: String(page),
      limit: String(limit),
      order_by: orderBy,
      order_dir: orderDir,
    });
    if (clasificacion) params.set('clasificacion', clasificacion);
    const res = await fetch(`${BASE_URL}/search?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getSongDetail(songId: number): Promise<Song> {
    const res = await fetch(`${BASE_URL}/song/${encodeURIComponent(songId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getTimeline(): Promise<TimelineData> {
    const res = await fetch(`${BASE_URL}/timeline`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getStats(): Promise<Stats> {
    const res = await fetch(`${BASE_URL}/stats`, { headers: authHeaders() });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async login(username: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    return data;
  },

  async register(username: string, email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Registration failed');
    return data;
  },

  async getMe(): Promise<User | null> {
    const res = await fetch(`${BASE_URL}/auth/me`, { headers: authHeaders() });
    if (!res.ok) return null;
    return res.json();
  },

  async adminListFonogramas(page = 1, limit = 20): Promise<PaginatedResponse<Fonograma>> {
    const res = await fetch(`${BASE_URL}/admin/fonogramas?page=${page}&limit=${limit}`, {
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminGetFonograma(id: number): Promise<Fonograma> {
    const res = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminCreateFonograma(payload: Partial<Fonograma>): Promise<Fonograma> {
    const res = await fetch(`${BASE_URL}/admin/fonogramas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminUpdateFonograma(id: number, payload: Partial<Fonograma>): Promise<Fonograma> {
    const res = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminDeleteFonograma(id: number): Promise<void> {
    const res = await fetch(`${BASE_URL}/admin/fonogramas/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
  },

  async adminListSongs(fonogramaId = '', page = 1, limit = 50): Promise<PaginatedResponse<Song>> {
    const q = fonogramaId ? `&fonograma_id=${fonogramaId}` : '';
    const res = await fetch(`${BASE_URL}/admin/songs?page=${page}&limit=${limit}${q}`, {
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminCreateSong(payload: Partial<Song>): Promise<Song> {
    const res = await fetch(`${BASE_URL}/admin/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminUpdateSong(id: number, payload: Partial<Song>): Promise<Song> {
    const res = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminDeleteSong(id: number): Promise<void> {
    const res = await fetch(`${BASE_URL}/admin/songs/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
  },

  async adminListUsers(): Promise<User[]> {
    const res = await fetch(`${BASE_URL}/admin/users`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminCreateUser(payload: Partial<User>): Promise<User> {
    const res = await fetch(`${BASE_URL}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminUpdateUser(id: number, payload: Partial<User>): Promise<User> {
    const res = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
    return data;
  },

  async adminDeleteUser(id: number): Promise<void> {
    const res = await fetch(`${BASE_URL}/admin/users/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error');
  },
};
