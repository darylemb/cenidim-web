import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppNavBar from '../AppNavBar.vue'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

function makeWrapper(activeTab = 'timeline', authed = false) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/login', name: 'login', component: { template: '<div />' } },
      { path: '/canciones', name: 'canciones', component: { template: '<div />' } },
      { path: '/admin', name: 'admin', component: { template: '<div />' } },
    ],
  })
  // Use the store hooks (not pinia._s.get) so the reactive refs are
  // wired up correctly before the component mounts.
  const ui = useUiStore(pinia)
  ui.setActiveTab(activeTab)
  if (authed) {
    const auth = useAuthStore(pinia)
    auth.user = { id: 1, username: 'admin', email: 'admin@test', role: 'admin' }
  }
  return mount(AppNavBar, {
    global: { plugins: [pinia, router] },
  })
}

describe('AppNavBar.vue', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders the four main tabs', () => {
    const w = makeWrapper()
    const tabs = w.findAll('.nav-tab')
    expect(tabs.length).toBe(4)
    expect(tabs.map(t => t.text())).toEqual([
      'Línea de tiempo', 'Canciones', 'Dashboards', 'Admin',
    ])
  })

  it('marks the active tab', () => {
    const w = makeWrapper('dashboards')
    // Sanity: did the store actually pick up the new activeTab?
    const ui = w.vm.$.appContext.config.globalProperties.$pinia._s.get('ui')
    expect(ui.activeTab).toBe('dashboards')
    const active = w.find('.nav-tab.active')
    expect(active.text()).toBe('Dashboards')
  })

  it('toggles the mobile menu when the burger is clicked', async () => {
    const w = makeWrapper()
    expect(w.vm.$.appContext.config.globalProperties.$pinia._s.get('ui').mobileMenuOpen).toBe(false)
    await w.find('.menu-toggle').trigger('click')
    expect(w.vm.$.appContext.config.globalProperties.$pinia._s.get('ui').mobileMenuOpen).toBe(true)
  })

  it('navigates to the clicked tab', async () => {
    const w = makeWrapper()
    await w.findAll('.nav-tab')[1].trigger('click') // Canciones
    await flushPromises()
    expect(w.vm.$router.currentRoute.value.name).toBe('canciones')
  })

  it('sends unauthed user to /login when clicking Admin', async () => {
    const w = makeWrapper('timeline', false)
    await w.findAll('.nav-tab')[3].trigger('click')
    await flushPromises()
    expect(w.vm.$router.currentRoute.value.name).toBe('login')
  })

  it('sends authed user to /admin when clicking Admin', async () => {
    const w = makeWrapper('timeline', true)
    await w.findAll('.nav-tab')[3].trigger('click')
    await flushPromises()
    expect(w.vm.$router.currentRoute.value.name).toBe('admin')
  })

  it('select has the four field options', () => {
    const w = makeWrapper()
    const opts = w.findAll('.nav-field-select option')
    expect(opts.length).toBe(4)
    expect(opts.map(o => o.text())).toEqual(['Todos', 'Pista', 'Álbum', 'Letra'])
  })

  it('clicking Buscar triggers a search and navigates to /canciones', async () => {
    const w = makeWrapper()
    await w.find('input[placeholder="Buscar canciones..."]').setValue('mi búsqueda')
    await w.find('.nav-action-btn').trigger('click')
    await flushPromises()
    expect(w.vm.$router.currentRoute.value.name).toBe('canciones')
  })

  it('clicking Reset clears the search term', async () => {
    const w = makeWrapper()
    await w.find('input[placeholder="Buscar canciones..."]').setValue('x')
    await w.find('.nav-btn-reset').trigger('click')
    expect(w.find('input[placeholder="Buscar canciones..."]').element.value).toBe('')
  })
})
