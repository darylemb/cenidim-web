import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'timeline',
      component: () => import('@/views/TimelineView.vue'),
    },
    {
      path: '/canciones',
      name: 'canciones',
      component: () => import('@/views/CancionesView.vue'),
    },
    {
      path: '/dashboards',
      name: 'dashboards',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminPanel.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/AuthPage.vue'),
    },
  ],
});

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return;
  const auth = useAuthStore();
  // restoreSession() resolves once /auth/me has been probed (or the
  // request failed and the token was cleared). If we hit a `requiresAuth`
  // route while that probe is still in flight — the typical "F5 on a
  // logged-in session" path — the guard must wait instead of
  // short-circuiting to /login.
  if (auth.authLoading) {
    try {
      await auth.restoreSession();
    } catch {
      // restoreSession swallows the network error; nothing to do here.
    }
  }
  if (!auth.isAuthenticated) {
    return { name: 'login' };
  }
});

export default router;
