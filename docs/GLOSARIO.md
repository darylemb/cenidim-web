# Glosario CENIDIM — Archivo Musical

> Glosario de términos y métricas del dashboard analítico. Esta es la
> fuente autoritativa para la terminología usada en el ensayo, los
> documentos de trabajo y los productos digitales derivados.
>
> **El frontend tiene tooltips inline ⓘ en cada gráfica**, pero este
> documento existe para (1) servir de referencia para la escritura
> del ensayo, (2) homogeneizar terminología entre los distintos
> equipos de trabajo y (3) sobrevivir al refactor del UI sin perder
> definiciones.
>
> Si una definición cambia, los tooltips en el dashboard se actualizan
> via `frontend/src/config/chartInfo.ts` y este archivo debe
> mantenerse sincronizado.

## Términos del proyecto

### Catálogo
Conjunto total de canciones indexadas en la base de datos. **Es
independiente de cualquier filtro**: su valor nunca cambia al
filtrar por año, tema o clasificación. Sirve como denominador en
las comparativas "Mostrando X de Y".

### Álbum (a.k.a. **Fonograma**)
Un disco LP / cassette físico. Cada álbum agrupa varias canciones.
La tabla `fonogramas` lo modela con su `clave_fonograma` como
primary key. Una misma canción puede existir en varios álbumes si
los autores la grabaron en producciones distintas, en cuyo caso
aparece varias veces en `songs` (no se deduplica).

### Canción / Pista
Una unidad de audio — un registro en la tabla `songs`. Cuando una
canción aparece en varios álbumes, cada aparición cuenta como un
registro separado en las agregaciones. **"Canción" y "Pista" son
intercambiables** en la UI; "Pista" se usa en algunos contextos
heredados (CSV `db_fonografia.pistas`).

### Tema
Categoría temática declarada por el autor del cancionero al pie
del archivo `.txt` (línea `Tema: ...`). **El sistema de
categorización es humano, no automático.** Cuando el archivo
contiene varios temas separados por comas, se conservan todos
(`songs.temas_raw`) y se asigna el primero como `songs.tema`
principal para el dashboard.

Algunos temas son binomios (`Vida/ muerte`, `Equilibrio/
desequilibrio`) y otros son palabras simples (`Familia`,
`Escuela`); la elección refleja la intención del catalogador.

El backend **normaliza variantes de capitalización** (`Vida/
muerte` y `Vida/ Muerte` colapsan en una sola chip) usando
`canonicalTema()` en `handlers/stats.go`.

### Tipología lingüística (clasificación del español)
Categoría que `scripts/classify_songs.py` calcula con spaCy
`es_core_news_md` sobre el cuerpo de la letra (descartando título,
autor, marcadores de metadatos y paréntesis cortos):

| Categoría | Criterio | Lectura sugerida |
|---|---|---|
| `ESPAÑOL_ESTANDAR` | &lt; 5 % OOV | Vocabulario cotidiano del español mexicano |
| `ESPAOL_REGIONAL` | 5–18 % OOV, sin palabras indígenas | Regionalismos (léxico local) sin تجاوز del umbral |
| `LENGUA_INDIGENA` | contiene palabras de `PALABRAS_INDIGENAS` o &gt; 18 % OOV | Vocabulario purépecha, náhuatl u otro |

`OOV` = *Out-of-Vocabulary*: porcentaje de tokens que spaCy no
reconoce en su vocabulario.

### Índice OOV (Out-of-Vocabulary)
Porcentaje de tokens que spaCy `es_core_news_md` no reconoce en
su vocabulario, calculado canción por canción. Se agrupa en
tres buckets para el dashboard:

| Bucket | Rango | Interpretación |
|---|---|---|
| BAJA | &lt; 5 % | Español estándar |
| MEDIA | 5–18 % | Regionalismos |
| ALTA | &gt; 18 % | Vocabulario altamente local o indígena |

### Nube de palabras
Visualización top-N (500) de las palabras más frecuentes del
corpus de letras. Tamaño = frecuencia logarítmica. Posición =
layout en espiral centrada (palabras heroicas en sectores de 60°,
resto espiral hacia afuera). Color = swatch determinístico basado
en hash.

El backend normaliza a minúsculas antes de contar (Mamá y mamá
colapsan) y descarta palabras de 1 carácter, stop-words del
español estándar, y los marcadores de metadatos (Dura:, Tema:,
Personajes:, autor) que el preproceso de lyrics elimina.

## Estructura de la base de datos

```
users                    # Operadores del panel admin (rol: viewer/editor/admin)
user_identities          # Asociación usuario ↔ provider OAuth (post-OAuth)
fonogramas               # Discos físicos (LP/cassette)
songs                    # Pistas (con letra, autor, compositor, duracion, personajes)
song_stats               # Métricas por canción (pct_oov, categoría, contiene_indigena)
```

Para los nombres exactos de las columnas, ver
`backend/database/migrations/`. Las migraciones se ejecutan en
el siguiente orden en el próximo despliegue:

| # | Migración | Propósito |
|---|---|---|
| — | `cmd/build-db/main.go` (CREATE TABLE) | Crea el schema inicial |
| 004 | `user_identities.sql` | Asocia usuario con OAuth |
| 005 | `005_admin_email.sql` | Re-apunta el email del admin al operador |
| 006 | `006_normalize_tema.sql` | No-op; marcador para normalización SQL |
| 007 | `007_song_metadata.sql` | Añade autor, compositor, duracion, personajes |

## Cómo está construida la base de datos

1. **`db-builder` (Go)** parsea `db_fonografia.csv` + `LetrasTXT/*.txt`
   y crea `fonogramas`, `songs` (con `autor`, `compositor`,
   `duracion`, `personajes` extraídos del bloque de metadatos al
   pie del .txt), y un usuario `admin` seed.

2. **`scripts/classify_songs.py`** corre sobre cada canción:
   - Calcula `%OOV` y `categoría` con spaCy `es_core_news_md`.
   - Normaliza `tema` (Title Case por segmento, conservando `/`).
   - Llena `songs.autor / compositor / duracion / personajes` si
     están vacíos.
   - Reemplaza `songs.lyrics` con el cuerpo sin metadatos al pie.

3. **`database/migrations/*.sql`** se ejecutan en cada arranque
   del backend (`database/db.go:53 applyMigrations`). Son
   idempotentes.

## Gráficas del dashboard analítico

| Gráfica | Definición |
|---|---|
| Canciones por año | Conteo de canciones por año del fonograma. `s/d` agrupa fonogramas sin año. |
| Clasificación lingüística | Distribución de canciones por categoría `ESPAÑOL_ESTANDAR / REGIONAL / INDÍGENA`. |
| Por tema | Distribución por `Tema:` literal. Variantes con capitalización distinta colapsan (canonicalTema). |
| Índice OOV | Distribución por bucket BAJA / MEDIA / ALTA. |
| Nube de palabras | Top 500 palabras más frecuentes del corpus de letras. |

Para las definiciones largas exactas, ver
`frontend/src/config/chartInfo.ts` (el `ⓘ` del dashboard surface
esos strings).

## Decisiones de UX que el reviewer documentó (01/jul/2026)

- **Catálogo ≠ Álbumes**: "Catálogo" muestra el total filtro-independiente;
  "Álbumes" se mueve con el filtro. Las hints de cada KPI indican
  explícitamente "Filtrado · N en catálogo" o "Catálogo completo".
- **Top 10 por álbum** se eliminó: el revisor lo marcó como no
  relevante para el análisis.
- **Promedio caracteres** se eliminó: no relevante para el
  análisis.
- **Mamparas temáticas con case-variant** se colapsan en una sola
  chip canónica (Title Case por segmento, conservando `/`).
- **Mamparas de metadatos** (Dura:, M.G.A., (F. Gabilondo S.))
  se extraen a columnas y se eliminan del cuerpo de la letra.
- **Texto de las canciones** se preprocesa para excluir título al
  inicio, autor/compositor al final, y marcadores (Dura:, Tema:,
  Personajes:). El repositorio `letras.db` lleva la versión
  limpia; los originales siguen en `LetrasTXT/`.

## Referencias

- `frontend/src/config/chartInfo.ts` — definiciones largas
  exactas de cada gráfica.
- `backend/handlers/stats.go` (`canonicalTema` y stop words) —
  las reglas de normalización y filtrado autoritativas.
- `backend/cmd/build-db/main.go` (`extractSongMetadata`) — el
  extractor de los metadatos del pie del .txt.
- `scripts/classify_songs.py` — el pipeline Python que calcula
  clasificación OOV y pobla las columnas de metadatos.
