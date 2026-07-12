/**
 * Word cloud packing algorithm.
 *
 * The component is a thin Vue wrapper around two pure functions:
 *   - `packWordCloud` runs the layout
 *   - `boxesOverlap` is the AABB collision check
 *
 * Keeping the algorithm pure (no Vue refs, no DOM, no fetch) lets us
 * unit-test the geometry in isolation: the fix that addressed the
 * "tight cluster" regression (top hero words claiming one sector each)
 * is verified by checking that the bounding box of the placed words
 * covers a healthy share of the viewBox, not just the center.
 */

export interface WordItem {
  text: string;
  size: number;
}

export interface LayoutWord extends WordItem {
  x: number;
  y: number;
  fontSize: number;
  color: string;
  weight: number;
  fontFamily: string;
}

export interface Box {
  cx: number;
  cy: number;
  w: number;
  h: number;
}

export interface PackOptions {
  /** Pixels per em for the smallest word in the layout. */
  minFontSize?: number;
  /** Pixels per em for the largest word. */
  maxFontSize?: number;
  /** Top-N words get the wider spiral. */
  heroLimit?: number;
  /** Radial step for the hero spiral. */
  heroRadialStep?: number;
  /** Radial step for medium/small words. */
  mediumRadialStep?: number;
  /** Angular step in radians. */
  angleStep?: number;
  /** Top-N hero words seeded on a ring around the center. */
  heroDistributeCount?: number;
  /** Padding between boxes as a fraction of fontSize. */
  paddingFactor?: number;
  /** Char-width factor (em → px). */
  charWidthFactor?: number;
  /** Vertical squish of the spiral (1.0 = circle, <1.0 = horizontal). */
  verticalSquish?: number;
  /** Palette for `color`. Cycled by index. */
  palette?: string[];
  /** Font for the biggest words. */
  heroFontFamily?: string;
  /** Font for the rest. */
  bodyFontFamily?: string;
  /** Boundary margin in px. */
  margin?: number;
  /** Max spiral iterations per word. */
  maxIterations?: number;
  /** Optional scale applied to font sizes (e.g. for viewport scaling). */
  fontScale?: number;
}

const DEFAULT_PALETTE = [
  '#1a1612',
  '#751428',
  '#c5a46c',
  '#c97a4a',
  '#6b8068',
  '#2c4a6e',
  '#9a2a2a',
  '#7c3aed',
  '#1d4ed8',
  '#047857',
  '#d97706',
  '#be185d',
  '#4a4239',
  '#8a7f6e',
  '#a16207',
  '#3a3128',
];

/**
 * Axis-aligned bounding-box overlap check.
 *
 * Two boxes overlap iff they overlap in BOTH x and y. The padding
 * grows each box by `padding` on every side — that means the
 * effective minimum distance between two word centers is
 * `(a.w + b.w)/2 + 2*padding` in x, and the same with h in y.
 */
export function boxesOverlap(a: Box, b: Box, padding: number): boolean {
  return !(
    a.cx - a.w / 2 - padding > b.cx + b.w / 2 + padding ||
    a.cx + a.w / 2 + padding < b.cx - b.w / 2 - padding ||
    a.cy - a.h / 2 - padding > b.cy + b.h / 2 + padding ||
    a.cy + a.h / 2 + padding < b.cy - b.h / 2 - padding
  );
}

/**
 * Pack a list of words into a rectangular canvas of size W×H.
 *
 * Words are processed in the order given (caller sorts by frequency
 * descending). The first `heroDistributeCount` words start on a ring
 * at evenly-spaced angles so the biggest words claim distinct
 * sectors. The remaining words spiral outward from the center with
 * a wide step so the layout fills the canvas instead of clustering.
 *
 * Font sizes follow a single eased curve (no hero/non-hero jump), so
 * visual hierarchy is progressive instead of abrupt.
 */
export function packWordCloud(
  words: WordItem[],
  W: number,
  H: number,
  options: PackOptions = {}
): LayoutWord[] {
  if (words.length === 0 || W < 200 || H < 120) return [];

  const opts = {
    minFontSize: 0.04,
    maxFontSize: 0.16,
    heroLimit: 40,
    heroRadialStep: 22,
    mediumRadialStep: 18,
    angleStep: 0.42,
    heroDistributeCount: 6,
    // Padding between word boxes, as a fraction of the word's
    // font size. Bumped from 0.18 → 0.28 in response to reviewer
    // feedback 01/jul/2026 ("zona con palabras encimadas"). The
    // trade-off is that fewer words fit per canvas, but the
    // remaining ones read as discrete units.
    paddingFactor: 0.28,
    charWidthFactor: 0.55,
    verticalSquish: 0.82,
    palette: DEFAULT_PALETTE,
    heroFontFamily: "'Fraunces', serif",
    bodyFontFamily: "'Outfit', sans-serif",
    margin: 4,
    maxIterations: 20000,
    fontScale: 1,
    ...options,
  };

  const sorted = [...words];
  const maxSize = sorted[0]?.size || 1;
  const minSize = sorted[sorted.length - 1]?.size || 1;

  const placed: Box[] = [];
  const result: LayoutWord[] = [];

  const centerX = W / 2;
  const centerY = H / 2;
  const minDim = Math.min(W, H);

  for (let i = 0; i < sorted.length; i++) {
    const word = sorted[i];
    const normalizedSize = (word.size - minSize) / (maxSize - minSize + 1);
    const isHero = i < opts.heroLimit;

    // Single continuous scale: low frequencies are gently compressed,
    // high frequencies expand smoothly. This avoids a visible "step"
    // between hero and non-hero buckets.
    const easedSize = Math.pow(Math.max(0, Math.min(1, normalizedSize)), 0.72);
    const minPx = minDim * 0.020;
    const maxPx = minDim * 0.118;
    const fontSize = (minPx + easedSize * (maxPx - minPx)) * opts.fontScale;

    const padding = fontSize * opts.paddingFactor;
    const wordWidth = word.text.length * fontSize * opts.charWidthFactor;
    const wordHeight = fontSize * 0.95;

    let bestPos: { x: number; y: number; dist: number } | null = null;
    let placedHere = false;
    const distributed = i < opts.heroDistributeCount;
    const startAngle = distributed ? (i / opts.heroDistributeCount) * Math.PI * 2 : 0;
    // Hero words are seeded on a ring at 0.28 × minDim so the biggest
    // words claim distinct sectors without hugging the borders.
    // Remaining words start progressively farther out, but with an
    // offset so the center still gets medium-size words and the cloud
    // reads as one compact shape (instead of an upper/lower split).
    const remainingCount = sorted.length - opts.heroDistributeCount;
    const remainingRank = Math.max(0, i - opts.heroDistributeCount);
    const remainingRatio = remainingCount <= 1 ? 0 : remainingRank / (remainingCount - 1);
    const startRadius = distributed ? minDim * 0.28 : minDim * (0.10 + 0.45 * remainingRatio);
    for (let spiral = 0; spiral < opts.maxIterations; spiral++) {
      const angle = startAngle + spiral * opts.angleStep;
      const radius =
        startRadius +
        (isHero ? opts.heroRadialStep : opts.mediumRadialStep) * Math.sqrt(spiral + 1);
      const testX = centerX + radius * Math.cos(angle);
      const testY = centerY + radius * Math.sin(angle) * opts.verticalSquish;

      if (
        testX - wordWidth / 2 < opts.margin ||
        testX + wordWidth / 2 > W - opts.margin ||
        testY - wordHeight / 2 < opts.margin ||
        testY + wordHeight / 2 > H - opts.margin
      ) {
        continue;
      }

      const box: Box = { cx: testX, cy: testY, w: wordWidth, h: wordHeight };

      let overlaps = false;
      for (const p of placed) {
        if (boxesOverlap(box, p, padding)) {
          overlaps = true;
          break;
        }
      }

      if (!overlaps) {
        placed.push(box);
        result.push({
          ...word,
          x: testX,
          y: testY,
          fontSize,
          color: opts.palette[i % opts.palette.length],
          weight: normalizedSize > 0.74 ? 600 : normalizedSize > 0.46 ? 500 : 400,
          fontFamily: isHero && normalizedSize > 0.45 ? opts.heroFontFamily : opts.bodyFontFamily,
        });
        placedHere = true;
        break;
      }

      const dist = Math.sqrt((testX - centerX) ** 2 + (testY - centerY) ** 2);
      if (bestPos === null || dist < bestPos.dist) {
        bestPos = { x: testX, y: testY, dist };
      }
    }

    if (!placedHere && bestPos) {
      const testX = bestPos.x;
      const testY = bestPos.y;
      const box: Box = { cx: testX, cy: testY, w: wordWidth, h: wordHeight };
      placed.push(box);
      result.push({
        ...word,
        x: testX,
        y: testY,
        fontSize,
        color: opts.palette[i % opts.palette.length],
        weight: 400,
        fontFamily: opts.bodyFontFamily,
      });
    }
  }

  return result;
}
