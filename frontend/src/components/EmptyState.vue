<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string
    description?: string
  }>(),
  {
    label: 'Sin datos para los filtros seleccionados',
    description: '',
  },
)
</script>

<template>
  <div class="empty-state" role="status" aria-live="polite">
    <p class="empty-state__label">{{ label }}</p>
    <p v-if="description" class="empty-state__description">{{ description }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-text-muted);
  text-align: center;
  min-height: 8rem;
}
.empty-state__label {
  font-size: var(--font-size-md);
  margin: 0;
  color: var(--color-text-secondary);
  font-weight: 500;
}
.empty-state__description {
  font-size: var(--font-size-sm);
  margin-top: var(--space-2);
  max-width: 32rem;
}
</style>
