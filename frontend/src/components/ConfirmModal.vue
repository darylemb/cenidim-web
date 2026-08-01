<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="admin-confirm modal-content" role="alertdialog" :aria-labelledby="titleId" @click.stop>
      <h3 v-if="title" :id="titleId" class="admin-confirm-title">{{ title }}</h3>
      <p class="admin-confirm-message">{{ message }}</p>
      <div class="admin-confirm-actions">
        <button class="btn-secondary" @click="$emit('cancel')">
          {{ cancelLabel }}
        </button>
        <button :class="confirmButtonClass" :disabled="loading" @click="$emit('confirm')">
          {{ loading ? loadingLabel : confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'danger' | 'warning' | 'primary';

const props = withDefaults(
  defineProps<{
    message: string;
    loading: boolean;
    title?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    loadingLabel?: string;
    variant?: Variant;
  }>(),
  {
    title: '',
    confirmLabel: 'Confirmar',
    cancelLabel: 'Cancelar',
    loadingLabel: 'Procesando...',
    variant: 'danger',
  }
);

defineEmits<{ confirm: []; cancel: [] }>();

const titleId = computed(() => `confirm-title-${Math.random().toString(36).slice(2, 9)}`);

const confirmButtonClass = computed(() => {
  switch (props.variant) {
    case 'warning':
      return 'btn-warning';
    case 'primary':
      return 'btn-primary';
    case 'danger':
    default:
      return 'btn-danger';
  }
});
</script>

<style scoped>
.admin-confirm {
  max-width: 480px;
  padding: var(--space-5) var(--space-6);
}

.admin-confirm-title {
  font-family: var(--font-display, var(--font-body));
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.admin-confirm-message {
  color: var(--color-text);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  margin-bottom: var(--space-5);
}

.admin-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-warning {
  padding: var(--space-2) var(--space-4);
  border: 1px solid #b45309;
  background: #d97706;
  color: #fff;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  min-height: var(--tap-target-min);
  transition: var(--transition-fast);
}

.btn-warning:hover:not(:disabled) {
  background: #b45309;
}

.btn-warning:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
