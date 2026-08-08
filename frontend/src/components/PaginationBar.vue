<template>
  <div v-if="total > 0" class="pagination-container">
    <div class="pagination-info">
      Mostrando <strong>{{ shown }}</strong> de <strong>{{ total }}</strong> resultados
    </div>
    <div class="pagination-controls">
      <button class="pagination-btn" :disabled="page === 1" @click="$emit('change', page - 1)">
        &laquo; Anterior
      </button>
      <div class="pagination-pages">
        <button
          v-for="p in pageNumbers"
          :key="p"
          :class="['page-num', { active: p === page }]"
          @click="$emit('change', p)"
        >
          {{ p }}
        </button>
      </div>
      <button
        class="pagination-btn"
        :disabled="page === totalPages"
        @click="$emit('change', page + 1)"
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
</template>

<script setup lang="ts">
/**
 * Shared pagination bar: "Mostrando X de Y resultados", numbered page
 * buttons and a per-page selector. Used by the catalog table
 * (CancionesView) and the admin Canciones tab (AdminPanel).
 *
 * Emits `change(page)` when the user picks a page, and `limit` (a
 * number) when the per-page selector changes. The parent owns the
 * fetch, so it can reuse the same store/endpoint from either view.
 */
import { computed } from 'vue';

const props = defineProps<{
  page: number;
  limit: number;
  total: number;
  /** Number of rows currently rendered on this page. */
  shown: number;
}>();

const emit = defineEmits<{
  // eslint-disable-next-line no-unused-vars
  (e: 'change', page: number): void;
  // eslint-disable-next-line no-unused-vars
  (e: 'limit', limit: number): void;
}>();

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)));

// Sliding window of up to 5 page numbers around the current page.
const pageNumbers = computed(() => {
  const total = totalPages.value;
  const current = props.page;
  if (total <= 5) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  if (current <= 3) return [1, 2, 3, 4, 5];
  if (current >= total - 2) {
    return [total - 4, total - 3, total - 2, total - 1, total];
  }
  return [current - 2, current - 1, current, current + 1, current + 2];
});

function onLimitChange(e: Event) {
  const next = Number((e.target as HTMLSelectElement).value);
  if (next > 0) emit('limit', next);
}
</script>

<style scoped>
.pagination-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-top: var(--space-6);
  padding: var(--space-4) 0;
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
}

.pagination-info {
  color: var(--color-text-secondary);
}

.pagination-info strong {
  color: var(--color-text);
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.pagination-btn {
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--border-light);
  background: var(--color-panel);
  color: var(--color-text);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--color-brand);
}

.pagination-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.pagination-pages {
  display: flex;
  gap: var(--space-1);
}

.page-num {
  min-width: 2.2rem;
  padding: 0.5rem 0.6rem;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.page-num:hover {
  border-color: var(--border-light);
  color: var(--color-text);
}

.page-num.active {
  background: var(--color-brand);
  color: var(--color-text-on-brand, #fff);
  font-weight: 600;
}

.pagination-limit select {
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--border-light);
  background: var(--color-panel);
  color: var(--color-text);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
</style>
