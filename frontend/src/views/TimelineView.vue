<template>
  <div class="content-area">
    <div class="page-header-flex">
      <h2 class="page-title">Cronología Musical</h2>
      <div class="total-indicator">
        <strong>{{ years.length }}</strong> años registrados
      </div>
    </div>

    <div class="timeline-intro">
      <p>Explora el archivo sonoro por año. Selecciona una canción para ver su letra.</p>
    </div>

    <div class="timeline-container" ref="timelineRef">
      <TransitionGroup name="timeline-item" tag="div" class="timeline-track">
        <div
          v-for="(year, index) in years"
          :key="year"
          :class="['timeline-year-item', { visible: visibleYears.has(year) }]"
          :data-year="year"
          :style="{ '--year-index': index, '--animation-delay': `${index * 50}ms` }"
        >
          <div v-if="index < years.length - 1" class="timeline-connector">
            <div class="connector-line"></div>
            <div class="connector-dot"></div>
          </div>

          <div class="timeline-year-node">
            <div class="node-circle">
              <span class="node-year">{{ year }}</span>
            </div>
            <div class="node-label">{{ year }}</div>
          </div>

          <div class="timeline-year-badge">
            <span class="badge-count">{{ getSongsInYear(year).length }}</span>
            <span class="badge-label">canciones</span>
          </div>

          <div class="timeline-song-selector">
            <select class="timeline-select" @change="onSongSelect($event, year)">
              <option value="" disabled>Seleccionar pista</option>
              <option v-for="song in getSongsInYear(year)" :key="song.id" :value="song.id">
                {{ song.title.length > 35 ? song.title.substring(0, 32) + '...' : song.title }}
              </option>
            </select>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <div class="timeline-summary">
      <div class="summary-track">
        <div
          v-for="year in years"
          :key="year"
          class="summary-segment"
          :style="{ '--segment-width': `${Math.max(getSongsInYear(year).length * 3, 10)}%` }"
          :title="`${year}: ${getSongsInYear(year).length} canciones`"
        ></div>
      </div>
    </div>

    <LyricModal
      v-if="selectedSong"
      :song="selectedSong"
      :lyrics="lyrics"
      :loading="loadingLyrics"
      @close="selectedSong = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { apiService } from '@/services/api';
import type { Song } from '@/types';
import LyricModal from '@/components/LyricModal.vue';

const years = ref<string[]>([]);
const timeline = ref<Record<string, Song[]>>({});
const selectedSong = ref<Song | null>(null);
const lyrics = ref('');
const loadingLyrics = ref(false);
const visibleYears = ref(new Set<string>());
const timelineRef = ref<HTMLElement | null>(null);
const timelineController = ref<AbortController | null>(null);

let observer: IntersectionObserver | null = null;
let _lyricsSeq = 0;
let _lyricsController: AbortController | null = null;

onMounted(async () => {
  timelineController.value = new AbortController();
  try {
    const data = await apiService.getTimeline(timelineController.value.signal);
    const validYears = data.years.filter((y: string) => y !== 's/d');
    years.value = validYears;
    timeline.value = Object.fromEntries(
      Object.entries(data.timeline).filter(([key]) => key !== 's/d')
    );
    visibleYears.value = new Set(validYears);
    setupObserver();
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') return;
    console.error('Error loading timeline:', e);
  }
});

onUnmounted(() => {
  observer?.disconnect();
  timelineController.value?.abort();
});

function setupObserver() {
  if (!timelineRef.value) return;
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const year = (entry.target as HTMLElement).dataset.year;
          if (year) visibleYears.value.add(year);
        }
      });
    },
    { root: timelineRef.value, rootMargin: '100px', threshold: 0.1 }
  );
  const els = timelineRef.value.querySelectorAll('.timeline-year-item');
  els.forEach((el) => observer!.observe(el));
}

function getSongsInYear(year: string): Song[] {
  return (timeline.value[year] ?? []).filter((s) => s.year && s.year !== 's/d');
}

async function onSongSelect(event: Event, year: string) {
  const songId = (event.target as HTMLSelectElement).value;
  if (!songId) return;
  const song = timeline.value[year]?.find((s) => s.id === parseInt(songId));
  selectedSong.value = song ?? null;
  lyrics.value = '';
  const seq = ++_lyricsSeq;
  loadingLyrics.value = true;
  _lyricsController?.abort();
  _lyricsController = new AbortController();
  try {
    const data = await apiService.getSongDetail(parseInt(songId), _lyricsController.signal);
    if (seq !== _lyricsSeq) return;
    lyrics.value = data?.lyrics ?? '';
  } catch {
    if (seq !== _lyricsSeq) return;
    lyrics.value = 'Error al cargar la letra.';
  } finally {
    if (seq === _lyricsSeq) loadingLyrics.value = false;
  }
}
</script>

<style scoped>
.timeline-year-item {
  opacity: 0;
  transform: translateX(20px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.timeline-year-item.visible {
  opacity: 1;
  transform: translateX(0);
}

.timeline-song-selector {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.timeline-year-item.visible .timeline-song-selector {
  opacity: 1;
  transform: translateY(0);
}

.timeline-item-enter-active {
  transition: all 0.5s ease-out;
}

.timeline-item-leave-active {
  transition: all 0.3s ease-in;
  position: absolute;
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.timeline-item-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.timeline-item-move {
  transition: transform 0.5s ease;
}
</style>