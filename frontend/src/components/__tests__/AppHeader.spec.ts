import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import AppHeader from '../AppHeader.vue';
import { useAuthStore } from '@/stores/auth';

const RouterStub = {
  template: '<div data-testid="router-stub" />',
};

function makeWrapper(authed = false) {
  const pinia = createPinia();
  setActivePinia(pinia);
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: RouterStub },
      { path: '/login', name: 'login', component: RouterStub },
    ],
  });
  const AppNavBarStub = { template: '<div data-testid="nav-stub" />' };
  if (authed) {
    const auth = useAuthStore(pinia);
    auth.user = { id: 1, username: 'admin', email: 'admin@test', role: 'admin' };
  }
  return mount(AppHeader, {
    global: {
      plugins: [pinia, router],
      stubs: { AppNavBar: AppNavBarStub },
    },
  });
}

describe('AppHeader.vue', () => {
  beforeEach(() => setActivePinia(createPinia()));

  it('renders the CENIDIM branding', () => {
    const w = makeWrapper();
    expect(w.find('.logo-icon-small').text()).toBe('C');
    expect(w.find('h2').text()).toBe('CENIDIM');
    expect(w.text()).toContain('Archivo Musical');
  });

  it('shows "Acceder" button when not authed', () => {
    const w = makeWrapper(false);
    const btn = w.find('.btn-primary');
    expect(btn.exists()).toBe(true);
    expect(btn.text()).toBe('Acceder');
  });

  it('shows username + role badge + Cerrar when authed', () => {
    const w = makeWrapper(true);
    expect(w.find('.header-user').exists()).toBe(true);
    expect(w.find('.header-username').text()).toBe('admin');
    expect(w.find('.role-badge').text()).toBe('Administrador');
    expect(w.text()).toContain('Cerrar');
    expect(w.find('.btn-primary').exists()).toBe(false);
  });

  it('clicking Acceder pushes /login', async () => {
    const w = makeWrapper(false);
    await w.find('.btn-primary').trigger('click');
    await flushPromises();
    // openAuth() in the component routes to the /login name.
    expect(w.vm.$router.currentRoute.value.name).toBe('login');
  });
});

it.skip('openAuth navigates to /login when invoked', async () => {
  const w = makeWrapper(false);
  // The "Acceder" button's @click is bound to openAuth; triggering
  // it exercises the openAuth path which pushes /login.
  await w.find('.btn-primary').trigger('click');
  expect(w.vm.$router.currentRoute.value.name).toBe('login');
});
