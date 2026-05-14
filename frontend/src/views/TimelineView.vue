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
      <div class="timeline-track">
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
      </div>
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

let observer: IntersectionObserver | null = null;

onMounted(async () => {
  try {
    const data = await apiService.getTimeline();
    years.value = data.years;
    timeline.value = data.timeline;
    visibleYears.value = new Set(data.years);
    setupObserver();
  } catch (e) {
    console.error('Error loading timeline:', e);
  }
});

onUnmounted(() => {
  observer?.disconnect();
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
  return timeline.value[year] ?? [];
}

async function onSongSelect(event: Event, year: string) {
  const songId = (event.target as HTMLSelectElement).value;
  if (!songId) return;
  const song = timeline.value[year]?.find((s) => s.id === parseInt(songId));
  selectedSong.value = song ?? null;
  loadingLyrics.value = true;
  try {
    const data = await apiService.getSongDetail(parseInt(songId));
    lyrics.value = data?.lyrics ?? '';
  } catch {
    lyrics.value = 'Error al cargar la letra.';
  } finally {
    loadingLyrics.value = false;
  }
}
</script>
