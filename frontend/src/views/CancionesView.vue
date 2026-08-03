<template>
  <div class="content-area">
    <header class="canciones__masthead">
      <div>
        <span class="eyebrow">Catálogo</span>
        <h1 class="canciones__title display">Canciones</h1>
      </div>
      <div class="canciones__total">
        <span class="canciones__total-num display mono">{{ total.toLocaleString() }}</span>
        <span class="canciones__total-label">resultados</span>
      </div>
    </header>

    <section class="canciones__controls" aria-label="Controles de tabla">
      <label class="canciones__select-wrap">
        <span class="canciones__select-label eyebrow">Búsqueda</span>
        <input
          v-model="localQuery"
          type="search"
          class="canciones__input"
          placeholder="Palabra en título, álbum o letra"
          @input="onQueryChange"
        />
      </label>

      <label class="canciones__select-wrap">
        <span class="canciones__select-label eyebrow">Clasificación</span>
        <select
          v-model="localClasificacion"
          class="canciones__select"
          @change="onClasificacionChange"
        >
          <option value="">Todas</option>
          <option value="ESPAÑOL_ESTANDAR">Estándar</option>
          <option value="ESPAÑOL_REGIONAL">Regional</option>
          <option value="LENGUA_INDIGENA">Indígena</option>
        </select>
      </label>

      <label class="canciones__select-wrap">
        <span class="canciones__select-label eyebrow">Ordenar por</span>
        <select v-model="localOrderBy" class="canciones__select" @change="onOrderByChange">
          <option value="id">ID</option>
          <option value="clave">Clave</option>
          <option value="title">Pista</option>
          <option value="album">Álbum</option>
          <option value="year">Año</option>
          <option value="filename">Archivo</option>
          <option value="clasificacion">Clasificación</option>
        </select>
      </label>

      <label class="canciones__select-wrap">
        <span class="canciones__select-label eyebrow">Dirección</span>
        <select v-model="localOrderDir" class="canciones__select" @change="onOrderDirChange">
          <option value="asc">Ascendente</option>
          <option value="desc">Descendente</option>
        </select>
      </label>
    </section>

    <div class="results-table-container">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>Buscando en el archivo del CENIDIM…</p>
      </div>
      <div class="table-scroll-wrapper">
        <table :class="['results-table', 'results-table--wide', { loadingopacity: loading }]">
          <!-- Fixed column widths: with table-layout:fixed the header
               row defines the geometry, so the table never reflows when
               filters/page change (review request 03/ago/2026). -->
          <colgroup>
            <col style="width: 72px" />
            <col style="width: 190px" />
            <col style="width: 170px" />
            <col style="width: 130px" />
            <col style="width: 160px" />
            <col style="width: 130px" />
            <col style="width: 130px" />
            <col style="width: 84px" />
            <col style="width: 130px" />
            <col style="width: 100px" />
            <col style="width: 100px" />
            <col style="width: 92px" />
            <col style="width: 70px" />
            <col style="width: 210px" />
            <col style="width: 210px" />
            <col style="width: 150px" />
            <col style="width: 130px" />
            <col style="width: 150px" />
            <col style="width: 96px" />
          </colgroup>
          <thead>
            <tr>
              <th
                v-for="col in songCols"
                :key="col.key"
                :class="['sortable-th', { 'sortable-th--active': col.sortable && localOrderBy === col.key }]"
                :aria-sort="col.sortable && localOrderBy === col.key ? (localOrderDir === 'asc' ? 'ascending' : 'descending') : undefined"
                :role="col.sortable ? 'button' : undefined"
                @click="col.sortable && onSortCol(col.key)"
              >
                <span class="sortable-th__label">{{ col.label }}</span>
                <span
                  v-if="col.sortable && localOrderBy === col.key"
                  class="sortable-th__arrow"
                  aria-hidden="true"
                >
                  {{ localOrderDir === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="song in results" :key="song.id">
              <td data-label="Clave" class="mono">{{ song.fonograma_id }}</td>
              <td data-label="Pista" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.title">{{ song.title }}</span>
              </td>
              <td data-label="Álbum" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.album">{{ song.album }}</span>
              </td>
              <td data-label="Subtítulo" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.subtitulo">{{ song.subtitulo }}</span>
              </td>
              <td data-label="Intérprete Principal" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.interprete_principal">{{
                  song.interprete_principal
                }}</span>
              </td>
              <td data-label="Intérpretes Invitados" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.interpretes_invitados">{{
                  song.interpretes_invitados
                }}</span>
              </td>
              <td data-label="Intérprete Participante" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.interprete_participante">{{
                  song.interprete_participante
                }}</span>
              </td>
              <td data-label="Soporte Físico" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.soporte_fisico">{{
                  song.soporte_fisico
                }}</span>
              </td>
              <td data-label="Editora" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.editora">{{ song.editora }}</span>
              </td>
              <td data-label="N° Catálogo" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.numero_catalogo">{{
                  song.numero_catalogo
                }}</span>
              </td>
              <td data-label="Ciudad" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.ciudad_edicion">{{
                  song.ciudad_edicion
                }}</span>
              </td>
              <td data-label="País" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.pais_edicion">{{ song.pais_edicion }}</span>
              </td>
              <td data-label="Año" class="table-cell-truncate mono">
                <span class="table-cell-text" :title="song.year">{{ song.year }}</span>
              </td>
              <td data-label="Pistas" class="table-cell-truncate cell-pistas">
                <span class="table-cell-text" :title="song.pistas">{{ song.pistas }}</span>
              </td>
              <td data-label="Observaciones" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.observaciones">{{
                  song.observaciones
                }}</span>
              </td>
              <td data-label="Archivo" class="table-cell-truncate mono">
                <span class="table-cell-text" :title="song.filename">{{ song.filename }}</span>
              </td>
              <td data-label="Clasificación">
                <span :class="['clasificacion-badge', badgeClass(song.clasificacion)]">
                  {{ labelText(song.clasificacion) }}
                </span>
              </td>
              <td data-label="Tema">
                <ThemeBadge :theme="song.tema ?? ''" />
              </td>
              <td data-label="Acción">
                <button v-if="song.filename" class="action-btn" @click="openLyrics(song.id)">
                  Ver Letra
                </button>
                <span v-else class="table-cell-muted">—</span>
              </td>
            </tr>
            <tr v-if="!loading && results.length === 0">
              <td colspan="19">
                <EmptyState
                  label="No se encontraron canciones para los criterios aplicados."
                  description="Pruebe a relajar los criterios, o use la sección de filtros arriba."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="total > 0" class="pagination-container">
      <div class="pagination-info">
        Mostrando <strong>{{ results.length }}</strong> de <strong>{{ total }}</strong> resultados
      </div>
      <div class="pagination-controls">
        <button class="pagination-btn" :disabled="page === 1" @click="changePage(page - 1)">
          &laquo; Anterior
        </button>
        <div class="pagination-pages">
          <button
            v-for="p in pageNumbers"
            :key="p"
            :class="['page-num', { active: p === page }]"
            @click="changePage(p)"
          >
            {{ p }}
          </button>
        </div>
        <button
          class="pagination-btn"
          :disabled="page === totalPages"
          @click="changePage(page + 1)"
        >
          Siguiente &raquo;
        </button>
      </div>
      <div class="pagination-limit">
        <select :value="limit" @change="onLimitChange">
          <option value="20">20 por página</option>
          <option value="50">50 por página</option>
          <option value="100">100 por página</option>
        </select>
      </div>
    </div>

    <LyricModal
      v-if="selectedSongId"
      :song="selectedSongData"
      :lyrics="selectedLyrics"
      :loading="loadingLyrics"
      @close="selectedSongId = null"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * CancionesView is the catalog browser.
 *
 * The dashboard's filter set (year range, theme chips, album, free-text) is
 * independent of this view. CancionesView manages its OWN local state
 * (free-text query, classification, ordering, page, limit) via
 * `useSearchStore`, with no coupling to `useFiltersStore`. This keeps
 * the two views from contaminating each other.
 *
 * Data consistency note: the `tema` value shown by ThemeBadge comes
 * directly from `songs.tema` — the same column the dashboard stats
 * group by and the same column the word cloud filters by. After
 * `scripts/classify_songs.py` runs, that column holds the literal
 * "Tema: ..." value from each LetrasTXT/*.txt file (no inference).
 */
import { ref, computed, onMounted } from 'vue';
import { useSearchStore } from '@/stores/search';
import { apiService } from '@/services/api';
import type { Song } from '@/types';
import LyricModal from '@/components/LyricModal.vue';
import ThemeBadge from '@/components/ThemeBadge.vue';
import EmptyState from '@/components/EmptyState.vue';
import { storeToRefs } from 'pinia';

const search = useSearchStore();
const { results, total, page, limit, loading } = storeToRefs(search);

// Local view state — fully self-contained.
const localQuery = ref('');
const localClasificacion = ref('');
const localOrderBy = ref<string>('id');
const localOrderDir = ref<'asc' | 'desc'>('asc');
const selectedSongId = ref<number | null>(null);
const selectedSongData = ref<Song | null>(null);
const selectedLyrics = ref('');
const loadingLyrics = ref(false);

// Column model for the catalog table. ``key`` is the backend order_by
// value; ``sortable`` false for the action column. Clicking a sortable
// header toggles asc/desc and refetches (review request 03/ago/2026).
const songCols: Array<{ key: string; label: string; sortable: boolean }> = [
  { key: 'clave', label: 'Clave', sortable: true },
  { key: 'title', label: 'Pista', sortable: true },
  { key: 'album', label: 'Álbum', sortable: true },
  { key: 'subtitulo', label: 'Subtítulo', sortable: true },
  { key: 'interprete_principal', label: 'Intérprete Principal', sortable: true },
  { key: 'interpretes_invitados', label: 'Intérpretes Invitados', sortable: true },
  { key: 'interprete_participante', label: 'Intérprete Participante', sortable: true },
  { key: 'soporte_fisico', label: 'Soporte Físico', sortable: true },
  { key: 'editora', label: 'Editora', sortable: true },
  { key: 'numero_catalogo', label: 'N° Catálogo', sortable: true },
  { key: 'ciudad_edicion', label: 'Ciudad', sortable: true },
  { key: 'pais_edicion', label: 'País', sortable: true },
  { key: 'year', label: 'Año', sortable: true },
  { key: 'pistas', label: 'Pistas', sortable: true },
  { key: 'observaciones', label: 'Observaciones', sortable: true },
  { key: 'filename', label: 'Archivo', sortable: true },
  { key: 'clasificacion', label: 'Clasificación', sortable: true },
  { key: 'tema', label: 'Tema', sortable: true },
  { key: 'actions', label: 'Acción', sortable: false },
];

function onSortCol(key: string) {
  if (key === localOrderBy.value) {
    localOrderDir.value = localOrderDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    localOrderBy.value = key;
    localOrderDir.value = 'asc';
  }
  search.performSearch(
    localQuery.value,
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

const totalPages = computed(() => Math.ceil(total.value / limit.value));
const pageNumbers = computed(() => {
  const pages = [];
  const total = totalPages.value;
  const current = page.value;
  if (total <= 5) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else if (current <= 3) {
    for (let i = 1; i <= 5; i++) pages.push(i);
  } else if (current >= total - 2) {
    for (let i = total - 4; i <= total; i++) pages.push(i);
  } else {
    for (let i = current - 2; i <= current + 2; i++) pages.push(i);
  }
  return pages;
});

function runSearch() {
  search.performSearch(
    localQuery.value,
    'all',
    page.value,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

onMounted(() => {
  runSearch();
});

function onQueryChange() {
  search.performSearch(
    localQuery.value,
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

function onClasificacionChange() {
  search.performSearch(
    localQuery.value,
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

function onOrderByChange() {
  search.performSearch(
    localQuery.value,
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

function onOrderDirChange() {
  search.performSearch(
    localQuery.value,
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

function onLimitChange(e: Event) {
  const newLimit = parseInt((e.target as HTMLSelectElement).value, 10);
  search.performSearch(
    localQuery.value,
    'all',
    1,
    newLimit,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

function changePage(newPage: number) {
  search.performSearch(
    localQuery.value,
    'all',
    newPage,
    limit.value,
    localClasificacion.value,
    localOrderBy.value,
    localOrderDir.value,
  );
}

async function openLyrics(songId: number) {
  selectedSongId.value = songId;
  loadingLyrics.value = true;
  try {
    const data = await apiService.getSongDetail(songId);
    selectedSongData.value = data;
    selectedLyrics.value = data?.lyrics ?? '';
  } catch {
    selectedLyrics.value = 'Error al cargar la letra.';
  } finally {
    loadingLyrics.value = false;
  }
}

function labelText(clas: string): string {
  return (
    {
      ESPAÑOL_ESTANDAR: 'Estándar',
      ESPAÑOL_REGIONAL: 'Regional',
      LENGUA_INDIGENA: 'Indígena',
    }[clas] ?? clas
  );
}

function badgeClass(clas: string): string {
  return (
    {
      ESPAÑOL_ESTANDAR: 'badge-estandar',
      ESPAÑOL_REGIONAL: 'badge-regional',
      LENGUA_INDIGENA: 'badge-indigena',
    }[clas] ?? 'badge-estandar'
  );
}
</script>

<style scoped>
.canciones__masthead {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: var(--space-5);
  padding: var(--space-5) 0 var(--space-6);
  border-bottom: var(--hairline);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.canciones__title {
  font-family: var(--font-display);
  font-size: var(--font-size-3xl);
  font-weight: 400;
  font-variation-settings: 'opsz' 144, 'SOFT' 30, 'WONK' 0;
  color: var(--color-text);
  margin: var(--space-1) 0 0;
  line-height: 0.95;
  letter-spacing: var(--tracking-tight);
}

.canciones__total {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-1);
}

.canciones__total-num {
  font-size: var(--font-size-3xl);
  font-weight: 500;
  color: var(--color-text);
  line-height: 1;
  font-variation-settings: 'opsz' 144;
}

.canciones__total-label {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.canciones__controls {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: var(--space-5);
  padding: var(--space-5) 0;
  margin-bottom: var(--space-5);
  border-top: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
}

.canciones__select-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.canciones__select-label {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.canciones__select,
.canciones__input {
  background: transparent;
  border: none;
  border-bottom: var(--hairline);
  padding: var(--space-2) 0;
  font-family: var(--font-body);
  font-size: var(--font-size-md);
  color: var(--color-text);
  cursor: pointer;
  min-height: var(--tap-target-min);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%231a1612'%3E%3Cpath d='M4 6l4 4 4-4' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0 center;
  background-size: 14px;
  transition: border-color var(--transition-fast);
  width: 100%;
}

.canciones__input {
  background-image: none;
  cursor: text;
}

.canciones__select:hover,
.canciones__input:hover {
  border-bottom-color: var(--color-border-strong);
}

.canciones__select:focus,
.canciones__input:focus {
  outline: none;
  border-bottom-color: var(--color-brand);
  border-bottom-width: 2px;
  padding-bottom: calc(var(--space-2) - 1px);
}

@media (max-width: 768px) {
  .canciones__controls {
    grid-template-columns: 1fr;
  }
}

.table-cell-muted {
  color: var(--color-text-muted);
}

.sortable-th[role='button'] {
  cursor: pointer;
  user-select: none;
}

.sortable-th {
  white-space: nowrap;
}

.sortable-th:hover .sortable-th__label {
  color: var(--color-brand);
}

.sortable-th--active .sortable-th__label {
  color: var(--color-brand);
}

.sortable-th__arrow {
  margin-left: 4px;
  font-size: 0.7em;
  color: var(--color-brand);
}
</style>
