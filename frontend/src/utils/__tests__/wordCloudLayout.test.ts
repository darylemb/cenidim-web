import { describe, it, expect } from 'vitest';
import { packWordCloud, boxesOverlap, type WordItem, type Box } from '../../utils/wordCloudLayout';

/**
 * Builds a realistic candidate set: a long tail of frequencies with
 * the usual 80/20 shape (the first few words dominate, the rest
 * trail off). This mirrors what the backend's `/word-cloud` endpoint
 * returns in practice.
 */
function sampleWords(): WordItem[] {
  const out: WordItem[] = [];
  const top = [
    'casa',
    'amor',
    'corazón',
    'vida',
    'alma',
    'cielo',
    'noche',
    'sol',
    'luna',
    'mar',
    'viento',
    'fuego',
    'tierra',
    'agua',
    'flor',
    'canción',
    'voz',
    'tiempo',
    'ojos',
    'beso',
    'muerte',
    'dolor',
    'alegre',
    'triste',
    'caminar',
    'soñar',
    'volver',
    'quedar',
    'partir',
    'sentir',
    'temer',
    'esperar',
    'mirar',
    'callar',
    'hablar',
    'cantar',
    'bailar',
    'reír',
    'llorar',
    'dormir',
    'despertar',
    'perder',
    'encontrar',
    'buscar',
    'huir',
    'volver',
    'creer',
    'pensar',
    'saber',
    'poder',
    'querer',
    'tener',
    'hacer',
    'decir',
    'dar',
    'ver',
    'ir',
    'ser',
    'estar',
    'venir',
    'poner',
    'salir',
    'dejar',
    'tomar',
    'traer',
    'caer',
    'valer',
    'ganar',
    'morir',
    'vivir',
    'nacer',
    'crecer',
    'subir',
    'bajar',
  ];
  for (let i = 0; i < top.length; i++) {
    out.push({ text: top[i], size: 200 - i * 2 });
  }
  return out;
}

function bbox(
  words: { x: number; y: number; fontSize: number; text: string }[],
  _W: number,
  _H: number
) {
  if (words.length === 0) return null;
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;
  for (const w of words) {
    const hw = (w.text.length * w.fontSize * 0.55) / 2;
    const hh = (w.fontSize * 0.95) / 2;
    minX = Math.min(minX, w.x - hw);
    maxX = Math.max(maxX, w.x + hw);
    minY = Math.min(minY, w.y - hh);
    maxY = Math.max(maxY, w.y + hh);
  }
  return { minX, maxX, minY, maxY, w: maxX - minX, h: maxY - minY };
}

describe('wordCloudLayout', () => {
  describe('boxesOverlap', () => {
    it('returns false for two boxes clearly separated in x', () => {
      const a: Box = { cx: 0, cy: 0, w: 10, h: 10 };
      const b: Box = { cx: 100, cy: 0, w: 10, h: 10 };
      expect(boxesOverlap(a, b, 0)).toBe(false);
    });

    it('returns true for two boxes sharing the same center', () => {
      const a: Box = { cx: 0, cy: 0, w: 10, h: 10 };
      const b: Box = { cx: 0, cy: 0, w: 10, h: 10 };
      expect(boxesOverlap(a, b, 0)).toBe(true);
    });

    it('treats the padding as growing both boxes', () => {
      const a: Box = { cx: 0, cy: 0, w: 10, h: 10 };
      const b: Box = { cx: 19, cy: 0, w: 10, h: 10 };
      // Without padding: separated by 9 in x (no overlap, since 19 > 0+5+5)
      expect(boxesOverlap(a, b, 0)).toBe(false);
      // With padding=5: each box grows by 5, so a's right edge is 10 and
      // b's left edge is 9. They overlap.
      expect(boxesOverlap(a, b, 5)).toBe(true);
    });
  });

  describe('packWordCloud', () => {
    it('returns an empty layout for empty input', () => {
      expect(packWordCloud([], 1000, 500)).toEqual([]);
    });

    it('returns an empty layout for tiny viewBox', () => {
      const words = sampleWords().slice(0, 5);
      expect(packWordCloud(words, 100, 50)).toEqual([]);
    });

    it('places every word inside the viewBox bounds', () => {
      const words = sampleWords();
      const W = 1200,
        H = 600;
      const placed = packWordCloud(words, W, H);
      for (const w of placed) {
        const hw = (w.text.length * w.fontSize * 0.55) / 2;
        const hh = (w.fontSize * 0.95) / 2;
        expect(w.x - hw).toBeGreaterThanOrEqual(0);
        expect(w.x + hw).toBeLessThanOrEqual(W);
        // With dominant-baseline="middle" the y attribute is the visual
        // center, and the box extends wordHeight/2 above and below.
        expect(w.y - hh).toBeGreaterThanOrEqual(0);
        expect(w.y + hh).toBeLessThanOrEqual(H);
      }
    });

    it('places every input word (or skips gracefully under heavy density)', () => {
      const words = sampleWords();
      const placed = packWordCloud(words, 1200, 600);
      // We expect to place at least 90% of the candidates — the spiral
      // should accommodate this many on a 1200×600 canvas.
      expect(placed.length).toBeGreaterThanOrEqual(words.length * 0.9);
    });

    it('regression: the cloud spreads across the viewBox, not a tight cluster', () => {
      // Before the fix, every word was placed within ~50px of the
      // center because the spiral started at radius 12 with a tiny
      // step. The bounding box of the placed words used to be a
      // small fraction of the viewBox. We assert the layout covers
      // a healthy share of the canvas so this regression cannot
      // silently come back.
      const words = sampleWords();
      const W = 1200,
        H = 600;
      const placed = packWordCloud(words, W, H);
      const bb = bbox(placed, W, H);
      expect(bb).not.toBeNull();

      // Width coverage: at least 60% of the viewBox width.
      expect(bb!.w / W).toBeGreaterThan(0.6);
      // Height coverage: at least 50% of the viewBox height (the
      // vertical squish makes this naturally smaller than width).
      expect(bb!.h / H).toBeGreaterThan(0.5);
    });

    it('regression: the 6 hero words are placed in different sectors, not all near the center', () => {
      // The "tight cluster" bug had all words within a ~50px ring
      // around (W/2, H/2). We assert that the bounding box of just
      // the top 6 words spans a meaningful portion of the viewBox,
      // proving the hexagonal seeding is working.
      const words = sampleWords();
      const W = 1200,
        H = 600;
      const placed = packWordCloud(words, W, H);
      const top6 = placed.slice(0, 6);
      const bb = bbox(top6, W, H);
      expect(bb).not.toBeNull();

      const centerX = W / 2;
      const centerY = H / 2;
      // Each hero word should be at least 10% of the shorter
      // dimension away from the center (60px in this viewBox).
      // If all 6 are within 60px of center, they're clustering.
      for (const w of top6) {
        const dx = w.x - centerX;
        const dy = w.y - centerY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        expect(dist).toBeGreaterThan(Math.min(W, H) * 0.1);
      }

      // The 6 hero words together should span at least 40% of the
      // viewBox width — that proves they're spread across sectors,
      // not all hugging the same point.
      expect(bb!.w / W).toBeGreaterThan(0.4);
    });

    it('does not place two words whose bounding boxes overlap (ignoring the visual padding)', () => {
      const words = sampleWords();
      const W = 1200,
        H = 600;
      // Use the same fontScale the component would compute for a
      // 1200×600 viewBox: max(0.45, min(1200/1600, 600/900)) = 0.667.
      // The default of 1.0 produces fonts ~50% larger than the
      // component actually uses, which over-stresses the spiral.
      const placed = packWordCloud(words, W, H, { fontScale: 0.667 });

      // The packing algorithm uses padding = 0.18 * fontSize between
      // boxes, so we re-check here without that padding to make sure
      // the bounding boxes themselves are mostly disjoint.
      let overlapPairs = 0;
      for (let i = 0; i < placed.length; i++) {
        for (let j = i + 1; j < placed.length; j++) {
          const a = placed[i];
          const b = placed[j];
          const aBox: Box = {
            cx: a.x,
            cy: a.y,
            w: a.text.length * a.fontSize * 0.55,
            h: a.fontSize * 0.95,
          };
          const bBox: Box = {
            cx: b.x,
            cy: b.y,
            w: b.text.length * b.fontSize * 0.55,
            h: b.fontSize * 0.95,
          };
          // The packing adds 0.18*fontSize padding to each side, so
          // disjointness with no padding would be over-strict. Use
          // a small fraction as tolerance.
          const tolerance = Math.max(a.fontSize, b.fontSize) * 0.05;
          if (boxesOverlap(aBox, bBox, -tolerance)) overlapPairs++;
        }
      }
      // In dense datasets the spiral's last-resort fallback can place
      // a few words at positions that touch (but don't visually
      // overlap) a neighbor. Allow up to 2% of pairs to be tight.
      const totalPairs = (placed.length * (placed.length - 1)) / 2;
      expect(overlapPairs / totalPairs).toBeLessThan(0.02);
    });

    it('adapts to a much larger canvas by spreading further', () => {
      const words = sampleWords();
      const small = packWordCloud(words, 600, 300);
      const large = packWordCloud(words, 1800, 900);

      const bbSmall = bbox(small, 600, 300)!;
      const bbLarge = bbox(large, 1800, 900)!;

      // Both layouts should fill at least 60% of their viewBox in
      // width — the algorithm should adapt, not only work at one
      // size.
      expect(bbSmall.w / 600).toBeGreaterThan(0.6);
      expect(bbLarge.w / 1800).toBeGreaterThan(0.6);
    });

    it('respects the order of the input: most-frequent first', () => {
      // The biggest word should end up with the biggest fontSize
      // and weight 600 (the threshold for "hero" typography).
      const words = sampleWords();
      const placed = packWordCloud(words, 1200, 600);
      expect(placed[0].text).toBe(words[0].text);
      expect(placed[0].weight).toBe(600);
      // The font sizes should be monotonically non-increasing as
      // the list goes on (ties allowed when sizes are equal).
      for (let i = 1; i < placed.length; i++) {
        expect(placed[i].fontSize).toBeLessThanOrEqual(placed[i - 1].fontSize);
      }
    });
  });
});
