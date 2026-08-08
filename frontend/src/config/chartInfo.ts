/**
 * chartInfo.ts — single source of truth for the long-form
 * descriptions that the dashboard's chart-level info buttons
 * surface. Written for a NON-TECHNICAL audience (the artistic /
 * research team): no spaCy, tokens, OOV, or developer acronyms.
 *
 * If you change a definition here, update docs/GLOSARIO.md to match.
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
    'Cada punto muestra cuántas canciones del archivo tienen ese año de publicación (el del disco donde aparecieron). El recuadro "s/d" agrupa los discos a los que aún no se les ha asignado año. Si un disco tiene varias canciones, cada canción cuenta por separado.',
  clasificacion:
    'Cómo se habla en la letra de cada canción, según el programa de análisis de texto del archivo. Se divide en tres grupos:\n- Estándar: vocabulario de todos los días.\n- Regional: incluye palabras y expresiones propias de regiones de México.\n- Indígena: incluye palabras de lenguas indígenas, o vocabulario muy poco común.\nCada canción se clasifica en el grupo que mejor la describe.',
  tema: 'Cuenta de canciones por el tema que las autoras del cancionero escribieron al pie de cada letra. Las variantes con mayúsculas o espacios distintos (p. ej. "Vida/ muerte" y "Vida/ Muerte") se unen en un solo tema. Las canciones sin tema no aparecen en esta gráfica.',
  oov: 'Qué tan cotidiano o especializado es el vocabulario de las letras.\n- Baja: palabras comunes, fáciles de entender.\n- Media: hay algunas palabras poco frecuentes o regionales.\n- Alta: vocabulario poco común, antiguo o de lenguas indígenas.\nEs una forma rápida de ver si las canciones usan lenguaje de todos los días o uno más especializado.',
  nubePalabras:
    'Las palabras que más se repiten en las letras del archivo. Las palabras más grandes son las que aparecen con más frecuencia. Se ignoran palabras vacías (como "el", "de", "que"), números y encabezados, para que solo se vean palabras con contenido.',
};
