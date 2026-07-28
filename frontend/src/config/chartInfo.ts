/**
 * chartInfo.ts — single source of truth for the long-form
 * descriptions that the dashboard's chart-level info buttons
 * surface. Reviewer feedback (01/jul/2026) asked for explicit
 * definitions of each chart so that the methodology section of
 * the eventual essay can cite the dashboard verbatim.
 *
 * Keep language consistent with `docs/GLOSARIO.md`. If you change
 * a definition here, update the glossary to match.
 */

export interface ChartInfo {
  /** Year-by-year song volume. */
  cancionesPorAnio: string;
  /** Tipología lingüística (ESPAÑOL_ESTANDAR / REGIONAL / INDÍGENA). */
  clasificacion: string;
  /** Canciones agrupadas por tema declarado. */
  tema: string;
  /** Out-of-Vocabulary rate buckets (BAJA / MEDIA / ALTA). */
  oov: string;
  /** Nube de palabras (top-N frecuencia del corpus de letras). */
  nubePalabras: string;
}

export const chartInfo: ChartInfo = {
  cancionesPorAnio:
    'Cada punto representa el total de canciones cuyo fonograma (LP / cassette) tiene como año de publicación ese valor. El bucket “s/d” agrupa los fonogramas sin año asignado. Un mismo disco puede aportar varias canciones si cada pista está individualizada en la tabla `pistas` del CSV.',
  clasificacion:
    'Categorización lingüística calculada por scripts/classify_songs.py sobre el cuerpo de la letra (descarta título, autor, marcadores `Dura: Tema: Personajes:` y paréntesis cortos). Se usa el modelo spaCy `es_core_news_md` y se reporta la categoría dominante: ESPAÑOL_ESTANDAR (vocabulario cotidiano, &lt; 5 % OOV), ESPAÑOL_REGIONAL (regionalismos, 5–18 % OOV) o LENGUA_INDIGENA (palabras de la lista PALABRAS_INDIGENAS o &gt; 18 % OOV).',
  tema: 'Cuenta de canciones por valor del campo `Tema:` (lo que las autoras del cancionero escribieron al pie del .txt, antes de `Personajes:`). Las variantes con distinta capitalización (“Vida/ muerte” vs “Vida/ Muerte”) se colapsan bajo un único bucket canónico (Title Case por segmento). El bucket vacío representa canciones sin `Tema:` y se omite del dashboard.',
  oov: 'Porcentaje de tokens que spaCy `es_core_news_md` no reconoce en su vocabulario, calculado canción por canción. BAJA (&lt; 5 %) sugiere español estándar; MEDIA (5–18 %) sugiere regionalismos; ALTA (&gt; 18 %) sugiere vocabulario indígena o altamente local. La lista cerrada `PALABRAS_INDIGENAS` eleva la canción a LENGUA_INDIGENA aunque el OOV baje.',
  nubePalabras:
    'Top-N (500) palabras más frecuentes extraídas del cuerpo de la letra. El backend normaliza a minúsculas antes de contar (Mamá / mamá colapsan en una sola entrada) y descarta palabras de 1 carácter, stop-words del español estándar y los marcadores de metadatos que el preproceso elimina. El tamaño de fuente refleja la frecuencia logarítmica.',
};
