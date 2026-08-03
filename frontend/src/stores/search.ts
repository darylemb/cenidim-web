import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Song } from '@/types';
import { apiService } from '@/services/api';

export const useSearchStore = defineStore('search', () => {
  const query = ref('');
  const field = ref<'all' | 'title' | 'album' | 'lyrics'>('all');
  const clasificacion = ref('');
  const orderBy = ref<string>('id');
  const orderDir = ref<'asc' | 'desc'>('asc');
  const results = ref<Song[]>([]);
  const total = ref(0);
  const page = ref(1);
  const limit = ref(20);
  const loading = ref(false);

  const hasResults = computed(() => results.value.length > 0);
  const isLoading = computed(() => loading.value);
  const totalPages = computed(() => Math.ceil(total.value / limit.value));

  async function performSearch(
    searchTerm?: string,
    searchField?: string,
    targetPage = 1,
    targetLimit = 20,
    targetClasificacion = '',
    targetOrderBy: string = 'id',
    targetOrderDir: 'asc' | 'desc' = 'asc'
  ) {
    loading.value = true;
    page.value = targetPage;
    limit.value = targetLimit;
    orderBy.value = targetOrderBy as typeof orderBy.value;
    orderDir.value = targetOrderDir as typeof orderDir.value;

    if (searchTerm !== undefined) query.value = searchTerm;
    if (searchField !== undefined) field.value = searchField as typeof field.value;
    if (targetClasificacion !== undefined) clasificacion.value = targetClasificacion;

    try {
      const data = await apiService.searchSongs(
        query.value,
        field.value,
        targetPage,
        targetLimit,
        clasificacion.value,
        targetOrderBy,
        targetOrderDir
      );
      results.value = data.results ?? [];
      total.value = data.total ?? 0;
    } catch {
      results.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  function resetSearch() {
    query.value = '';
    field.value = 'all';
    clasificacion.value = '';
    orderBy.value = 'id';
    orderDir.value = 'asc';
    performSearch('', 'all', 1, limit.value, '', 'id', 'asc');
  }

  return {
    query,
    field,
    clasificacion,
    orderBy,
    orderDir,
    results,
    total,
    page,
    limit,
    loading,
    hasResults,
    isLoading,
    totalPages,
    performSearch,
    resetSearch,
  };
});
