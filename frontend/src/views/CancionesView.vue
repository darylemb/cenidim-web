<template>
  <div class="content-area">
    <div class="page-header-flex">
      <h2 class="page-title">Canciones</h2>
      <div class="total-indicator">
        <strong>{{ total }}</strong> canciones encontradas
      </div>
    </div>

    <div class="filter-bar">
      <label for="clasificacion-filter" class="filter-label">Clasificación de lengua:</label>
      <select
        id="clasificacion-filter"
        v-model="localClasificacion"
        class="clasificacion-select"
        @change="onClasificacionChange"
      >
        <option value="">Todas las clasificaciones</option>
        <option value="ESPAÑOL_ESTANDAR">Español Estándar</option>
        <option value="ESPAÑOL_REGIONAL">Español Regional</option>
        <option value="LENGUA_INDIGENA">Lengua Indígena</option>
      </select>

      <label for="order-by-filter" class="filter-label">Ordenar por:</label>
      <select
        id="order-by-filter"
        v-model="localOrderBy"
        class="clasificacion-select"
        @change="onOrderByChange"
      >
        <option value="id">ID</option>
        <option value="clave">Clave</option>
        <option value="title">Pista</option>
        <option value="album">Álbum</option>
        <option value="year">Año</option>
        <option value="filename">Archivo</option>
        <option value="clasificacion">Clasificación</option>
      </select>

      <select v-model="localOrderDir" class="clasificacion-select" @change="onOrderDirChange">
        <option value="asc">Ascendente</option>
        <option value="desc">Descendente</option>
      </select>
    </div>

    <div class="results-table-container">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>Buscando en el archivo del CENIDIM...</p>
      </div>
      <div class="table-scroll-wrapper">
        <table :class="['results-table', 'results-table--wide', { loadingopacity: loading }]">
          <thead>
            <tr>
              <th>Clave</th>
              <th>Pista</th>
              <th>Álbum</th>
              <th>Subtítulo</th>
              <th>Intérprete Principal</th>
              <th>Intérpretes Invitados</th>
              <th>Intérprete Participante</th>
              <th>Soporte Físico</th>
              <th>Editora</th>
              <th>N° Catálogo</th>
              <th>Ciudad</th>
              <th>País</th>
              <th>Año</th>
              <th>Pistas</th>
              <th>Observaciones</th>
              <th>Archivo</th>
              <th>Clasificación</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="song in results" :key="song.id">
              <td data-label="Clave">{{ song.fonograma_id }}</td>
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
                <span class="table-cell-text" :title="song.pais_edicion">{{
                  song.pais_edicion
                }}</span>
              </td>
              <td data-label="Año" class="table-cell-truncate">
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
              <td data-label="Archivo" class="table-cell-truncate">
                <span class="table-cell-text" :title="song.filename">{{ song.filename }}</span>
              </td>
              <td data-label="Clasificación">
                <span :class="['clasificacion-badge', badgeClass(song.clasificacion)]">
                  {{ labelText(song.clasificacion) }}
                </span>
              </td>
              <td data-label="Acción">
                <button v-if="song.filename" class="action-btn" @click="openLyrics(song.id)">
                  Ver Letra
                </button>
                <span v-else>—</span>
              </td>
            </tr>
            <tr v-if="!loading && results.length === 0">
              <td colspan="18" style="text-align: center; padding: 4rem">
                <div class="no-results">
                  <span style="font-size: 2rem; display: block; margin-bottom: 1rem">🔍</span>
                  <p>No se encontraron resultados para su búsqueda.</p>
                  <button class="btn-reset" style="margin-top: 1rem" @click="onReset">
                    Mostrar todas
                  </button>
                </div>
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
import { ref, computed, onMounted } from 'vue';
import { useSearchStore } from '@/stores/search';
import { apiService } from '@/services/api';
import type { Song } from '@/types';
import LyricModal from '@/components/LyricModal.vue';
import { storeToRefs } from 'pinia';

const search = useSearchStore();
const { results, total, page, limit, clasificacion, orderBy, orderDir, loading } =
  storeToRefs(search);

const localClasificacion = ref('');
const localOrderBy = ref('id');
const localOrderDir = ref<'asc' | 'desc'>('asc');
const selectedSongId = ref<number | null>(null);
const selectedSongData = ref<Song | null>(null);
const selectedLyrics = ref('');
const loadingLyrics = ref(false);

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

onMounted(() => {
  localClasificacion.value = clasificacion.value;
  localOrderBy.value = orderBy.value;
  localOrderDir.value = orderDir.value;
  if (results.value.length === 0) {
    search.performSearch('', 'all', 1, 20);
  }
});

function onClasificacionChange() {
  search.performSearch(
    '',
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value as
      | 'id'
      | 'clave'
      | 'title'
      | 'album'
      | 'year'
      | 'filename'
      | 'clasificacion',
    localOrderDir.value
  );
}

function onOrderByChange() {
  search.performSearch(
    '',
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value as
      | 'id'
      | 'clave'
      | 'title'
      | 'album'
      | 'year'
      | 'filename'
      | 'clasificacion',
    localOrderDir.value
  );
}

function onOrderDirChange() {
  search.performSearch(
    '',
    'all',
    1,
    limit.value,
    localClasificacion.value,
    localOrderBy.value as
      | 'id'
      | 'clave'
      | 'title'
      | 'album'
      | 'year'
      | 'filename'
      | 'clasificacion',
    localOrderDir.value
  );
}

function onLimitChange(e: Event) {
  const newLimit = parseInt((e.target as HTMLSelectElement).value, 10);
  search.performSearch(
    '',
    'all',
    1,
    newLimit,
    localClasificacion.value,
    localOrderBy.value as
      | 'id'
      | 'clave'
      | 'title'
      | 'album'
      | 'year'
      | 'filename'
      | 'clasificacion',
    localOrderDir.value
  );
}

function changePage(newPage: number) {
  search.performSearch(
    '',
    'all',
    newPage,
    limit.value,
    localClasificacion.value,
    localOrderBy.value as
      | 'id'
      | 'clave'
      | 'title'
      | 'album'
      | 'year'
      | 'filename'
      | 'clasificacion',
    localOrderDir.value
  );
}

function onReset() {
  localClasificacion.value = '';
  localOrderBy.value = 'id';
  localOrderDir.value = 'asc';
  search.resetSearch();
}

async function openLyrics(songId: number) {
  selectedSongId.value = songId;
  loadingLyrics.value = true;
  try {
    const data = await apiService.getSongDetail(songId);
    selectedSongData.value = data;
    selectedLyrics.value = data.lyrics ?? '';
  } catch {
    selectedLyrics.value = 'Error al cargar la letra.';
  } finally {
    loadingLyrics.value = false;
  }
}

function labelText(clas: string): string {
  return (
    {
      ESPAÑOL_ESTANDAR: 'Español Estándar',
      ESPAÑOL_REGIONAL: 'Español Regional',
      LENGUA_INDIGENA: 'Lengua Indígena',
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
