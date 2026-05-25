<template>
  <div class="content-area">
    <div class="page-header-flex">
      <h2 class="page-title">Dashboards Analíticos</h2>
    </div>

    <div class="dashboard-kpis">
      <div class="kpi-card">
        <h3>Total de Álbumes</h3>
        <div class="kpi-value">{{ stats?.total_albums ?? 0 }}</div>
        <p class="kpi-desc">Colecciones indexadas en la base de datos.</p>
      </div>
      <div class="kpi-card">
        <h3>Total de Canciones</h3>
        <div class="kpi-value">{{ stats?.total_songs ?? 0 }}</div>
        <p class="kpi-desc">Letras disponibles para análisis.</p>
      </div>
      <div class="kpi-card">
        <h3>Agregadas Recientemente</h3>
        <div class="kpi-value status-ok">+{{ stats?.recently_added ?? 0 }}</div>
        <p class="kpi-desc">En los últimos 30 días.</p>
      </div>
      <div class="kpi-card">
        <h3>Canciones con Letra</h3>
        <div class="kpi-value">{{ stats?.songs_with_lyrics ?? 0 }}</div>
        <p class="kpi-desc">De {{ stats?.total_songs ?? 0 }} totales.</p>
      </div>
      <div class="kpi-card">
        <h3>Promedio de Caracteres</h3>
        <div class="kpi-value">~{{ avgLyricsChars }}</div>
        <p class="kpi-desc">Longitud promedio de letra.</p>
      </div>
      <div class="kpi-card kpi-card--warning" v-if="(stats?.songs_without_year ?? 0) > 0">
        <h3>Sin Año de Datos</h3>
        <div class="kpi-value">{{ stats?.songs_without_year ?? 0 }}</div>
        <p class="kpi-desc">Canciones con año desconocido.</p>
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container chart-container--full">
        <Bar :data="albumChartData" :options="albumChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container chart-container--full">
        <Doughnut :data="clasificacionChartData" :options="doughnutChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container chart-container--full">
        <Line :data="yearLineChartData" :options="yearLineChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container chart-container--full">
        <Bar :data="oovChartData" :options="oovChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container chart-container--full chart-container--tall">
        <WordCloud />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import WordCloud from '@/components/WordCloud.vue';
import { apiService } from '@/services/api';
import type { Stats } from '@/types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement
);

const stats = ref<Stats | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    stats.value = await apiService.getStats();
    console.log('Stats loaded:', stats.value);
  } catch (e) {
    console.error('Error loading stats:', e);
  } finally {
    loading.value = false;
  }
});

const avgLyricsChars = computed(() => {
  const val = stats.value?.avg_lyrics_length ?? 0;
  return val > 0 ? Math.round(val).toLocaleString() : '0';
});

const albumColors = [
  'rgba(117, 20, 40, 0.85)',
  'rgba(59, 130, 246, 0.85)',
  'rgba(16, 185, 129, 0.85)',
  'rgba(245, 158, 11, 0.85)',
  'rgba(139, 92, 246, 0.85)',
  'rgba(236, 72, 153, 0.85)',
  'rgba(6, 182, 212, 0.85)',
  'rgba(249, 115, 22, 0.85)',
  'rgba(34, 197, 94, 0.85)',
  'rgba(168, 85, 247, 0.85)',
];

// ── Album Bar Chart ──────────────────────────────────────────
const albumChartData = computed(() => {
  const top = stats.value?.top_albums ?? [];
  return {
    labels: top.map((a) => (a.album.length > 20 ? a.album.substring(0, 17) + '...' : a.album)),
    datasets: [
      {
        label: 'Cantidad de Canciones',
        data: top.map((a) => a.count),
        backgroundColor: top.map((_, i) => albumColors[i % albumColors.length]),
        borderColor: top.map((_, i) => albumColors[i % albumColors.length].replace('0.85', '1')),
        borderWidth: 2,
      },
    ],
  };
});

const albumChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1000, easing: 'easeOutQuart' as const },
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Distribución de Canciones por Álbum',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
  },
  scales: {
    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
    x: { grid: { display: false } },
  },
};

// ── Clasificacion Doughnut ────────────────────────────────────
const clasificacionChartData = computed(() => {
  const map = stats.value?.songs_by_clasificacion ?? {};
  const hasData = Object.keys(map).length > 0;
  const labels: Record<string, string> = {
    ESPAÑOL_ESTANDAR: 'Español Estándar',
    ESPAÑOL_REGIONAL: 'Español Regional',
    LENGUA_INDIGENA: 'Lengua Indígena',
  };
  return {
    labels: hasData
      ? Object.keys(map).map((k) => labels[k] ?? k)
      : ['Español Estándar', 'Español Regional', 'Lengua Indígena'],
    datasets: [
      {
        data: hasData ? Object.values(map) : [0, 0, 0],
        backgroundColor: hasData ? ['#c5a46c', '#60a5fa', '#751428'] : ['#e5e7eb', '#e5e7eb', '#e5e7eb'],
        hoverOffset: 20,
        borderWidth: 0,
      },
    ],
  };
});

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  cutout: '60%',
  plugins: {
    legend: {
      position: 'right' as const,
      labels: { usePointStyle: true, padding: 20, font: { size: 12 } },
    },
    title: {
      display: true,
      text: 'Clasificación de Español',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
  },
};

// ── Year Line Chart ──────────────────────────────────────────
const yearLineChartData = computed(() => {
  const byYear = stats.value?.songs_by_year ?? {};
  const sdCount = byYear['s/d'] ?? 0;
  const validYears = Object.keys(byYear)
    .filter((y) => y !== 's/d')
    .sort();
  const labels = [...validYears];
  const data = validYears.map((y) => byYear[y]);
  if (sdCount > 0) {
    labels.push('s/d');
    data.push(sdCount);
  }
  return {
    labels,
    datasets: [
      {
        label: 'Canciones',
        data,
        borderColor: '#751428',
        backgroundColor: 'rgba(117, 20, 40, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 6,
        pointBackgroundColor: '#751428',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointHoverRadius: 8,
        pointHoverBackgroundColor: '#751428',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 3,
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
    title: {
      display: true,
      text: 'Canciones por Año',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(117, 20, 40, 0.9)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: 'rgba(117, 20, 40, 1)',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      displayColors: false,
      callbacks: {
        title: (items: unknown[]) => {
          const ctx = items[0] as { label: string };
          return `Año: ${ctx.label}`;
        },
        label: (item: unknown) => {
          const ctx = item as { raw: number };
          return `Canciones: ${ctx.raw}`;
        },
      },
    },
  },
  scales: {
    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
    x: { grid: { display: false } },
  },
};

// ── OOV Level Bar Chart ────────────────────────────────────────
const oovChartData = computed(() => {
  const map = stats.value?.songs_by_oov_level ?? {};
  const hasData = Object.keys(map).length > 0;
  const labels: Record<string, string> = {
    BAJA: 'BAJA (<5%)',
    MEDIA: 'MEDIA (5-18%)',
    ALTA: 'ALTA (>18%)',
  };

  if (!hasData) {
    return {
      labels: ['Sin datos de OOV'],
      datasets: [
        {
          label: 'Nivel OOV',
          data: [0],
          backgroundColor: ['#e5e7eb'],
          borderWidth: 0,
        },
      ],
    };
  }

  return {
    labels: Object.keys(map).map((k) => labels[k] ?? k),
    datasets: [
      {
        label: 'Nivel OOV',
        data: Object.values(map),
        backgroundColor: ['#34d399', '#fbbf24', '#f87171'],
        borderWidth: 0,
      },
    ],
  };
});

const oovChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Nivel de OOV por Canción',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
  },
  scales: {
    x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
    y: { grid: { display: false } },
  },
};
</script>

<style scoped>
.dashboard-charts {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.chart-container {
  width: 100%;
  max-width: 100%;
  height: 350px;
}

.chart-container--full {
  width: 100%;
  max-width: 100%;
}

.chart-container--tall {
  height: 420px;
}

.kpi-card--warning {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
  border-left: 4px solid #ffc107;
}

.kpi-card--warning .kpi-value {
  color: #856404;
}
</style>