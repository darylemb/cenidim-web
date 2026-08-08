<template>
  <Teleport to="body">
    <div v-if="song" class="lyrics-modal-overlay" @click="$emit('close')">
      <div class="lyrics-modal" @click.stop>
        <button class="close-modal" @click="$emit('close')">&times;</button>
        <div class="lyrics-content">
          <h3>{{ song.title }}</h3>
          <p class="album-info">{{ song.album }}<template v-if="song.year"> · {{ song.year }}</template></p>
          <p v-if="song.interprete_principal" class="song-interpret">
            {{ song.interprete_principal }}
          </p>

          <div class="lyrics-meta">
            <ThemeBadge :theme="song.tema ?? ''" />
          </div>

          <dl v-if="showDetails && detailRows.length" class="song-ficha" aria-label="Ficha de la canción">
            <template v-for="row in detailRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>{{ row.value }}</dd>
            </template>
          </dl>

          <hr />
          <h4 class="lyrics-title">Letra</h4>
          <div v-if="loading">
            <div class="loader small"></div>
          </div>
          <pre v-else>{{ lyrics || 'Letra no disponible' }}</pre>

          <router-link
            :to="{ path: '/canciones', query: { query: song.title } }"
            class="lyrics-catalog-link"
            @click="$emit('close')"
          >
            Ver en el catálogo →
          </router-link>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ThemeBadge from '@/components/ThemeBadge.vue'

const props = defineProps<{
  song: {
    title: string
    album: string
    year: string
    tema?: string
    interprete_principal?: string
    interpretes_invitados?: string
    interprete_participante?: string
    soporte_fisico?: string
    editora?: string
    numero_catalogo?: string
    ciudad_edicion?: string
    pais_edicion?: string
    pistas?: string
    observaciones?: string
    filename?: string
    clasificacion?: string
  } | null
  lyrics: string
  loading: boolean
  /** When true, show the full "ficha" (metadata) above the lyrics.
   *  "Ver letra" passes false so it only shows the lyrics. */
  showDetails?: boolean
}>()

defineEmits<{ close: () => void }>()

// Show only the fields that actually have a value, so a non-technical
// reader sees the details without a wall of empty labels.
const detailRows = computed<Array<{ label: string; value: string }>>(() => {
  if (!props.song) return []
  const rows: Array<{ label: string; value: string }> = []
  const add = (label: string, value: string | undefined | null) => {
    const v = (value ?? '').trim()
    if (v) rows.push({ label, value: v })
  }
  add('Intérprete', props.song.interprete_principal)
  add('Intérpretes invitados', props.song.interpretes_invitados)
  add('Intérprete participante', props.song.interprete_participante)
  add('Soporte', props.song.soporte_fisico)
  add('Editora', props.song.editora)
  add('N° catálogo', props.song.numero_catalogo)
  add('Ciudad', props.song.ciudad_edicion)
  add('País', props.song.pais_edicion)
  add('Pistas', props.song.pistas)
  add('Observaciones', props.song.observaciones)
  return rows
})
</script>

<style scoped>
.lyrics-meta {
  margin: var(--space-2) 0 var(--space-4);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.song-interpret {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: var(--space-1) 0 0;
}

.lyrics-catalog-link {
  display: inline-block;
  margin-top: var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-brand);
  text-decoration: underline;
  text-underline-offset: 4px;
}

.song-ficha {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: var(--space-1) var(--space-4);
  margin: var(--space-4) 0;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-soft);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}

.song-ficha dt {
  font-weight: 600;
  color: var(--color-text-muted);
}

.song-ficha dd {
  margin: 0;
  color: var(--color-text);
}

.lyrics-title {
  font-family: var(--font-display);
  font-size: var(--font-size-md);
  font-weight: 600;
  margin: 0 0 var(--space-2);
}
</style>
