import { createApp } from 'vue';
import { createPinia } from 'pinia';
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
import App from './App.vue';
import router from './router';
import '@/assets/main.css';

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

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
