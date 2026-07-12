<script setup lang="ts">
import { computed } from 'vue'
import { themeSlug, swatchFor } from '@/config/themes'

const props = withDefaults(
  defineProps<{
    theme?: string
    label?: string
  }>(),
  { theme: '', label: '' },
)

const display = computed(() => {
  if (props.label) return props.label
  if (!props.theme) return 'Sin tema'
  return props.theme
})

const isUnclassified = computed(() => !props.theme)

const slug = computed(() => themeSlug(props.theme))

const swatch = computed(() => swatchFor(props.theme))
</script>

<template>
  <span
    class="theme-badge"
    :class="['theme-badge--' + slug, { 'theme-badge--unclassified': isUnclassified }]"
    :data-theme="props.theme || ''"
    role="status"
  >
    <span class="theme-badge__dot" aria-hidden="true" :style="{ background: swatch }" />
    {{ display }}
  </span>
</template>

<style scoped>
.theme-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-wide);
  line-height: 1;
  background: var(--color-bg-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
.theme-badge__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
.theme-badge--unclassified {
  color: var(--color-text-muted);
  font-style: italic;
}
</style>
