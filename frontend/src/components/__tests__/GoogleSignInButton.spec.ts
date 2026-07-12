import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import GoogleSignInButton from '../GoogleSignInButton.vue';

describe('GoogleSignInButton', () => {
  it('renders an anchor to /api/auth/google/start by default', () => {
    const wrapper = mount(GoogleSignInButton);
    const link = wrapper.find('a');
    expect(link.exists()).toBe(true);
    expect(link.attributes('href')).toBe('/api/auth/google/start');
  });

  it('renders the unavailable label when prop is set', () => {
    const wrapper = mount(GoogleSignInButton, { props: { unavailable: true } });
    expect(wrapper.find('a').exists()).toBe(false);
    const btn = wrapper.find('button');
    expect(btn.exists()).toBe(true);
    expect(btn.text()).toContain('temporalmente no disponible');
    expect(btn.attributes('disabled')).toBeDefined();
  });

  it('includes the Google logo and the localized label', () => {
    const wrapper = mount(GoogleSignInButton);
    expect(wrapper.find('svg').exists()).toBe(true);
    expect(wrapper.text()).toContain('Continuar con Google');
  });
});
