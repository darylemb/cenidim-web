<script setup lang="ts">
/**
 * ChartInfoButton renders a small ⓘ that pops over a definition
 * dialog when clicked/focused. The dashboard uses it for each
 * non-trivial chart so reviewers (and reviewers' reviewers) can
 * understand what the visualization measures without leaving the
 * page.
 *
 * The dialog is a native <details> for accessibility (keyboard
 * open/close, screen reader discoverable) and styled to look like
 * a popover.
 */
import { ref } from 'vue'

defineProps<{
  info: string
}>()

const open = ref(false)
function toggle() {
  open.value = !open.value
}
</script>

<template>
  <button
    type="button"
    class="chart-info-btn"
    :aria-expanded="open"
    :aria-label="'¿Qué significa este gráfico?'"
    @click="toggle"
  >
    <span aria-hidden="true">ⓘ</span>
  </button>
  <div v-if="open" class="chart-info-popover" role="tooltip">
    <p>{{ info }}</p>
    <button
      type="button"
      class="chart-info-close"
      aria-label="Cerrar"
      @click="open = false"
    >
      ×
    </button>
  </div>
</template>

<style scoped>
.chart-info-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  margin-left: var(--space-1);
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  line-height: 1;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.chart-info-btn:hover,
.chart-info-btn:focus-visible {
  background: var(--color-brand);
  color: var(--color-text-inverse);
  border-color: var(--color-brand);
}
.chart-info-btn:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
}
.chart-info-popover {
  margin-top: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-soft);
  border: var(--hairline-soft);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  position: relative;
}
.chart-info-popover p {
  margin: 0;
  text-wrap: pretty;
}
.chart-info-close {
  position: absolute;
  top: var(--space-1);
  right: var(--space-2);
  background: none;
  border: none;
  font-size: 1.1rem;
  line-height: 1;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0 var(--space-1);
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
}
.chart-info-close:hover {
  color: var(--color-text);
}
</style>
