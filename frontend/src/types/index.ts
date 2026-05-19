export type Clasificacion = 'ESPAÑOL_ESTANDAR' | 'ESPAÑOL_REGIONAL' | 'LENGUA_INDIGENA' | '';
export type UserRole = 'viewer' | 'editor' | 'admin';
export type OrderDir = 'asc' | 'desc';
export type OrderBy = 'id' | 'clave' | 'title' | 'album' | 'year' | 'filename' | 'clasificacion';
export type Field = 'all' | 'title' | 'album' | 'lyrics';

export interface Song {
  id: number;
  fonograma_id: number;
  title: string;
  album: string;
  subtitulo: string;
  interprete_principal: string;
  interpretes_invitados: string;
  interprete_participante: string;
  soporte_fisico: string;
  editora: string;
  numero_catalogo: string;
  ciudad_edicion: string;
  pais_edicion: string;
  year: string;
  pistas: string;
  observaciones: string;
  filename: string;
  clasificacion: string;
  lyrics?: string;
  created_at?: string;
}

export interface Fonograma {
  clave_fonograma: number;
  titulo: string;
  subtitulo: string;
  interprete_principal: string;
  interpretes_invitados: string;
  interprete_participante: string;
  soporte_fisico: string;
  editora: string;
  numero_catalogo: string;
  ciudad_edicion: string;
  pais_edicion: string;
  anio: string;
  pistas: string;
  observaciones: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
}

export interface Stats {
  total_songs: number;
  total_albums: number;
  songs_by_year: Record<string, number>;
  songs_by_clasificacion: Record<string, number>;
  recently_added: number;
  top_albums: AlbumCount[];
  avg_lyrics_length: number;
  songs_with_lyrics: number;
  songs_by_oov_level: Record<string, number>;
  songs_by_indigena: Record<string, number>;
}

export interface AlbumCount {
  album: string;
  year: string;
  count: number;
}

export interface TimelineData {
  years: string[];
  timeline: Record<string, Song[]>;
}

export interface SearchResponse {
  results: Song[];
  total: number;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface PaginatedResponse<T> {
  results: T[];
  total: number;
  page: number;
  limit: number;
}
