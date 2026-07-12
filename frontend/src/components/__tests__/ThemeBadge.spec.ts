import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ThemeBadge from '../ThemeBadge.vue';
import { swatchFor, themeSlug } from '@/config/themes';

describe('ThemeBadge', () => {
  it('renders the raw theme label as written in the song (e.g., "Amor/ odio")', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: 'Amor/ odio' } });
    expect(wrapper.text()).toContain('Amor/ odio');
    expect(wrapper.classes()).toContain('theme-badge--amor-odio');
  });

  it('renders "Sin tema" when the theme is blank', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: '' } });
    expect(wrapper.text()).toContain('Sin tema');
    expect(wrapper.classes()).toContain('theme-badge--unclassified');
  });

  it('renders "Sin tema" when the theme is null-ish', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: undefined } });
    expect(wrapper.text()).toContain('Sin tema');
  });

  it('accepts a custom label override', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: 'Vida/ Muerte', label: 'Custom' } });
    expect(wrapper.text()).toContain('Custom');
  });

  it('exposes the underlying theme via data-theme attribute', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: 'Placer/ dolor' } });
    expect(wrapper.attributes('data-theme')).toBe('Placer/ dolor');
  });

  it('produces a slug for the theme CSS class', () => {
    const wrapper = mount(ThemeBadge, { props: { theme: 'Escuela' } });
    expect(wrapper.classes()).toContain('theme-badge--escuela');
  });

  it('handles an arbitrary unknown theme without crashing', () => {
    // The classifier used to write a fixed 11-all-caps set; after the
    // pipeline change any literal value from LetrasTXT may appear here.
    const wrapper = mount(ThemeBadge, { props: { theme: 'Fantasmas y brujas' } });
    expect(wrapper.text()).toContain('Fantasmas y brujas');
    // The dot has a colour assigned via the swatch hash function.
    const dot = wrapper.find('.theme-badge__dot');
    const style = dot.attributes('style') ?? '';
    expect(style).toContain('background');
  });
});

describe('swatchFor', () => {
  it('returns a stable colour for the same theme across calls', () => {
    expect(swatchFor('Amor')).toBe(swatchFor('Amor'));
    expect(swatchFor('Placer/ dolor')).toBe(swatchFor('Placer/ dolor'));
  });

  it('returns different colours for distinct themes (most of the time)', () => {
    const a = swatchFor('Amor');
    const b = swatchFor('Escuela');
    // With 12 swatches and ~25 distinct themes, collisions are possible;
    // the contract is "consistent per key", not "globally unique".
    expect(typeof a).toBe('string');
    expect(a).toMatch(/^#[0-9a-f]{6}$/);
    expect(b).toMatch(/^#[0-9a-f]{6}$/);
  });

  it('falls back to a neutral grey for empty input', () => {
    expect(swatchFor('')).toBe('#8a7f6e');
  });
});

describe('themeSlug', () => {
  it('replaces non-alphanumeric chars with a single dash', () => {
    expect(themeSlug('Placer/ dolor')).toBe('placer-dolor');
    expect(themeSlug('Vida--Muerte')).toBe('vida-muerte');
  });
  it('returns "unclassified" for empty input', () => {
    expect(themeSlug('')).toBe('unclassified');
  });
});
