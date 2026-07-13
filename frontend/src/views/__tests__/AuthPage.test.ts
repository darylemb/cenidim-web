import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AuthPage from '../AuthPage.vue'
import { apiService } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/api', () => ({
  apiService: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
  },
}))

function makeWrapper(initialRoute = '/login') {
  setActivePinia(createPinia())
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: { template: '<div />' } },
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/reset', name: 'reset', component: { template: '<div />' } },
    ],
  })
  router.push(initialRoute).catch(() => {})
  return mount(AuthPage, {
    global: { plugins: [router] },
  })
}

describe('AuthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login and register tabs', () => {
    const w = makeWrapper()
    expect(w.text()).toContain('Iniciar Sesión')
    expect(w.text()).toContain('Registrarse')
  })

  it('renders login form fields', () => {
    const w = makeWrapper()
    expect(w.find('input#username').exists()).toBe(true)
    expect(w.find('input#password').exists()).toBe(true)
  })

  it('switches to register mode and reveals the email field', async () => {
    const w = makeWrapper()
    // Click "Registrarse" tab
    await w.findAll('button').find(b => b.text() === 'Registrarse')!.trigger('click')
    expect(w.find('input#email').exists()).toBe(true)
  })

  it('submits login with username + password', async () => {
    vi.mocked(apiService.login).mockResolvedValue({
      token: 'fake',
      user: { id: 1, username: 'test', email: 't@t.com', role: 'admin' },
    })
    const w = makeWrapper()
    await w.find('input#username').setValue('admin')
    await w.find('input#password').setValue('admin123')
    await w.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(apiService.login).toHaveBeenCalledWith('admin', 'admin123')
  })

  it('submits register with email + username + password', async () => {
    vi.mocked(apiService.register).mockResolvedValue({
      token: 'fake',
      user: { id: 2, username: 'new', email: 'new@x', role: 'viewer' },
    })
    const w = makeWrapper()
    await w.findAll('button').find(b => b.text() === 'Registrarse')!.trigger('click')
    await w.find('input#username').setValue('new')
    await w.find('input#email').setValue('new@x')
    await w.find('input#password').setValue('S3cret!')
    await w.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(apiService.register).toHaveBeenCalledWith('new', 'new@x', 'S3cret!')
  })

  it('opens the forgot-password modal when "¿Olvidaste…?" is clicked', async () => {
    const w = makeWrapper()
    await w.findAll('button').find(b => b.text().includes('¿Olvidaste'))!.trigger('click')
    expect(w.text()).toContain('Recuperar contraseña')
  })

  it('submits the forgot form with the typed email', async () => {
    vi.mocked(apiService.forgotPassword).mockResolvedValue({ ok: true })
    const w = makeWrapper()
    await w.findAll('button').find(b => b.text().includes('¿Olvidaste'))!.trigger('click')
    await w.find('input#forgot-email').setValue('lost@test')
    await w.findAll('form').at(-1)!.trigger('submit.prevent')
    await flushPromises()
    expect(apiService.forgotPassword).toHaveBeenCalledWith('lost@test')
  })

  // The Google OAuth callback path moved to the admin linking flow
  // (Fase 6), so this test stays a no-op until that branch is wired.
  it('forgotPassword reports a friendly error when the API throws', async () => {
    vi.mocked(apiService.forgotPassword).mockRejectedValueOnce(new Error('Upstream down'))
    const w = makeWrapper()
    await w.findAll('button').find(b => b.text().includes('¿Olvidaste'))!.trigger('click')
    await w.find('input#forgot-email').setValue('user@x')
    await w.findAll('form').at(-1)!.trigger('submit.prevent')
    await flushPromises()
    expect(w.text()).toContain('Upstream down')
  })
})
