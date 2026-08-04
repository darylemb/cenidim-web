<template>
  <div class="content-area dashboard">
    <header class="dashboard__masthead">
      <div class="dashboard__masthead-text">
        <span class="eyebrow">Archivo CENIDIM</span>
        <h1 class="dashboard__title display">Dashboards analíticos</h1>
        <p class="dashboard__lede">
          Una vista sintética del catálogo musical: distribución por año, lengua,
          género y presencia regional en el archivo.
        </p>
      </div>
      <div v-if="!loading && !isEmptyResult && stats" class="dashboard__masthead-meta">
        <div class="meta-block">
          <span class="meta-block__label eyebrow">Catálogo</span>
          <span class="meta-block__value display mono">{{ (stats.catalog_total ?? stats.total_songs).toLocaleString() }}</span>
          <span class="meta-block__hint">canciones indexadas</span>
        </div>
        <div class="meta-block">
          <span class="meta-block__label eyebrow">Álbumes</span>
          <span class="meta-block__value display mono">{{ stats.total_albums.toLocaleString() }}</span>
          <span class="meta-block__hint">colecciones</span>
        </div>
      </div>
    </header>

    <DashboardFilters />
    <FilterChips />

    <div v-if="loading" class="dashboard__loading">
      <div class="spinner" aria-label="Cargando estadísticas"></div>
      <span class="dashboard__loading-text">Cargando estadísticas…</span>
    </div>

    <EmptyState
      v-else-if="isEmptyResult"
      label="El archivo no devuelve coincidencias para estos filtros."
      description="Pruebe a relajar uno o más criterios, o restablecer el conjunto completo."
    >
      <template #action>
        <button class="dashboard__reset-btn" @click="onClearAll">Restablecer filtros</button>
      </template>
    </EmptyState>

    <template v-else>
      <p v-if="!filters.isEmpty" class="dashboard__summary">
        Mostrando <strong>{{ stats?.total_songs ?? 0 }}</strong> de
        <strong>{{ stats?.catalog_total ?? stats?.total_songs ?? 0 }}</strong> canciones que coinciden con los filtros activos.
      </p>

      <!-- KPI strip.
           Each card carries a label, the value, and a hint that
           answers "what does this number mean?" — reviewer feedback
           (01/jul/2026) pointed out that the previous mix of
           constant vs filter-dependent KPIs in the same strip was
           confusing. We now label every constant KPI with a "catálogo
           completo" tag and every filtered KPI with a "filtro actual"
           tag. -->
      <section class="dashboard__kpis" aria-label="Indicadores clave">
        <article class="kpi">
          <span class="kpi__label">Total canciones</span>
          <span class="kpi__value display mono">{{ stats?.total_songs ?? 0 }}</span>
          <span class="kpi__hint" v-if="hasActiveFilters">Filtrado · {{ stats?.catalog_total ?? '–' }} en catálogo</span>
          <span class="kpi__hint" v-else>Con letra en catálogo</span>
        </article>
        <article class="kpi">
          <span class="kpi__label">Álbumes</span>
          <span class="kpi__value display mono">{{ stats?.total_albums ?? 0 }}</span>
          <span class="kpi__hint" v-if="hasActiveFilters">Filtrado · colección única por disco</span>
          <span class="kpi__hint" v-else>Colección única por disco</span>
        </article>
        <article class="kpi">
          <span class="kpi__label">Agregadas recientemente</span>
          <span class="kpi__value display mono kpi__value--accent">+{{ stats?.recently_added ?? 0 }}</span>
          <span class="kpi__hint">Catálogo completo · últimos 30 días</span>
        </article>
        <article class="kpi">
          <span class="kpi__label">Con letra</span>
          <span class="kpi__value display mono">{{ stats?.songs_with_lyrics ?? 0 }}</span>
          <span class="kpi__hint" v-if="hasActiveFilters">Filtrado · de {{ stats?.total_songs ?? 0 }} visibles</span>
          <span class="kpi__hint" v-else>En {{ stats?.catalog_total ?? '–' }} indexadas</span>
        </article>
        <article class="kpi">
          <span class="kpi__label">Años distintos</span>
          <span class="kpi__value display mono">{{ Object.keys(stats?.songs_by_year ?? {}).filter(y => y !== 's/d').length }}</span>
          <span class="kpi__hint" v-if="hasActiveFilters">Filtrado · rango temporal activo</span>
          <span class="kpi__hint" v-else>Catálogo completo</span>
        </article>
        <article class="kpi">
          <span class="kpi__label">Temas distintos</span>
          <span class="kpi__value display mono">{{ stats?.distinct_themes ?? 0 }}</span>
          <span class="kpi__hint" v-if="hasActiveFilters">Filtrado · en {{ stats?.total_songs ?? 0 }} canciones</span>
          <span class="kpi__hint" v-else>En catálogo completo</span>
        </article>
        <article v-if="(stats?.songs_without_year ?? 0) > 0" class="kpi kpi--warning">
          <span class="kpi__label">Sin año</span>
          <span class="kpi__value display mono">{{ stats?.songs_without_year ?? 0 }}</span>
          <span class="kpi__hint">Pendiente de datar</span>
        </article>
      </section>

      <!-- Hero chart: timeline by year.
           The chart tooltip explains how the year bucket is built
           and that 's/d' represents songs whose fonograma has no
           publish year. -->
      <section class="dashboard__hero" aria-label="Canciones por año">
        <header class="chart-header">
          <span class="eyebrow">Eje temporal</span>
          <h2 class="chart-header__title display">Canciones por año</h2>
          <p class="chart-header__caption">
            Volumen anual del catálogo, año a año.
            <ChartInfoButton :info="chartInfo.cancionesPorAnio" />
          </p>
        </header>
        <div class="chart-canvas" role="img" aria-label="Gráfico de canciones por año">
          <Line :data="yearLineChartData" :options="yearLineChartOptions" />
        </div>
      </section>

      <!-- 2-col chart grid.
           Previously this row started with a "Top 10 por álbum" bar
           chart. Reviewer feedback (01/jul/2026) marked it as not
           relevant for the research analysis so it has been removed
           (commit ux: dashboard KPI strip + chart labels clarified).
           Each remaining chart now carries a ChartInfoButton that
           surfaces the definition in a popover so the user does not
           have to consult an external glossary to understand what
           the visualization measures. -->
      <section class="dashboard__grid">
        <article class="chart-card" aria-label="Tipología lingüística">
          <header class="chart-header">
            <span class="eyebrow">Tipología lingüística</span>
            <h2 class="chart-header__title display">Clasificación</h2>
            <p class="chart-header__caption">
              Distribución por categoría de español.
              <ChartInfoButton :info="chartInfo.clasificacion" />
            </p>
          </header>
          <div class="chart-canvas" role="img" aria-label="Gráfico de clasificación lingüística">
            <Doughnut v-if="hasClasificacionData" :data="clasificacionChartData" :options="doughnutChartOptions" />
            <EmptyState v-else label="Sin datos de clasificación" />
          </div>
          <ul class="chart-card__legend" aria-label="Leyenda">
            <li><strong>Estándar</strong> &lt; 5% palabras OOV — vocabulario cotidiano</li>
            <li><strong>Regional</strong> 5–18% OOV — regionalismos sin presencia indígena</li>
            <li><strong>Indígena</strong> contiene palabras de la lista <code>PALABRAS_INDIGENAS</code> o &gt; 18% OOV</li>
          </ul>
        </article>

        <article class="chart-card" aria-label="Canciones por tema">
          <header class="chart-header">
            <span class="eyebrow">Categorías temáticas</span>
            <h2 class="chart-header__title display">Por tema</h2>
            <p class="chart-header__caption">
              Distribución por tema declarado en el archivo de letra.
              <ChartInfoButton :info="chartInfo.tema" />
            </p>
          </header>
          <div class="chart-canvas" role="img" aria-label="Gráfico de canciones por tema">
            <Bar v-if="hasThemeData" :data="themeChartData" :options="themeChartOptions" />
            <EmptyState v-else label="Sin datos de tema" />
          </div>
        </article>

        <article class="chart-card" aria-label="Nivel de vocabulario fuera del modelo">
          <header class="chart-header">
            <span class="eyebrow">Léxico</span>
            <h2 class="chart-header__title display">Índice OOV</h2>
            <p class="chart-header__caption">
              Porcentaje de palabras no reconocidas por spaCy <code>es_core_news_md</code>.
              <ChartInfoButton :info="chartInfo.oov" />
            </p>
          </header>
          <div class="chart-canvas" role="img" aria-label="Gráfico de índice OOV por canción">
            <Bar v-if="hasOovData" :data="oovChartData" :options="oovChartOptions" />
            <EmptyState v-else label="Sin datos de OOV" />
          </div>
          <ul class="chart-card__legend" aria-label="Leyenda">
            <li><strong>Baja</strong> &lt; 5% OOV</li>
            <li><strong>Media</strong> 5–18% OOV</li>
            <li><strong>Alta</strong> &gt; 18% OOV</li>
          </ul>
        </article>
      </section>

      <!-- Word cloud full width — uses its own aspect ratio so the SVG
           fills the container's width without being letterboxed. The
           WordCloud component now owns its own header (intro + info
           button); we keep the wrapper section for layout slot. -->
      <section class="dashboard__wordcloud" aria-label="Nube de palabras">
        <div class="wordcloud-frame" role="img" aria-label="Nube de palabras frecuentes en las canciones">
          <WordCloud />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import WordCloud from '@/components/WordCloud.vue';
import DashboardFilters from '@/components/DashboardFilters.vue';
import FilterChips from '@/components/FilterChips.vue';
import EmptyState from '@/components/EmptyState.vue';
import ChartInfoButton from '@/components/ChartInfoButton.vue';
import { apiService } from '@/services/api';
import { useFiltersStore } from '@/stores/filters';
import type { Stats } from '@/types';
import { swatchFor } from '@/config/themes';
import { chartInfo } from '@/config/chartInfo';

const filters = useFiltersStore();
const stats = ref<Stats | null>(null);
const loading = ref(true);
let statsController: AbortController | null = null;
let initialSyncDone = false;

async function loadStats() {
  statsController?.abort();
  statsController = new AbortController();
  loading.value = true;
  try {
    stats.value = await apiService.getStats(filters.queryString, statsController.signal);
  } catch {
    stats.value = null;
  } finally {
    loading.value = false;
  }
}

function onClearAll() {
  // Called by the EmptyState reset button. Mutating the store
  // triggers the watch below, which is the single source of truth
  // for stats reloading — no manual loadStats() needed here.
  filters.clear();
}

onMounted(() => {
  // First load: pull current URL filters (applied by DashboardFilters.onMounted)
  // then fetch stats. The watch below will NOT re-fire because initialSyncDone
  // gates the first paint.
  setTimeout(() => {
    initialSyncDone = true;
    loadStats();
  }, 0);
});

onUnmounted(() => {
  statsController?.abort();
});

// Watch for queryString changes. This is the single source of truth for
// stats reloading. All filter mutations (DashboardFilters, FilterChips,
// EmptyState reset) flow through the store, so the watch fires once per
// intentional change — no double-fetch.
watch(
  () => filters.queryString,
  () => {
    if (initialSyncDone) loadStats();
  },
);

const isEmptyResult = computed(() => (stats.value?.total_songs ?? 0) === 0);

const hasActiveFilters = computed(() => !filters.isEmpty);

const hasClasificacionData = computed(
  () => Object.keys(stats.value?.songs_by_clasificacion ?? {}).length > 0,
);
const hasThemeData = computed(
  () => Object.keys(stats.value?.songs_by_theme ?? {}).length > 0,
);
const hasOovData = computed(
  () => Object.keys(stats.value?.songs_by_oov_level ?? {}).length > 0,
);

// albumColors palette was tied to the Top 10 album chart and was
// removed together with it (reviewer feedback 01/jul/2026).

// ── Clasificacion Doughnut ────────────────────────────────────
// ── Clasificacion Doughnut ────────────────────────────────────
const clasificacionChartData = computed(() => {
  const map = stats.value?.songs_by_clasificacion ?? {};
  const labels: Record<string, string> = {
    ESPAÑOL_ESTANDAR: 'Español Estándar',
    ESPAÑOL_REGIONAL: 'Español Regional',
    LENGUA_INDIGENA: 'Lengua Indígena',
  };
  return {
    labels: Object.keys(map).map((k) => labels[k] ?? k),
    datasets: [
      {
        data: Object.values(map),
        backgroundColor: ['#c5a46c', '#2c4a6e', '#751428'],
        hoverOffset: 16,
        borderWidth: 2,
        borderColor: 'var(--color-bg)',
      },
    ],
  };
});

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  cutout: '62%',
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        usePointStyle: true,
        padding: 16,
        font: { family: 'Outfit', size: 12, weight: 500 },
        color: 'var(--color-text)',
      },
    },
    title: { display: false },
  },
};

// ── Year Line Chart ──────────────────────────────────────────
const yearLineChartData = computed(() => {
  const byYear = stats.value?.songs_by_year ?? {};
  // s/d (no year) is surfaced via the "Sin año" KPI strip instead of
  // cluttering the time-axis. Keep the count available for the parent
  // template's summary line.
  const validYears = Object.keys(byYear)
    .filter((y) => y !== 's/d')
    .sort();
  const labels = [...validYears];
  const data = validYears.map((y) => byYear[y]);
  return {
    labels,
    datasets: [
      {
        label: 'Canciones',
        data,
        borderColor: '#751428',
        backgroundColor: 'rgba(117, 20, 40, 0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 5,
        pointBackgroundColor: '#751428',
        pointBorderColor: 'var(--color-bg)',
        pointBorderWidth: 2,
        pointHoverRadius: 7,
      },
    ],
  };
});

const yearLineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 1500,
    easing: 'easeOutQuart' as const,
    animateRotate: true,
    animateScale: true,
  },
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: { display: false },
    title: { display: false },
    tooltip: {
      enabled: true,
      backgroundColor: '#1a1612',
      titleColor: '#faf7f0',
      bodyColor: '#faf7f0',
      borderColor: '#c5a46c',
      borderWidth: 1,
      cornerRadius: 2,
      padding: 12,
      displayColors: false,
      titleFont: { family: 'Fraunces', size: 14, weight: 600 },
      bodyFont: { family: 'JetBrains Mono', size: 12 },
      callbacks: {
        title: (items: unknown[]) => {
          const ctx = items[0] as { label: string };
          if (!ctx || typeof ctx.label !== 'string') return '';
          return `Año ${ctx.label}`;
        },
        label: (item: unknown) => {
          const ctx = item as { raw: unknown };
          const value = typeof ctx.raw === 'number' ? ctx.raw : 0;
          return `${value} canción${value === 1 ? '' : 'es'}`;
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(26, 22, 18, 0.06)' },
      ticks: { font: { family: 'JetBrains Mono', size: 11 }, color: 'var(--color-text-muted)' },
    },
    x: {
      grid: { display: false },
      ticks: { font: { family: 'JetBrains Mono', size: 11 }, color: 'var(--color-text-muted)' },
    },
  },
};

// ── OOV Level Bar Chart ────────────────────────────────────────
const oovChartData = computed(() => {
  const map = stats.value?.songs_by_oov_level ?? {};
  const labels: Record<string, string> = {
    BAJA: 'BAJA (<5%)',
    MEDIA: 'MEDIA (5–18%)',
    ALTA: 'ALTA (>18%)',
  };
  return {
    labels: Object.keys(map).map((k) => labels[k] ?? k),
    datasets: [
      {
        label: 'Nivel OOV',
        data: Object.values(map),
        backgroundColor: ['#6b8068', '#c97a4a', '#9a2a2a'],
        borderWidth: 0,
        borderRadius: 2,
      },
    ],
  };
});

const oovChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  plugins: { legend: { display: false }, title: { display: false } },
  scales: {
    x: { beginAtZero: true, grid: { color: 'rgba(26, 22, 18, 0.06)' } },
    y: { grid: { display: false }, ticks: { font: { family: 'Outfit', size: 12 } } },
  },
};

// ── Theme Bar Chart ────────────────────────────────────────────
// Themes now come straight from the `Tema: ...` line in each LetrasTXT
// song (not the classifier's keyword buckets). We hash the value to
// pick a stable colour from the brand-aligned swatch set.
const themeColorFor = (key: string) => {
  if (!key) return 'rgba(138, 127, 110, 0.85)';
  const hex = swatchFor(key);
  // Convert #rrggbb to rgba(r, g, b, 0.85)
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.85)`;
};

const themeChartData = computed(() => {
  const map = stats.value?.songs_by_theme ?? {};
  const entries = Object.entries(map).sort((a, b) => b[1] - a[1]);
  return {
    labels: entries.map(([k]) => (k === '' ? 'Sin tema' : k)),
    datasets: [
      {
        label: 'Canciones',
        data: entries.map(([, v]) => v),
        backgroundColor: entries.map(([k]) => themeColorFor(k)),
        borderWidth: 0,
        borderRadius: 2,
      },
    ],
  };
});

const themeChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  plugins: { legend: { display: false }, title: { display: false } },
  scales: {
    x: { beginAtZero: true, grid: { color: 'rgba(26, 22, 18, 0.06)' } },
    y: { grid: { display: false }, ticks: { font: { family: 'Outfit', size: 12 } } },
  },
};
</script>

<style scoped>
.dashboard {
  --rail-width: 1px;
}

.dashboard__masthead {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-7);
  align-items: end;
  padding: var(--space-6) 0 var(--space-7);
  border-bottom: var(--hairline);
  margin-bottom: var(--space-7);
}

.dashboard__masthead-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 50ch;
}

.dashboard__title {
  font-family: var(--font-display);
  font-size: var(--font-size-4xl);
  font-weight: 400;
  font-variation-settings: 'opsz' 144, 'SOFT' 30, 'WONK' 0;
  line-height: 0.95;
  color: var(--color-text);
  margin: 0;
  letter-spacing: var(--tracking-tight);
}

.dashboard__lede {
  font-family: var(--font-body);
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  line-height: var(--line-height-loose);
  margin: var(--space-3) 0 0;
  max-width: 50ch;
}

.dashboard__masthead-meta {
  display: flex;
  gap: var(--space-7);
  padding-left: var(--space-7);
  border-left: var(--hairline-soft);
}

.meta-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  text-align: right;
}

.meta-block__label {
  font-family: var(--font-body);
}

.meta-block__value {
  font-size: var(--font-size-3xl);
  font-weight: 500;
  color: var(--color-text);
  line-height: 1;
  font-variation-settings: 'opsz' 144;
}

.meta-block__hint {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.dashboard__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) var(--space-5);
  color: var(--color-text-muted);
  gap: var(--space-4);
}

.dashboard__loading-text {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.dashboard__summary {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  padding: var(--space-3) 0;
  margin: 0;
  border-top: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
}

.dashboard__summary strong {
  color: var(--color-text);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.dashboard__kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0;
  margin: var(--space-6) 0;
  border-top: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
}

.kpi {
  padding: var(--space-5) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  border-right: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
  position: relative;
}

.kpi:last-child {
  border-right: none;
}

.kpi__label {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.kpi__value {
  font-family: var(--font-display);
  font-size: var(--font-size-3xl);
  font-weight: 500;
  font-variation-settings: 'opsz' 144;
  color: var(--color-text);
  line-height: 1;
  margin: var(--space-2) 0;
  letter-spacing: var(--tracking-tight);
}

.kpi__value--accent {
  color: var(--color-brand);
}

.kpi__hint {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  line-height: var(--line-height-snug);
}

.kpi--warning {
  background: rgba(201, 122, 74, 0.08);
}

.kpi--warning .kpi__value {
  color: var(--color-warning);
}

.dashboard__hero {
  margin: var(--space-7) 0 var(--space-7);
  padding: var(--space-6) 0;
  border-top: var(--hairline);
  border-bottom: var(--hairline);
}

.dashboard__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
  margin: var(--space-7) 0;
  border-top: var(--hairline);
}

.chart-card {
  padding: var(--space-6) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  border-right: var(--hairline-soft);
  border-bottom: var(--hairline-soft);
  min-height: 320px;
}

.chart-card:nth-child(2n) {
  border-right: none;
}

.chart-card__legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  border-top: var(--hairline-soft);
  padding-top: var(--space-3);
}
.chart-card__legend li {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.chart-card__legend strong {
  font-weight: 600;
  color: var(--color-text);
  min-width: 5.5rem;
  display: inline-block;
}
.chart-card__legend code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  padding: 0 var(--space-1);
  background: var(--color-bg-soft);
  border-radius: var(--radius-sm);
}

.chart-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.chart-header__title {
  font-family: var(--font-display);
  font-size: var(--font-size-xl);
  font-weight: 400;
  font-variation-settings: 'opsz' 72, 'SOFT' 50;
  color: var(--color-text);
  margin: 0;
  line-height: 1.1;
  letter-spacing: var(--tracking-tight);
}

.chart-header__caption {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: var(--space-1) 0 0;
}

.chart-canvas {
  width: 100%;
  height: 280px;
  position: relative;
}

.chart-canvas--tall {
  height: 360px;
}

.dashboard__wordcloud {
  margin: var(--space-7) 0;
  padding: var(--space-6) 0;
  border-top: var(--hairline);
  border-bottom: var(--hairline);
}

/* The word cloud's own frame: full container width, aspect-ratio driven
   height so the SVG never gets letterboxed. */
.wordcloud-frame {
  width: 100%;
  margin-top: var(--space-4);
}

.dashboard__reset-btn {
  margin-top: var(--space-4);
  background: var(--color-brand);
  color: var(--color-text-inverse);
  border: none;
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  cursor: pointer;
  min-height: var(--tap-target-min);
  transition: background var(--transition-fast);
}

.dashboard__reset-btn:hover {
  background: var(--color-brand-dark);
}

@media (max-width: 1023px) {
  .dashboard__masthead {
    grid-template-columns: 1fr;
  }
  .dashboard__masthead-meta {
    padding-left: 0;
    border-left: none;
    border-top: var(--hairline-soft);
    padding-top: var(--space-4);
  }
  .meta-block {
    text-align: left;
  }
}

@media (max-width: 768px) {
  .dashboard__title {
    font-size: var(--font-size-3xl);
  }
  .dashboard__grid {
    grid-template-columns: 1fr;
  }
  .chart-card {
    border-right: none;
  }
  .dashboard__kpis {
    grid-template-columns: repeat(2, 1fr);
  }
  .kpi:nth-child(2n) {
    border-right: none;
  }
  .kpi:nth-child(n + 3) {
    border-top: var(--hairline-soft);
  }
}
</style>
