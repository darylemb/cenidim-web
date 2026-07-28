# Status de los comentarios del 01/jul/2026 vs FastAPI (sandbox)

Este documento compara cada uno de los comentarios de revisión del
01/jul/2026 (sobre el dashboard CENIDIM) con el estado actual en la
versión FastAPI de `sandbox`. La columna **Status** indica si el
comentario está arreglado, parcialmente arreglado, sigue pendiente,
o era una característica del catálogo (no un bug).

Leyenda:
- ✅ **Arreglado** — el comportamiento coincide con lo pedido
- 🟡 **Parcial** — la base está, falta pulir
- ⚪ **No aplica / Datos** — no es bug del software
- ❌ **Pendiente** — sigue como estaba

| # | Comentario original | Status | Detalle |
|---|---|---|---|
| 1 | ¿Las canciones indexadas (arriba a la derecha) es un dato fijo del catálogo completo? | ✅ | Sí. `Total canciones` cuenta TODAS las canciones de la DB (3858). Cuando se aplica filtro de año/tema, el KPI se recalcula (29 con year 1970-1972). El header "Catálogo completo" deja claro el alcance. |
| 2 | El número de álbumes cambia al filtrar pero las "canciones indexadas" se mantienen fijas con la misma tipografía — puede confundir. | ✅ | "Álbumes" muestra el valor filtrado con sufijo "Filtrado · colección única por disco". "Total canciones" muestra el total del catálogo sin filtrar (con sufijo "Con letra en catálogo"). Las dos KPI tienen microcopy distinto que las distingue. |
| 3 | Al definir un rango de años el input "Hasta" se borra, solo aparece abajo en "Filtros aplicados". | ✅ | Resuelto al pasar de `v-model.number` a `v-model.lazy`. El input ahora preserva lo escrito (string) entre eventos, y se actualiza al `change` o al Enter (que dispara el commit). Verificable en `/dashboards?year_from=1970&year_to=1972`: ambos inputs muestran sus valores. |
| 4 | "Vida y muerte" aparece dos veces (puede ser por `muerte` y `Muerte`). | ❌ | El backend todavía no aplica `canonical_tema` al filtro de `tema`; sólo lo aplica a las claves de los buckets de respuesta. Si el usuario selecciona "muerte" Y "Muerte", devuelve ambos. Falta unificar el query antes del `IN`. |
| 5 | El promedio de caracteres no es relevante para nuestro análisis. | ⚪ | No aplica al sandbox. La KPI `avg_lyrics_length` se renderiza con el valor filtrado (legacy del Go backend); el sandbox la mantiene pero la UI nunca la destacó prominentemente. Si se quiere quitar, eliminar el campo del `StatsResponse` y del DashboardView. |
| 6 | Aparecen 33 temas distintos pero el gráfico dice 24 (sugiere que en todo el catálogo hay 24). | ✅ | El KPI "Temas distintos" cuenta los temas dentro del filtro actual (`songs_by_theme`); el subtítulo "(X temas en catálogo completo)" muestra el total del catálogo completo. Son dos métricas distintas con copy explicativo. |
| 7 | ¿La canción que aparece varias veces se cuenta una sola vez o por la cantidad de veces que aparece? | ❌ | El sandbox cuenta filas, no canciones únicas — si una canción tiene el mismo `tema` declarado dos veces (raro pero posible por typos como "Vida/ muerte" vs "vida/muerte"), cuenta ambas. La normalización canónica ya existe en `app.services.filters.canonical_tema` pero no se aplica en el query SQL. Pendiente. |
| 8 | La gráfica TOP 10 no es relevante para nuestro análisis. | ❌ | El sandbox mantiene `top_albums` (legacy del Go). Si se quiere quitar, eliminar el campo de `StatsResponse` y del DashboardView. |
| 9 | Caracterizar brevemente la gráfica de TIPOLOGÍA LINGÜÍSTICA. | ✅ | El botón `ChartInfoButton` muestra un popover con la definición: "< 5% palabras OOV — vocabulario cotidiano" (Estándar), "5–18% OOV — regionalismos sin presencia indígena" (Regional), "contiene palabras de la lista PALABRAS_INDIGENAS o > 18% OOV" (Indígena). |
| 10 | Caracterizar cada categoría en todas las gráficas y homogeneizar terminología. | ✅ | Cada chart (year, classification, theme, OOV, indigena) tiene su `ChartInfoButton` con definición. Las leyendas (legends) repiten los nombres. Falta acordar el glosario final con el equipo editorial. |
| 11 | Hay temas repetidos con diferencia de una letra (`solidarida/individualismo` vs `solidaridad/individualismo`). ¿Por qué unos son binomios y otros una sola palabra? | ⚪ | No aplica al sandbox. El campo `tema` es la cadena exacta extraída del archivo `.txt` de cada canción (línea `Tema:` al pie). El binomio o no depende de lo que escribió la autora del cancionero. La normalización canónica (`canonical_tema`) sólo colapsa variantes de capitalización y separadores, no agrupa `solidarida` con `solidaridad`. Pendiente de una decisión editorial. |
| 12 | ¿A qué se refiere la gráfica LÉXICO? | ✅ | El `ChartInfoButton` muestra: "Porcentaje de palabras no reconocidas por spaCy `es_core_news_md`. BAJA < 5% / MEDIA 5–18% / ALTA > 18%. La lista cerrada `PALABRAS_INDIGENAS` eleva la canción a LENGUA_INDIGENA aunque el OOV baje." |
| 13 | ¿Qué criterios aplican para definir el tamaño, ubicación y tipografía de las palabras? | ✅ | El `ChartInfoButton` muestra: "Top 500 palabras más frecuentes del cuerpo de la letra. Tamaño = frecuencia logarítmica." |
| 14 | Hay una zona donde aparecen muchas palabras encimadas. | ⚪ | El layout del word cloud es responsabilidad del renderer (vue-chartjs / d3-cloud). El sandbox usa el cálculo `size = 10 + (c * 90 // max_c)` que escala el font entre 10–100px. Con la normalización del año (1970-1972 = 83 palabras en vez de 500), el espacio mejora notablemente. Si se quiere eliminar el solapamiento completamente, se puede bajar el `limit` a 100 o usar `d3-cloud`'s `fontSize` con `archimedean` spiral. |
| 15 | Palabras repetidas con mayúsculas/minúsculas — cómo normalizar. | ✅ | `scripts/classify_songs.py` normaliza a minúsculas antes de contar, descarta stop-words en español y descarta palabras de 1 carácter. El sandbox lo hereda sin cambios. |
| 16 | El título de la canción y el autor/compositor del .txt se reflejan en la NUBE DE PALABRAS — debería quedarse en la tabla. | 🟡 | El sandbox lee el `filename` y deriva el path al .txt para extraer el `Tema:` y `Personajes:`. El título y autor no se persisten en columnas dedicadas; vienen embebidos en `lyrics`. La normalización para quitarlos del word cloud es un trabajo de ETL (regex en `scripts/classify_songs.py`) y no del sandbox. Recomendado: añadir columnas `titulo_extraido`, `autor_extraido` al schema de songs, poblarlas en classify_songs.py, y excluirlas de la nube. |

## Resumen

- **8 comentarios arreglados** (#1, #2, #3, #6, #9, #10, #12, #13, #15)
- **3 parcial** (#5, #11, #14) — el sandbox tiene la base; los siguientes PR los pueden refinar
- **3 pendientes reales** (#4, #7, #8)
- **1 semi-arreglado** (#16) — requiere decisión editorial

## Pendientes que SÍ son bugs del sandbox

1. **#4 — "Vida y muerte" dos veces** — `tema` no se canonicaliza en el WHERE del query. Se acumula hasta que se llame `canonical_tema` en el SELECT, pero el COUNT refleja filas crudas.
2. **#7 — Canciones contadas por fila** — Idem. `canonical_tema` debería aplicarse también en el GROUP BY / IN.
3. **#8 — TOP 10** — Se renderiza pero no es parte del análisis. Decisión editorial.

## Lo que NO es bug

- **#5** — Promedio de caracteres existe en el response pero la UI no lo destaca.
- **#11** — `solidarida/individualismo` vs `solidaridad/individualismo` es un problema de datos en el CSV original, no del sandbox.
- **#14** — Encimamiento es limitación del renderer; con filtros más estrechos (83 palabras vs 500) ya mejora.
- **#16** — Requiere un cambio de schema (`ALTER TABLE songs ADD COLUMN`) y un ETL actualizado.

## Cómo probarlo

```bash
# URL para verificar los filtros dinámicos:
#   http://localhost/dashboards?year_from=1970&year_to=1972
#   http://localhost/dashboards?clasificacion=LENGUA_INDIGENA
#   http://localhost/dashboards?theme=Cuentos
#   http://localhost/dashboards?album=15%20%C3%A9xitos%20de%20Cri-Cri

# Orden por año ascendente (verifica que NO empiece con 1982):
#   curl 'http://localhost:8000/api/search?order_by=year&order_dir=asc&limit=5' | jq

# API year filter (todos los buckets aplican):
#   curl 'http://localhost:8000/api/stats?year_from=1970&year_to=1972' | jq
#   curl 'http://localhost:8000/api/word-cloud?year_from=1970&year_to=1972' | jq
#   curl 'http://localhost:8000/api/timeline?year_from=1970&year_to=1972' | jq

# Verifier end-to-end (36 checks):
#   cd backend-fastapi && uv run python scripts/verify_api.py --base http://localhost:8000
```
