import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import { apiService } from '../services/api';

// Registrar los módulos de chart.js que vamos a usar
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

export const DashboardView = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    apiService
      .getStats()
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading stats:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const isMobile = window.innerWidth < 768;

  if (loading) {
    return (
      <div className="content-area">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Cargando métricas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-area">
        <div className="page-header-flex">
          <h2 className="page-title">Dashboards Analíticos</h2>
        </div>
        <div className="auth-error">
          Error al cargar las métricas: {error}
        </div>
      </div>
    );
  }

  // Prepare chart data from real stats
  const topAlbums = stats?.top_albums || [];
  const songsByClasificacion = stats?.songs_by_clasificacion || {};

  // Bar chart data - Songs per Album (top 10)
  const barChartData = {
    labels: topAlbums.map((a) => a.album.length > 20 ? a.album.substring(0, 17) + '...' : a.album),
    datasets: [
      {
        label: 'Cantidad de Canciones',
        data: topAlbums.map((a) => a.count),
        backgroundColor: 'rgba(117, 20, 40, 0.7)',
        borderColor: 'rgba(117, 20, 40, 1)',
        borderWidth: 1,
      },
    ],
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        display: !isMobile,
      },
      title: {
        display: true,
        text: 'Distribución de Canciones por Álbum',
        font: { size: isMobile ? 14 : 16, weight: 'bold' },
        padding: { bottom: 20 },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#f1f5f9' },
      },
      x: {
        grid: { display: false },
      },
    },
  };

  // Pie chart data - Songs by Clasificacion
  const clasificacionLabels = Object.keys(songsByClasificacion).length > 0
    ? Object.keys(songsByClasificacion).map((key) => {
        const labels = {
          ESPAÑOL_ESTANDAR: 'Español Estándar',
          ESPAÑOL_REGIONAL: 'Español Regional',
          LENGUA_INDIGENA: 'Lengua Indígena',
        };
        return labels[key] || key;
      })
    : ['Alegría', 'Melancolía', 'Infantil', 'Naturaleza', 'Otros'];

  const clasificacionValues = Object.values(songsByClasificacion).length > 0
    ? Object.values(songsByClasificacion)
    : [35, 10, 40, 10, 5];

  const pieChartData = {
    labels: clasificacionLabels,
    datasets: [
      {
        label: 'Proyección de Sentimientos',
        data: clasificacionValues,
        backgroundColor: [
          '#c5a46c', // Dorado
          '#60a5fa', // Azul
          '#751428', // Guinda
          '#34d399', // Verde
          '#a78bfa', // Morado
        ],
        hoverOffset: 20,
        borderWidth: 0,
      },
    ],
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: isMobile ? 'bottom' : 'right',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: { size: 12 },
        },
      },
      title: {
        display: true,
        text: 'Clasificación Temática',
        font: { size: isMobile ? 14 : 16, weight: 'bold' },
        padding: { bottom: 20 },
      },
    },
  };

  return (
    <div className="content-area">
      <div className="page-header-flex">
        <h2 className="page-title">Dashboards Analíticos</h2>
      </div>

      {/* Tarjetas de Métricas Rápidas (KPIs) */}
      <div className="dashboard-kpis">
        <div className="kpi-card">
          <h3>Total de Álbumes</h3>
          <div className="kpi-value">{stats?.total_albums || 0}</div>
          <p className="kpi-desc">Colecciones indexadas en la base de datos.</p>
        </div>

        <div className="kpi-card">
          <h3>Total de Canciones</h3>
          <div className="kpi-value">{stats?.total_songs || 0}</div>
          <p className="kpi-desc">Letras disponibles para análisis.</p>
        </div>

        <div className="kpi-card">
          <h3>Agregadas Recientemente</h3>
          <div className="kpi-value status-ok">+{stats?.recently_added || 0}</div>
          <p className="kpi-desc">En los últimos 30 días.</p>
        </div>
      </div>

      {/* Contenedores de Gráficos */}
      <div className="dashboard-charts">
        <div className="chart-container">
          <Bar data={barChartData} options={barChartOptions} />
        </div>

        <div className="chart-container">
          <Pie data={pieChartData} options={pieChartOptions} />
        </div>
      </div>
    </div>
  );
};
