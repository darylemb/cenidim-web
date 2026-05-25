<template>
  <div class="word-cloud-wrapper">
    <div class="word-cloud-container">
      <h3 class="word-cloud-title">Palabras en las canciones</h3>
      <div v-if="loading" class="word-cloud-loading">Cargando...</div>
      <div v-else-if="error" class="word-cloud-error">{{ error }}</div>
      <div v-else class="word-cloud-canvas" ref="canvasContainer">
        <svg viewBox="0 0 700 450" class="word-cloud-svg" preserveAspectRatio="xMidYMid meet">
          <g v-for="(word, index) in cloudLayout" :key="index">
            <text
              :x="word.x"
              :y="word.y"
              :font-size="word.fontSize"
              :fill="word.color"
              text-anchor="middle"
              dominant-baseline="middle"
              class="word-cloud-text"
              :style="{ fontWeight: word.weight }"
            >
              {{ word.text }}
            </text>
          </g>
        </svg>
      </div>
      <div class="word-cloud-stats">
        <span>{{ topWords.length }} palabras</span>
        <span v-if="totalWords"> • {{ totalWords.toLocaleString() }} palabras totales</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';

interface WordItem {
  text: string;
  size: number;
}

interface LayoutWord extends WordItem {
  x: number;
  y: number;
  fontSize: number;
  color: string;
  weight: string;
}

const words = ref<WordItem[]>([]);
const totalWords = ref<number>(0);
const loading = ref(true);
const error = ref<string | null>(null);

const svgWidth = 700;
const svgHeight = 450;

const palette = [
  '#1e3a5f', '#2d5a87', '#3d7ab3', '#5a9bd4', '#7ab8e8',
  '#9dd3f5', '#bce8fa', '#d6effc', '#c5a46c', '#751428',
  '#2563eb', '#059669', '#dc2626', '#7c3aed', '#ea580c',
];

const topWords = computed(() => {
  return words.value
    .filter(w => w.text.length >= 4)
    .sort((a, b) => b.size - a.size)
    .slice(0, 100);
});

interface Box {
  cx: number;
  cy: number;
  w: number;
  h: number;
}

function boxesOverlap(a: Box, b: Box, padding: number): boolean {
  return !(
    a.cx - a.w / 2 - padding > b.cx + b.w / 2 + padding ||
    a.cx + a.w / 2 + padding < b.cx - b.w / 2 - padding ||
    a.cy - a.h / 2 - padding > b.cy + b.h / 2 + padding ||
    a.cy + a.h / 2 + padding < b.cy - b.h / 2 - padding
  );
}

const cloudLayout = computed<LayoutWord[]>(() => {
  if (topWords.value.length === 0) return [];

  const sorted = [...topWords.value];
  const maxSize = sorted[0]?.size || 1;
  const minSize = sorted[sorted.length - 1]?.size || 1;

  const placed: Box[] = [];
  const result: LayoutWord[] = [];

  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;

  for (let i = 0; i < sorted.length; i++) {
    const word = sorted[i];
    const normalizedSize = (word.size - minSize) / (maxSize - minSize + 1);
    const fontSize = 10 + normalizedSize * 24;

    let bestDist = Infinity;

    for (let spiral = 0; spiral < 600; spiral++) {
      const angle = spiral * 0.4;
      const radius = 8 * Math.sqrt(spiral + 1);
      const testX = centerX + radius * Math.cos(angle);
      const testY = centerY + radius * Math.sin(angle) * 0.75;

      const wordWidth = word.text.length * fontSize * 0.5;
      const wordHeight = fontSize * 0.9;

      const box: Box = {
        cx: testX,
        cy: testY,
        w: wordWidth,
        h: wordHeight,
      };

      let overlaps = false;
      for (const p of placed) {
        if (boxesOverlap(box, p, 2)) {
          overlaps = true;
          break;
        }
      }

      if (!overlaps &&
          testX - wordWidth / 2 > 8 && testX + wordWidth / 2 < svgWidth - 8 &&
          testY - wordHeight / 2 > 15 && testY + wordHeight / 2 < svgHeight - 8) {

        placed.push(box);
        result.push({
          ...word,
          x: testX,
          y: testY + fontSize * 0.35,
          fontSize,
          color: palette[i % palette.length],
          weight: normalizedSize > 0.5 ? 'bold' : 'normal',
        });
        break;
      }

      const dist = Math.sqrt((testX - centerX) ** 2 + (testY - centerY) ** 2);
      if (!overlaps && dist < bestDist) {
        bestDist = dist;
      }
    }
  }

  return result;
});

async function fetchWordCloud() {
  try {
    loading.value = true;
    const response = await fetch('/api/word-cloud');
    if (!response.ok) throw new Error('Error loading word cloud');
    const data = await response.json();
    words.value = data.words || [];
    totalWords.value = data.totalWords || 0;
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchWordCloud();
});
</script>

<style scoped>
.word-cloud-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.word-cloud-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 100%;
}

.word-cloud-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e3a5f;
  margin: 0 0 12px 0;
  text-align: center;
}

.word-cloud-loading,
.word-cloud-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 280px;
  color: #666;
}

.word-cloud-error {
  color: #dc3545;
}

.word-cloud-canvas {
  width: 100%;
  min-height: 380px;
}

.word-cloud-svg {
  width: 100%;
  height: auto;
  min-height: 380px;
}

.word-cloud-text {
  cursor: default;
  transition: opacity 0.2s;
}

.word-cloud-text:hover {
  opacity: 0.7;
}

.word-cloud-stats {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 11px;
  color: #666;
}
</style>