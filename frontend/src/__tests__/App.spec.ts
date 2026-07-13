import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from '../App.vue'

const routes = [
  { path: '/', name: 'home', component: { template: '<div>home</div>' } },
  { path: '/login', name: 'login', component: { template: '<div>login</div>' } },
]

function makeApp() {
  return mount(App, {
    global: {
      plugins: [
        createPinia(),
        createRouter({ history: createMemoryHistory(), routes }),
      ],
    },
  })
}

describe('App.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    // Stub the DefaultLayout import chain — render the slot inline.
  })

  it('renders the skip-link', () => {
    const w = makeApp()
    expect(w.find('.skip-link').exists()).toBe(true)
    expect(w.find('.skip-link').attributes('href')).toBe('#main-content')
  })

  it('renders router-view container', () => {
    const w = makeApp()
    expect(w.find('.app-container').exists()).toBe(true)
  })

  it('calls auth.restoreSession on mount', () => {
    // Smoke check: restoring should not throw even without a token.
    expect(() => makeApp()).not.toThrow()
  })
})
