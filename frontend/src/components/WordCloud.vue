<template>
  <div class="word-cloud-wrapper">
    <div class="word-cloud-container">
      <h3 class="word-cloud-title">Palabras en las canciones</h3>
      <div v-if="loading" class="word-cloud-loading">Cargando...</div>
      <div v-else-if="error" class="word-cloud-error">{{ error }}</div>
      <div v-else class="word-cloud-canvas" ref="canvasContainer">
        <svg viewBox="0 0 700 450" class="word-cloud-svg" preserveAspectRatio="xMidYMid meet" aria-label="Nube de palabras frecuentes en las canciones">
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
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { apiService } from '@/services/api';

const SPANISH_STOP_WORDS = new Set([
  'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con',
  'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí',
  'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'hay',
  'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra',
  'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos',
  'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada',
  'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi',
  'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os',
  'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos',
  'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros',
  'vuestras', 'esos', 'esas', 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'esté',
  'estés', 'estemos', 'estéis', 'estén', 'estaré', 'estarás', 'estará', 'estaremos', 'estaréis',
  'estarán', 'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían', 'estaba', 'estabas',
  'estábamos', 'estabais', 'estaban', 'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis',
  'estuvieron', 'estuviera', 'estuvieras', 'estuviéramos', 'estuvierais', 'estuvieran',
  'estuviese', 'estuvieses', 'estuviésemos', 'estuvieseis', 'estuviesen', 'estando', 'estado',
  'estada', 'estados', 'estadas', 'estad', 'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haya',
  'hayas', 'hayamos', 'hayáis', 'hayan', 'habré', 'habrás', 'habrá', 'habremos', 'habréis',
  'habrán', 'habría', 'habrías', 'habríamos', 'habríais', 'habrían', 'había', 'habías',
  'habíamos', 'habíais', 'habían', 'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron',
  'hubiera', 'hubieras', 'hubiéramos', 'hubierais', 'hubieran', 'hubiese', 'hubieses',
  'hubiésemos', 'hubieseis', 'hubiesen', 'habiendo', 'habido', 'habida', 'habidos', 'habidas',
  'soy', 'eres', 'es', 'somos', 'sois', 'son', 'sea', 'seas', 'seamos', 'seáis', 'sean', 'seré',
  'serás', 'será', 'seremos', 'seréis', 'serán', 'sería', 'serías', 'seríamos', 'seríais',
  'serían', 'era', 'eras', 'éramos', 'erais', 'eran', 'fui', 'fuiste', 'fue', 'fuimos',
  'fuisteis', 'fueron', 'fuera', 'fueras', 'fuéramos', 'fuerais', 'fueran', 'fuese', 'fueses',
  'fuésemos', 'fueseis', 'fuesen', 'siendo', 'sido', 'tengo', 'tienes', 'tiene', 'tenemos',
  'tenéis', 'tienen', 'tenga', 'tengas', 'tengamos', 'tengáis', 'tengan', 'tendré', 'tendrás',
  'tendrá', 'tendremos', 'tendréis', 'tendrán', 'tendría', 'tendrías', 'tendríamos', 'tendríais',
  'tendrían', 'tenía', 'tenías', 'teníamos', 'teníais', 'tenían', 'tuve', 'tuviste', 'tuvo',
  'tuvimos', 'tuvisteis', 'tuvieron', 'tuviera', 'tuvieras', 'tuviéramos', 'tuvierais',
  'tuvieran', 'tuviese', 'tuvieses', 'tuviésemos', 'tuvieseis', 'tuviesen', 'teniendo',
  'tenido', 'tenida', 'tenidos', 'tenidas', 'tened',
]);

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

let _wordCloudController: AbortController | null = null;

const svgWidth = 700;
const svgHeight = 450;

const palette = [
  '#1e3a5f', '#2d5a87', '#3d7ab3', '#5a9bd4', '#7ab8e8',
  '#9dd3f5', '#bce8fa', '#d6effc', '#c5a46c', '#751428',
  '#2563eb', '#059669', '#dc2626', '#7c3aed', '#ea580c',
];

const topWords = computed(() => {
  return words.value
    .filter(w => w.text.length >= 4 && !SPANISH_STOP_WORDS.has(w.text.toLowerCase()))
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
  _wordCloudController?.abort();
  _wordCloudController = new AbortController();
  try {
    loading.value = true;
    const data = await apiService.getWordCloud(_wordCloudController.signal);
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
  _wordCloudController?.abort();
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