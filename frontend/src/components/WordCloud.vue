<template>
  <div class="word-cloud">
    <header v-if="!loading && !error" class="word-cloud__header">
      <span class="eyebrow">Vocabulario recurrente</span>
      <p class="word-cloud__caption">
        Top {{ visibleWords.length }} palabras más frecuentes del cuerpo de la letra.
        Las palabras más grandes son las que más se repiten.
        <ChartInfoButton :info="chartInfo.nubePalabras" />
      </p>
    </header>
    <div v-if="loading" class="word-cloud__state" aria-live="polite">
      <div class="word-cloud__spinner" aria-hidden="true"></div>
      <span>Cargando vocabulario…</span>
    </div>
    <div v-else-if="error" class="word-cloud__state word-cloud__state--error">
      {{ error }}
    </div>
    <div v-else class="word-cloud__chips" role="list">
      <span
        v-for="(word, index) in visibleWords"
        :key="index"
        role="listitem"
        class="word-chip"
        :style="chipStyle(word, index)"
      >
        {{ word.text }}
      </span>
    </div>
    <div v-if="!loading && !error" class="word-cloud__stats">
      <span class="eyebrow">Vocabulario</span>
      <span class="word-cloud__stats-value mono">{{ visibleWords.length }}</span>
      <span>palabras más frecuentes</span>
      <span class="word-cloud__stats-sep" aria-hidden="true">·</span>
      <span class="word-cloud__stats-value mono">{{ totalWords.toLocaleString() }}</span>
      <span>apariciones totales en el corpus</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Recurrent vocabulary as a responsive chip cloud.
 *
 * Unlike a packed/spiral SVG layout (which could leave words cramped,
 * truncated or tiny at 200 entries), the chips wrap in a flex layout:
 * no two chips can ever overlap or be cut off, and the font size of
 * each chip scales with the word's frequency so the most recurrent
 * words still read largest.
 *
 * Stop words are excluded. Metadata (Dura:, Tema:, Personajes:) is
 * already stripped by the backend's cleanLyrics.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { apiService } from '@/services/api';
import { useFiltersStore } from '@/stores/filters';
import ChartInfoButton from '@/components/ChartInfoButton.vue';
import { chartInfo } from '@/config/chartInfo';

interface WordItem {
  text: string;
  size: number;
}

// (Frontend stop-word set removed in commit 5 — the backend is the
// single source of truth. See handlers/stats.go spanishStopWords
// + the LOWER(TRIM(...)) and < 2 char filters in GetWordCloud.)

/** Cap shown chips: enough to read the corpus without an ocean of
 * 5px fragments. The backend may return up to 200 words. */
const MAX_CHIPS = 80;
/** Font-size bounds for a chip (px). */
const MIN_PX = 13;
const MAX_PX = 27;

const words = ref<WordItem[]>([]);
const totalWords = ref<number>(0);
const loading = ref(true);
const error = ref<string | null>(null);

const filters = useFiltersStore();
let abortController: AbortController | null = null;

// Light-theme palette: warm inks on the cream background.
const lightPalette = [
  '#1a1612', '#751428', '#c5a46c', '#c97a4a', '#6b8068', '#2c4a6e',
  '#9a2a2a', '#7c3aed', '#1d4ed8', '#047857', '#d97706', '#be185d',
  '#4a4239', '#8a7f6e', '#a16207', '#3a3128',
];

// Dark-theme palette: lighter/brighter inks that stay visible on the
// deep warm-brown background (dark inks would disappear).
const darkPalette = [
  '#f3ede0', '#c5a46c', '#e0a35e', '#8fbfa0', '#7fa3d8', '#e07b9a',
  '#d9a0c8', '#a0c86f', '#e0b6a0', '#c9a86c', '#9bb8d8', '#e08f6f',
  '#c5b89c', '#a8b8d0', '#d8b45a', '#b08fbf',
];

const palette = ref(lightPalette);
if (typeof window !== 'undefined' && window.matchMedia) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const apply = (dark: boolean) => {
    palette.value = dark ? darkPalette : lightPalette;
  };
  apply(mq.matches);
  mq.addEventListener?.('change', (e) => apply(e.matches));
}

/**
 * Tighter filter: the backend already does the heavy normalization
 * (lowercase, drop < 2-char, drop stop-words, drop metadata) and
 * returns the top-N by frequency. We just sort.
 */
const topWords = computed(() => {
  return [...words.value].sort((a, b) => b.size - a.size);
});

const visibleWords = computed(() => topWords.value.slice(0, MAX_CHIPS));

const maxSize = computed(() => topWords.value[0]?.size ?? 1);
const minSize = computed(() => topWords.value[topWords.value.length - 1]?.size ?? 1);

/**
 * Chip style: font size + weight + colour scale with the word's rank.
 * The alpha background tint reuses the same hex colour so chips read
 * as discrete pills in both light and dark themes.
 */
function chipStyle(word: WordItem, index: number): Record<string, string> {
  const normalized = (word.size - minSize.value) / (maxSize.value - minSize.value + 1);
  const eased = Math.pow(Math.max(0, Math.min(1, normalized)), 0.72);
  const fontSize = MIN_PX + eased * (MAX_PX - MIN_PX);
  const color = palette.value[index % palette.value.length];
  const weight = normalized > 0.74 ? 600 : normalized > 0.46 ? 500 : 400;
  return {
    fontSize: `${fontSize.toFixed(1)}px`,
    fontWeight: String(weight),
    color,
    backgroundColor: `${color}1f`,
    borderColor: `${color}55`,
  };
}

async function fetchWordCloud() {
  abortController?.abort();
  abortController = new AbortController();
  try {
    loading.value = true;
    error.value = null;
    const data = await apiService.getWordCloud(
      filters.queryString,
      abortController.signal,
    );
    words.value = data.words || [];
    totalWords.value = data.totalWords || 0;
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') return;
    error.value = e instanceof Error ? e.message : 'Unknown error';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchWordCloud();
});

onUnmounted(() => {
  abortController?.abort();
});

// React to filter changes. The store debounces year and q so this
// fires once per stable state.
watch(
  () => filters.queryString,
  () => {
    fetchWordCloud();
  },
);
</script>

<style scoped>
.word-cloud {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.word-cloud__state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-9) var(--space-4);
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  min-height: 280px;
}

.word-cloud__state--error {
  color: var(--color-danger);
  text-transform: none;
  letter-spacing: 0;
  font-size: var(--font-size-md);
}

.word-cloud__spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-brand);
  border-radius: 50%;
  animation: word-cloud-spin 0.9s linear infinite;
}

@keyframes word-cloud-spin {
  to { transform: rotate(360deg); }
}

/* Flex-wrap chips: words can never overlap or be cut off, and they
   reflow to any container width. */
.word-cloud__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2) var(--space-3);
  min-height: 280px;
  padding: var(--space-4);
  border: 1px solid var(--border-light);
  background: var(--color-panel-soft);
  border-radius: var(--radius-md);
}

.word-chip {
  display: inline-block;
  padding: 0.35em 0.7em;
  line-height: 1.2;
  border: 1px solid transparent;
  border-radius: 999px;
  font-family: var(--font-body);
  transition: opacity var(--transition-fast);
  cursor: default;
  user-select: none;
}

.word-chip:hover {
  opacity: 0.6;
}

.word-cloud__stats {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-top: var(--space-3);
  margin-top: var(--space-2);
  border-top: var(--hairline-soft);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.word-cloud__stats .eyebrow {
  margin-right: var(--space-1);
}

.word-cloud__stats-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
  font-weight: 500;
}

.word-cloud__stats-sep {
  color: var(--color-text-muted);
  margin: 0 var(--space-2);
}
</style>
