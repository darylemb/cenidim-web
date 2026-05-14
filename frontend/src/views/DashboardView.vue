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
    </div>

    <div class="dashboard-charts">
      <div class="chart-container">
        <Bar :data="albumChartData" :options="albumChartOptions" />
      </div>
      <div class="chart-container">
        <Doughnut :data="clasificacionChartData" :options="doughnutChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-container">
        <Line :data="yearLineChartData" :options="yearLineChartOptions" />
      </div>
      <div class="chart-container">
        <Bar :data="oovChartData" :options="oovChartOptions" />
      </div>
    </div>

    <div class="dashboard-charts dashboard-charts--single">
      <div class="chart-container chart-container--tall">
        <PolarArea :data="indigenaChartData" :options="polarChartOptions" />
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
  RadialLinearScale,
} from 'chart.js';
import { Bar, Doughnut, Line, PolarArea } from 'vue-chartjs';
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
  PointElement,
  RadialLinearScale
);

const stats = ref<Stats | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    stats.value = await apiService.getStats();
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

// ── Album Bar Chart ──────────────────────────────────────────
const albumChartData = computed(() => {
  const top = stats.value?.top_albums ?? [];
  return {
    labels: top.map((a) => (a.album.length > 20 ? a.album.substring(0, 17) + '...' : a.album)),
    datasets: [
      {
        label: 'Cantidad de Canciones',
        data: top.map((a) => a.count),
        backgroundColor: 'rgba(117, 20, 40, 0.7)',
        borderColor: 'rgba(117, 20, 40, 1)',
        borderWidth: 1,
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
  const labels: Record<string, string> = {
    ESPAÑOL_ESTANDAR: 'Español Estándar',
    ESPAÑOL_REGIONAL: 'Español Regional',
    LENGUA_INDIGENA: 'Lengua Indígena',
  };
  return {
    labels:
      Object.keys(map).length > 0
        ? Object.keys(map).map((k) => labels[k] ?? k)
        : ['Español Estándar', 'Español Regional', 'Lengua Indígena'],
    datasets: [
      {
        data: Object.values(map).length > 0 ? Object.values(map) : [35, 10, 40],
        backgroundColor: ['#c5a46c', '#60a5fa', '#751428'],
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
      text: 'Clasificación Temática',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
  },
};

// ── Year Line Chart ──────────────────────────────────────────
const yearLineChartData = computed(() => {
  const byYear = stats.value?.songs_by_year ?? {};
  const sortedYears = Object.keys(byYear).sort();
  return {
    labels: sortedYears,
    datasets: [
      {
        label: 'Canciones',
        data: sortedYears.map((y) => byYear[y]),
        borderColor: '#751428',
        backgroundColor: 'rgba(117, 20, 40, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#751428',
      },
    ],
  };
});

const yearLineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Canciones por Año',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
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
  const labels: Record<string, string> = {
    BAJA: 'BAJA (<5%)',
    MEDIA: 'MEDIA (5-18%)',
    ALTA: 'ALTA (>18%)',
  };
  return {
    labels:
      Object.keys(map).length > 0
        ? Object.keys(map).map((k) => labels[k] ?? k)
        : ['BAJA (<5%)', 'MEDIA (5-18%)', 'ALTA (>18%)'],
    datasets: [
      {
        label: 'Nivel OOV',
        data: Object.values(map).length > 0 ? Object.values(map) : [10, 25, 5],
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

// ── Indigena Polar Chart ───────────────────────────────────────
const indigenaChartData = computed(() => {
  const map = stats.value?.songs_by_indigena ?? {};
  return {
    labels:
      Object.keys(map).length > 0
        ? Object.keys(map).map((k) =>
            k === 'CON_INDIGENA' ? 'Con Palabra Indígena' : 'Sin Palabra Indígena'
          )
        : ['Con Palabra Indígena', 'Sin Palabra Indígena'],
    datasets: [
      {
        data: Object.values(map).length > 0 ? Object.values(map) : [8, 42],
        backgroundColor: ['#c5a46c', '#751428'],
        borderWidth: 0,
      },
    ],
  };
});

const polarChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1200, easing: 'easeInOutQuart' as const },
  plugins: {
    legend: {
      position: 'right' as const,
      labels: { usePointStyle: true, padding: 20, font: { size: 12 } },
    },
    title: {
      display: true,
      text: 'Presencia de Palabra Indígena',
      font: { size: 14, weight: 'bold' as const },
      padding: { bottom: 20 },
    },
  },
  scales: {
    r: {
      ticks: { display: false },
      grid: { color: '#e2e8f0' },
    },
  },
};
</script>

<style scoped>
.dashboard-charts--single {
  grid-template-columns: 1fr;
  max-width: 600px;
}
</style>
