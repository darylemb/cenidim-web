/**
 * Dynamic theme palette for the word cloud + theme chips + ThemeBadge.
 *
 * Unlike the previous canonical-list approach, the themes shown in the
 * UI come from the actual `Tema: ...` field at the end of each song
 * file in `LetrasTXT/*.txt` (see `scripts/classify_songs.py`). Those
 * values are written by the human cataloguers and are the source of
 * truth — we do NOT infer them via keyword matching.
 *
 * Because the raw `Tema:` values are free-form Spanish (with case
 * variations, slashes for dualities like "Placer/ dolor", occasional
 * typos), this module exposes a *curated* palette of swatches that we
 * cycle through deterministically by hashing the theme key. New themes
 * get the next swatch; nothing crashes on an unknown value.
 */

// Brand-aligned swatches (12). These mirror the canonical set so a song
// tagged "Amor" or "Escuela" gets a recognisable colour, but the
// rotation ensures every distinct literal value (e.g. "Equilibrio/
// Desequilibrio" vs "Equilibrio/ desequilibrio") still gets its own
// consistent colour across the dashboard.
export const THEME_SWATCHES = [
  '#751428', // vino
  '#c5a46c', // mostaza
  '#6b8068', // sage
  '#c97a4a', // terracota
  '#2c4a6e', // azul tinta
  '#9a2a2a', // granada
  '#7c3aed', // religioso
  '#1d4ed8', // patriotico
  '#047857', // navidad
  '#d97706', // fiesta
  '#be185d', // amor
  '#a16207', // ocre
];

/** Stable hash → swatch index. Same theme always gets the same colour. */
export function swatchFor(theme: string): string {
  if (!theme) return '#8a7f6e';
  const k = theme.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  let h = 0;
  for (let i = 0; i < k.length; i++) {
    h = (h * 31 + k.charCodeAt(i)) >>> 0;
  }
  return THEME_SWATCHES[h % THEME_SWATCHES.length];
}

/** Returns a CSS class slug suitable for component-scoped selectors. */
export function themeSlug(theme: string): string {
  if (!theme) return 'unclassified';
  return theme.toLowerCase().replace(/[^a-z0-9]+/g, '-');
}

/** True if the literal value came from a `Tema:` line in LetrasTXT. */
export function isRawTheme(value: string): boolean {
  // Heuristic: a raw theme contains a slash duality or a known concept
  // word, OR is non-empty after trim. The classifier used to write
  // 11-all-caps tokens; the raw themes are mixed-case Spanish. The
  // presence of a lowercase letter OR a slash is a strong signal.
  if (!value) return false;
  if (value.includes('/')) return true;
  return /[a-záéíóúñ]/.test(value);
}
