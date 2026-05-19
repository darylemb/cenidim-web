<template>
  <Teleport to="body">
    <div v-if="song" class="lyrics-modal-overlay" @click="$emit('close')">
      <div class="lyrics-modal" @click.stop">
        <button class="close-modal" @click="$emit('close')">&times;</button>
        <div class="lyrics-content">
          <h3>{{ song.title }}</h3>
          <p class="album-info">{{ song.album }} ({{ song.year }})</p>
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
defineProps<{
  song: { title: string; album: string; year: string } | null
  lyrics: string
  loading: boolean
}>()

defineEmits<{ close: () => void }>()
</script>