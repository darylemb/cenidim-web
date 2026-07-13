import { describe, it, expect } from 'vitest'
import { swatchFor, themeSlug, isRawTheme, THEME_SWATCHES } from '../themes'

describe('config/themes', () => {
  it('THEME_SWATCHES is a non-empty array of hex colors', () => {
    expect(THEME_SWATCHES.length).toBeGreaterThan(0)
    for (const c of THEME_SWATCHES) {
      expect(c).toMatch(/^#[0-9a-f]{6}$/i)
    }
  })

  it('swatchFor returns the fallback for empty input', () => {
    expect(swatchFor('')).toBe('#8a7f6e')
  })

  it('swatchFor is deterministic for the same input', () => {
    expect(swatchFor('Amor')).toBe(swatchFor('Amor'))
  })

  it('swatchFor is case-insensitive', () => {
    expect(swatchFor('Amor')).toBe(swatchFor('amor'))
    expect(swatchFor('Amor')).toBe(swatchFor('AMOR'))
  })

  it('swatchFor is stable across input transformations', () => {
    // The function lowercases + strips non-alphanumerics before hashing,
    // so 'Vida/ muerte' and 'Vida  muerte' produce the same hash.
    expect(swatchFor('Vida/ muerte')).toBe(swatchFor('Vida  muerte'))
  })

  it('swatchFor returns one of the swatches', () => {
    expect(THEME_SWATCHES).toContain(swatchFor('Anything'))
  })

  it('themeSlug returns "unclassified" for empty input', () => {
    expect(themeSlug('')).toBe('unclassified')
  })

  it('themeSlug lowercases + replaces non-alphanumerics with hyphens', () => {
    expect(themeSlug('Vida/ muerte')).toBe('vida-muerte')
    expect(themeSlug('Familia')).toBe('familia')
    expect(themeSlug('Equilibrio/Desequilibrio')).toBe('equilibrio-desequilibrio')
  })

  it('isRawTheme returns false for empty input', () => {
    expect(isRawTheme('')).toBe(false)
  })

  it('isRawTheme detects a slash duality as a strong signal', () => {
    expect(isRawTheme('Vida/ muerte')).toBe(true)
    expect(isRawTheme('A/B')).toBe(true)
  })

  it('isRawTheme rejects an all-caps keyword-only token', () => {
    // A bare all-caps token with no slash and no lowercase letter is
    // the classifier's old canonical form, not a raw Tema: literal.
    expect(isRawTheme('AMOR')).toBe(false)
    expect(isRawTheme('JUEGO')).toBe(false)
  })

  it('isRawTheme accepts a value with a lowercase letter', () => {
    expect(isRawTheme('Amor')).toBe(true)
    expect(isRawTheme('juego')).toBe(true)
  })
})
