<template>
  <div class="word-cloud" ref="rootEl">
    <header v-if="!loading && !error" class="word-cloud__header">
      <span class="eyebrow">Vocabulario recurrente</span>
      <p class="word-cloud__caption">
        Top {{ topWords.length }} palabras más frecuentes del cuerpo de la letra.
        Tamaño = frecuencia logarítmica.
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
    <div v-else class="word-cloud__canvas" ref="canvasContainer">
      <svg
        :viewBox="`0 0 ${baseWidth} ${baseHeight}`"
        :preserveAspectRatio="preserveAspect"
        class="word-cloud__svg"
        role="img"
        aria-label="Nube de palabras frecuentes en las canciones"
      >
        <g v-for="(word, index) in cloudLayout" :key="index">
          <text
            :x="word.x"
            :y="word.y"
            :font-size="word.fontSize"
            :fill="word.color"
            text-anchor="middle"
            dominant-baseline="middle"
            class="word-cloud__text"
            :style="{ fontWeight: word.weight, fontFamily: word.fontFamily }"
          >
            {{ word.text }}
          </text>
        </g>
      </svg>
    </div>
    <div v-if="!loading && !error" class="word-cloud__stats">
      <span class="eyebrow">Vocabulario</span>
      <span class="word-cloud__stats-value mono">{{ topWords.length }}</span>
      <span>palabras únicas mostradas</span>
      <span class="word-cloud__stats-sep" aria-hidden="true">·</span>
      <span class="word-cloud__stats-value mono">{{ totalWords.toLocaleString() }}</span>
      <span>apariciones totales en el corpus</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Responsive word cloud.
 *
 * The SVG viewBox tracks the canvas container's actual pixel size,
 * re-packed on every resize (debounced). Font sizes scale with the
 * container's shorter dimension so the cloud always fills the
 * available space — no letterboxing, no shrinking.
 *
 * The packing algorithm distributes words across the full viewBox:
 *   1. Top 6 hero words are seeded at 60° intervals on a ring at
 *      0.28 × min(W,H) from center, so the biggest, most weighty
 *      words claim distinct sectors.
 *   2. The remaining 34 hero words and the medium/small words spiral
 *      outward from the center (or from their sector anchor) with
 *      a wide step (22 / 18 radial, 0.42 rad angular) so consecutive
 *      words are placed meaningfully apart and the cloud fills the
 *      whole canvas instead of clustering in the middle.
 *
 * Stop words are excluded. Metadata (Dura:, Tema:, Personajes:) is
 * already stripped by the backend's cleanLyrics.
 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { apiService } from '@/services/api';
import { useFiltersStore } from '@/stores/filters';
import { packWordCloud, type WordItem, type LayoutWord } from '@/utils/wordCloudLayout';
import ChartInfoButton from '@/components/ChartInfoButton.vue';
import { chartInfo } from '@/config/chartInfo';

// (Frontend stop-word set removed in commit 5 — the backend is the
// single source of truth. See handlers/stats.go spanishStopWords
// + the LOWER(TRIM(...)) and < 2 char filters in GetWordCloud.)

const rootEl = ref<HTMLElement | null>(null);
const canvasContainer = ref<HTMLElement | null>(null);
const words = ref<WordItem[]>([]);
const totalWords = ref<number>(0);
const loading = ref(true);
const error = ref<string | null>(null);

const filters = useFiltersStore();
let abortController: AbortController | null = null;

// The container's actual pixel size. The SVG's viewBox tracks this so
// the cloud always fills the available space without letterboxing.
const containerSize = ref({ width: 1000, height: 500 });

// Reference dimensions the algorithm was tuned for. Used to scale font
// sizes and the tail band for smaller / larger viewBoxes.
const REF_W = 1600;
const REF_H = 900;

// Aspect-ratio policy: when the container is much wider than 16:9, we
// preserve the viewBox to match exactly and letterbox on the SVG side
// (preserveAspectRatio="xMidYMid meet"). This keeps the layout stable
// during browser zoom and high-DPI scaling.
const preserveAspect = 'xMidYMid meet';

const baseWidth = computed(() => Math.max(200, Math.round(containerSize.value.width)));
const baseHeight = computed(() => Math.max(120, Math.round(containerSize.value.height)));

// Scale factor for font sizes and grid spacing, derived from the
// container's shorter dimension. Keeps the visual density the same
// regardless of viewport size.
const fontScale = computed(() =>
  Math.max(0.45, Math.min(baseWidth.value / REF_W, baseHeight.value / REF_H)),
);

const palette = [
  '#1a1612', '#751428', '#c5a46c', '#c97a4a', '#6b8068', '#2c4a6e',
  '#9a2a2a', '#7c3aed', '#1d4ed8', '#047857', '#d97706', '#be185d',
  '#4a4239', '#8a7f6e', '#a16207', '#3a3128',
];

/**
 * Tighter filter: the backend already does the heavy normalization
 * (lowercase, drop < 2-char, drop stop-words, drop metadata) and
 * returns the top-N by frequency. We just sort. The previous local
 * stop-word set was a redundant duplicate of the backend's list
 * and was removed in commit 5 (reviewer feedback 01/jul/2026) so
 * the front and back stop at the same definition.
 */
const topWords = computed(() => {
  return [...words.value].sort((a, b) => b.size - a.size);
});

/**
 * Layout pass — delegates to the pure `packWordCloud` utility.
 * See `frontend/src/utils/wordCloudLayout.ts` for the algorithm.
 */
const cloudLayout = computed<LayoutWord[]>(() => {
  return packWordCloud(topWords.value, baseWidth.value, baseHeight.value, {
    palette,
    fontScale: fontScale.value,
  });
});

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

let resizeObserver: ResizeObserver | null = null;
let resizeDebounceTimer: ReturnType<typeof setTimeout> | null = null;

function handleResize() {
  if (!canvasContainer.value) return;
  const rect = canvasContainer.value.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return;
  // Debounce so we don't re-pack hundreds of times during a window
  // drag. The cloud re-packs at most every 120 ms.
  if (resizeDebounceTimer) clearTimeout(resizeDebounceTimer);
  resizeDebounceTimer = setTimeout(() => {
    const next = { width: rect.width, height: rect.height };
    if (
      Math.abs(next.width - containerSize.value.width) > 1 ||
      Math.abs(next.height - containerSize.value.height) > 1
    ) {
      containerSize.value = next;
    }
  }, 120);
}

onMounted(async () => {
  await nextTick();
  // Initial measurement from the actual DOM.
  if (canvasContainer.value) {
    const rect = canvasContainer.value.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      containerSize.value = { width: rect.width, height: rect.height };
    }
  }
  fetchWordCloud();
  // ResizeObserver gives us pixel-accurate dimensions for any container
  // size change (window resize, sidebar collapse, mobile rotate, etc.).
  if (canvasContainer.value && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(canvasContainer.value);
  }
  // Window resize as a fallback (older browsers without RO, e.g. older Safari).
  window.addEventListener('resize', handleResize, { passive: true });
});

onUnmounted(() => {
  abortController?.abort();
  resizeObserver?.disconnect();
  window.removeEventListener('resize', handleResize);
  if (resizeDebounceTimer) clearTimeout(resizeDebounceTimer);
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

/* The canvas has no fixed height: the SVG inside fills 100% width
   and gets a height derived from the viewBox via preserveAspectRatio.
   Combined with the dynamic viewBox (= the container's pixel size),
   the cloud is sized to whatever space the dashboard gives it. */
.word-cloud__canvas {
  width: 100%;
  display: block;
}

.word-cloud__svg {
  display: block;
  width: 100%;
  height: auto;
  /* No min-height: we want the SVG to shrink/grow with its parent.
     A min-height would defeat the responsiveness the user asked for. */
}

.word-cloud__text {
  cursor: default;
  transition: opacity var(--transition-fast);
  user-select: none;
}

.word-cloud__text:hover {
  opacity: 0.55;
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
