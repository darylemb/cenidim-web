<template>
  <Teleport to="body">
    <div v-if="song" class="lyrics-modal-overlay" @click="$emit('close')">
      <div class="lyrics-modal" @click.stop>
        <button class="close-modal" @click="$emit('close')">&times;</button>
        <div class="lyrics-content">
          <h3>{{ song.title }}</h3>
          <p class="album-info">{{ song.album }} ({{ song.year }})</p>
          <div class="lyrics-meta">
            <ThemeBadge :theme="song.tema ?? ''" />
          </div>
          <hr />
          <div v-if="loading">
            <div class="loader small"></div>
          </div>
          <pre v-else>{{ lyrics || 'Letra no disponible' }}</pre>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import ThemeBadge from '@/components/ThemeBadge.vue'

defineProps<{
  song: {
    title: string
    album: string
    year: string
    tema?: string
  } | null
  lyrics: string
  loading: boolean
}>()

defineEmits<{ close: () => void }>()
</script>

<style scoped>
.lyrics-meta {
  margin: var(--space-2) 0 var(--space-4);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>