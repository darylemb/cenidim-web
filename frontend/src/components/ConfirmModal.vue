<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="admin-confirm modal-content" @click.stop>
      <p>{{ message }}</p>
      <div class="admin-confirm-actions">
        <button class="btn-secondary" @click="$emit('cancel')">Cancelar</button>
        <button class="btn-danger" :disabled="loading" @click="$emit('confirm')">
          {{ loading ? 'Eliminando...' : 'Eliminar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string;
  loading: boolean;
}>();

defineEmits<{ confirm: () => void; cancel: () => void }>();
</script>
