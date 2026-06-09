<script setup lang="ts">
import { useFiltersStore } from '@/stores/filters'
import { useRouter } from 'vue-router'
import { swatchFor } from '@/config/themes'

const emit = defineEmits<{ clear: []; remove: [key: string] }>()

const filters = useFiltersStore()
const router = useRouter()

function handleRemove(key: string) {
  emit('remove', key)
  const chip = filters.active.find((c) => c.key === key)
  chip?.onRemove()
  router.replace({ query: filters.toQuery() }).catch(() => {})
}

function handleClear() {
  emit('clear')
  filters.clear()
  router.replace({ query: filters.toQuery() }).catch(() => {})
}

function swatch(key: string): string {
  // Strip the 'theme:' prefix that the store uses to namespace the chip key.
  const t = key.startsWith('theme:') ? key.slice('theme:'.length) : ''
  return swatchFor(t)
}
</script>

<template>
  <div v-if="filters.active.length > 0" class="active-filters" role="list" aria-label="Filtros activos">
    <span class="active-filters__label eyebrow">Filtros aplicados</span>
    <div class="active-filters__chips">
      <button
        v-for="chip in filters.active"
        :key="chip.key"
        type="button"
        class="active-chip"
        :aria-label="`Quitar filtro: ${chip.label}`"
        @click="handleRemove(chip.key)"
      >
        <span
          v-if="chip.key.startsWith('theme:') && chip.key !== 'theme:__none__'"
          class="active-chip__dot"
          :style="{ background: swatch(chip.key) }"
          aria-hidden="true"
        ></span>
        <span class="active-chip__label">{{ chip.label }}</span>
        <svg class="active-chip__close" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M3 3 L13 13 M13 3 L3 13" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" />
        </svg>
      </button>
      <button
        type="button"
        class="active-filters__clear"
        @click="handleClear"
      >
        Limpiar todo
      </button>
    </div>
  </div>
</template>

<style scoped>
.active-filters {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  margin-bottom: var(--space-5);
  border-top: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
  flex-wrap: wrap;
}

.active-filters__label {
  flex-shrink: 0;
}

.active-filters__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: center;
}

.active-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2) var(--space-1) var(--space-3);
  background: var(--color-bg);
  border: var(--hairline);
  border-radius: var(--radius-pill);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 32px;
}

.active-chip:hover {
  background: var(--color-brand);
  color: var(--color-text-inverse);
  border-color: var(--color-brand);
}

.active-chip:hover .active-chip__close {
  color: var(--color-text-inverse);
}

.active-chip__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.active-chip__label {
  font-variant-numeric: tabular-nums;
}

.active-chip__close {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--color-text-muted);
  transition: color var(--transition-fast);
}

.active-filters__clear {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  cursor: pointer;
  padding: var(--space-2) var(--space-3);
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-thickness: 1px;
  transition: color var(--transition-fast);
  min-height: 32px;
}

.active-filters__clear:hover {
  color: var(--color-brand);
}
</style>
