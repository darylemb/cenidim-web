import React from 'react';
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

// Registrar los módulos de chart.js que vamos a usar
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export const DashboardView = () => {
  // Datos Dummies para la demostración
  const totalAlbums = 14;
  const totalCanciones = 175;

  // Datos para gráfico de barras (Canciones por Álbum - Dummy)
  const barChartData = {
    labels: ['Vol. 2', 'Vol. 3', 'Vol. 4', 'Vol. 6', 'Cantacuentos', 'Son de la Ciudad', 'Otros'],
    datasets: [
      {
        label: 'Cantidad de Canciones',
        data: [12, 15, 13, 14, 20, 18, 83],
        backgroundColor: 'rgba(117, 20, 40, 0.7)', // Color Guinda Cenidim
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
      },
      title: {
        display: true,
        text: 'Distribución de Canciones por Álbum',
        font: { size: 16 }
      },
    },
  };

  // Datos para gráfico de pastel (Sentimientos Proyectados - Dummy)
  const pieChartData = {
    labels: ['Alegría', 'Melancolía', 'Infantil/Didáctico', 'Naturaleza', 'Otros'],
    datasets: [
      {
        label: 'Proyección de Sentimientos',
        data: [35, 10, 40, 10, 5],
        backgroundColor: [
          'rgba(197, 164, 108, 0.8)', // Dorado
          'rgba(54, 162, 235, 0.8)',  // Azul
          'rgba(117, 20, 40, 0.8)',   // Guinda
          'rgba(75, 192, 192, 0.8)',  // Verde
          'rgba(153, 102, 255, 0.8)', // Morado
        ],
        borderColor: [
          'rgba(197, 164, 108, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(117, 20, 40, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Clasificación Temática / Sentimientos (Dummy Data)',
        font: { size: 16 }
      },
    },
  };

  return (
    <div className="content-area">
      <h2 className="page-title">Dashboards Analíticos</h2>
      
      {/* Tarjetas de Métricas Rápidas (KPIs) */}
      <div className="dashboard-kpis">
        <div className="kpi-card">
          <h3>Total de Álbumes</h3>
          <div className="kpi-value">{totalAlbums}</div>
          <p className="kpi-desc">Colecciones indexadas en la base de datos.</p>
        </div>
        
        <div className="kpi-card">
          <h3>Total de Canciones</h3>
          <div className="kpi-value">{totalCanciones}</div>
          <p className="kpi-desc">Letras disponibles para análisis NLP.</p>
        </div>
        
        <div className="kpi-card">
          <h3>Modelo NLP Activo</h3>
          <div className="kpi-value status-ok">Esperando...</div>
          <p className="kpi-desc">Se conectará al backend Python próximamente.</p>
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
