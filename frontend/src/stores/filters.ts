import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { LocationQuery, LocationQueryRaw } from 'vue-router';

export interface FilterState {
  themes: string[];
  yearFrom: number | null;
  yearTo: number | null;
  clasificaciones: string[];
  album: string | null;
  q: string;
}

const NONE = '__none__';
const DEBOUNCE_MS = 250;

function emptyState(): FilterState {
  return {
    themes: [],
    yearFrom: null,
    yearTo: null,
    clasificaciones: [],
    album: null,
    q: '',
  };
}

function parseIntOrNull(v: unknown): number | null {
  if (v == null || v === '') return null;
  if (Array.isArray(v)) v = v[0];
  const n = Number.parseInt(String(v), 10);
  return Number.isFinite(n) ? n : null;
}

function parseList(v: unknown): string[] {
  if (v == null || v === '') return [];
  const s = Array.isArray(v) ? v.join(',') : String(v);
  return s
    .split(',')
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

export const useFiltersStore = defineStore('filters', () => {
  const themes = ref<string[]>([]);
  const yearFrom = ref<number | null>(null);
  const yearTo = ref<number | null>(null);
  const clasificaciones = ref<string[]>([]);
  const album = ref<string | null>(null);
  const q = ref<string>('');

  // Debounce handles for year range and free-text.
  let yearTimer: ReturnType<typeof setTimeout> | null = null;
  let qTimer: ReturnType<typeof setTimeout> | null = null;
  const debounceListeners = new Set<() => void>();

  function debounceNotify() {
    debounceListeners.forEach((cb) => cb());
  }

  function onDebouncedFlush(cb: () => void): () => void {
    debounceListeners.add(cb);
    return () => debounceListeners.delete(cb);
  }

  function applyFromQuery(query: LocationQuery) {
    themes.value = parseList(query.theme);
    clasificaciones.value = parseList(query.clasificacion);
    yearFrom.value = parseIntOrNull(query.year_from);
    yearTo.value = parseIntOrNull(query.year_to);
    const a = query.album;
    album.value = a == null || a === '' ? null : String(Array.isArray(a) ? a[0] : a);
    const qq = query.q;
    q.value = qq == null ? '' : String(Array.isArray(qq) ? qq[0] : qq);

    // Drop invalid values silently (e.g. year_from > year_to).
    if (yearFrom.value != null && yearTo.value != null && yearFrom.value > yearTo.value) {
      yearFrom.value = null;
      yearTo.value = null;
    }
  }

  function toQuery(): LocationQueryRaw {
    const out: LocationQueryRaw = {};
    if (themes.value.length) out.theme = themes.value.join(',');
    if (yearFrom.value != null) out.year_from = String(yearFrom.value);
    if (yearTo.value != null) out.year_to = String(yearTo.value);
    if (clasificaciones.value.length) out.clasificacion = clasificaciones.value.join(',');
    if (album.value) out.album = album.value;
    if (q.value) out.q = q.value;
    return out;
  }

  function clear() {
    themes.value = [];
    yearFrom.value = null;
    yearTo.value = null;
    clasificaciones.value = [];
    album.value = null;
    q.value = '';
  }

  function setYearRange(from: number | null, to: number | null) {
    if (yearTimer) clearTimeout(yearTimer);
    yearTimer = setTimeout(() => {
      yearFrom.value = from;
      yearTo.value = to;
      debounceNotify();
    }, DEBOUNCE_MS);
  }

  function setQ(value: string) {
    if (qTimer) clearTimeout(qTimer);
    qTimer = setTimeout(() => {
      q.value = value;
      debounceNotify();
    }, DEBOUNCE_MS);
  }

  const queryString = computed(() => {
    const q = toQuery();
    const usp = new URLSearchParams();
    for (const [k, v] of Object.entries(q)) {
      if (v == null) continue;
      usp.set(k, String(v));
    }
    return usp.toString();
  });

  const active = computed(() => {
    const chips: { key: string; label: string; onRemove: () => void }[] = [];
    themes.value.forEach((t) =>
      chips.push({
        key: `theme:${t}`,
        label: `Tema: ${t === NONE ? 'Sin tema' : t}`,
        onRemove: () => {
          themes.value = themes.value.filter((x) => x !== t);
        },
      })
    );
    if (yearFrom.value != null || yearTo.value != null) {
      chips.push({
        key: 'year',
        label: `Año: ${yearFrom.value ?? '*'} – ${yearTo.value ?? '*'}`,
        onRemove: () => {
          yearFrom.value = null;
          yearTo.value = null;
        },
      });
    }
    clasificaciones.value.forEach((c) =>
      chips.push({
        key: `clasificacion:${c}`,
        label: `Clasificación: ${c}`,
        onRemove: () => {
          clasificaciones.value = clasificaciones.value.filter((x) => x !== c);
        },
      })
    );
    if (album.value) {
      const v = album.value;
      chips.push({
        key: 'album',
        label: `Álbum: ${v}`,
        onRemove: () => {
          album.value = null;
        },
      });
    }
    if (q.value) {
      const v = q.value;
      chips.push({
        key: 'q',
        label: `Buscar: ${v}`,
        onRemove: () => {
          q.value = '';
        },
      });
    }
    return chips;
  });

  const isEmpty = computed(
    () =>
      themes.value.length === 0 &&
      yearFrom.value == null &&
      yearTo.value == null &&
      clasificaciones.value.length === 0 &&
      !album.value &&
      !q.value
  );

  // Explicit setters so callers (including DashboardFilters' direct
  // assignment) can mutate the store through Pinia's proxy instead of
  // fighting with how setup-style stores expose refs.
  function setThemes(t: string[]) { themes.value = [...t] }
  function setClasificaciones(c: string[]) { clasificaciones.value = [...c] }

  return {
    themes,
    yearFrom,
    yearTo,
    clasificaciones,
    album,
    q,
    applyFromQuery,
    toQuery,
    clear,
    setYearRange,
    setQ,
    setThemes,
    setClasificaciones,
    onDebouncedFlush,
    queryString,
    active,
    isEmpty,
    emptyState,
  };
});

export { NONE as THEME_NONE, DEBOUNCE_MS };
