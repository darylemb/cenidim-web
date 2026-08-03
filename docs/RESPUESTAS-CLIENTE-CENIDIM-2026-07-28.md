# Respuestas a preguntas del CENIDIM referente a la página del Archivo Musical

Fecha: 28 de julio de 2026

## Preguntas y respuestas

### 1) Canciones indexadas - dato fijo o variable

**Pregunta textual:**
"¿Las canciones indexadas en el catalogo (arriba a la derecha) es un dato fijo que se refiere a todo el conjunto de canciones?"

**Respuesta:**
Es un numero fijo del total del archivo (actualmente 3,858). No cambia con filtros. Al filtrar, cambia el conteo de albumes visibles, no el total del catalogo.

**Estatus:** Resuelto

### 2) Posible confusion entre "Albumes" y "Canciones indexadas"

**Pregunta textual:**
"El numero de albumes cambia al filtrar y canciones indexadas no; puede confundir."

**Respuesta:**
Se agregaron aclaraciones de contexto bajo cada cifra para distinguir "total del catalogo" vs "resultado filtrado".

**Estatus:** Resuelto

### 3) Campo "Hasta" se borra al definir rango de anos

**Pregunta textual:**
"Al definir un rango de anos el input Hasta se borra."

**Respuesta:**
Ya esta corregido. El valor del campo se conserva y el rango aplicado aparece en "Filtros aplicados".

**Estatus:** Resuelto

### 4) "Vida y muerte" aparece dos veces

**Pregunta textual:**
"Vida y muerte aparece dos veces (muerte y Muerte)."

**Respuesta:**
La causa es variacion de escritura en origen (mayusculas, espacios, variantes). Para resolverlo totalmente se requiere normalizacion de temas en base de datos con forma canonica unica.

**Estatus:** Pendiente (normalizacion de datos)

### 5) Promedio de caracteres no relevante

**Pregunta textual:**
"El promedio de caracteres, en principio, para nuestro analisis no es relevante."

**Respuesta:**
Se mantiene como dato historico en backend, pero no se destaca en el tablero. Puede retirarse por completo sin impacto funcional si se decide editorialmente.

**Estatus:** Resuelto funcionalmente

### 6) 33 temas distintos vs 24 temas

**Pregunta textual:**
"Aparecen 33 temas distintos, pero en otro grafico dice 24 temas."

**Respuesta:**
Son metricas distintas: una refleja temas del filtro activo y la otra temas del catalogo completo. No es inconsistencia de calculo.

**Estatus:** Resuelto

### 7) Conteo de canciones repetidas

**Pregunta textual:**
"¿La cancion que aparece varias veces se cuenta una sola vez o por aparicion?"

**Respuesta:**
Actualmente el conteo es por filas/apariciones. La deduplicacion semantica depende de la normalizacion de temas y valores fuente.

**Estatus:** Pendiente (normalizacion de datos)

### 8) Grafica TOP 10 de discos

**Pregunta textual:**
"La grafica TOP 10, en principio no es relevante para nuestro analisis."

**Respuesta:**
Se retira en nueva versión.

**Estatus:** Resuelto

### 9) Que significa "Tipologia linguistica"

**Pregunta textual:**
"¿Podria caracterizarse brevemente la grafica de TIPOLOGIA LINGUISTICA?"

**Respuesta:**
Clasifica el lenguaje en tres categorias: Estandar, Regional e Indigena, con umbrales de palabras no reconocidas y deteccion de lexico indigena. El tablero incluye icono de informacion con esta explicacion.

**Estatus:** Resuelto

### 10) Homogeneizar terminologia en graficas y documentos

**Pregunta textual:**
"Deberia caracterizarse cada categoria y homogeneizar terminologia en documentos y productos."

**Respuesta:**
El tablero ya incluye ayuda contextual por grafica. Falta acuerdo editorial para vocabulario final unificado entre tablero, ensayo y documentos.

**Estatus:** Pendiente

### 11) Temas con errores menores de escritura

**Pregunta textual:**
"Hay temas repetidos por diferencia de una letra (solidarida/individualismo vs solidaridad/individualismo)."

**Respuesta:**
La app respeta texto fuente tal como fue transcrito. La unificacion requiere catalogo canonico de temas y reproceso de la base.

**Estatus:** Pendiente (normalizacion de datos)

### 12) Que muestra la grafica de Lexico (OOV)

**Pregunta textual:**
"¿A que se refiere la grafica LEXICO?"

**Respuesta:**
Mide proporcion de palabras fuera del vocabulario del analizador (OOV, Out of vocabulary). Se interpreta como nivel de cotidianidad/especializacion del lenguaje (baja, media, alta).

**Estatus:** Resuelto

### 13) Criterios de tamano en nube de palabras

**Pregunta textual:**
"¿Que criterios aplican para tamano, ubicacion y tipografia de palabras?"

**Respuesta:**
El tamano se asigna por frecuencia relativa de uso. Las mas frecuentes se muestran mas grandes. La distribucion visual se ajusta automaticamente.

**Estatus:** Resuelto (se puede modificar a petición)

### 14) Palabras encimadas en una zona de la nube

**Pregunta textual:**
"Hay una zona en donde aparecen muchas palabras encimadas."

**Respuesta:**
Es una limitacion comun del algoritmo de acomodo cuando hay muchas palabras. Mejora recomendada: limitar la nube a 100-200 terminos para mejor legibilidad.

**Estatus:** Pendiente mejora de visualizacion

### 15) Repeticiones por mayusculas/minusculas

**Pregunta textual:**
"Hay palabras repetidas con mayusculas y minusculas. ¿Como normalizar?"

**Respuesta:**
Ya se normaliza a minusculas antes del conteo y se excluyen stop-words, palabras de un caracter y metadatos comunes.

**Estatus:** Resuelto (puede modificarse)

### 16) Titulo/autor se mezclan en la nube de palabras

**Pregunta textual:**
"El titulo, autor y compositor se reflejan en la nube de palabras. ¿Opinion?"

**Respuesta:**
La recomendacion es separar metadatos en columnas dedicadas (titulo_extraido, autor_extraido), reprocesar canciones y excluir esos campos del analisis de nube para considerar solo letra.

**Estatus:** Pendiente

## Resumen de avance

- Resueltos: 10
- Pendientes tecnicos: 5
- Pendientes editoriales/decision: 3

---

## Actualizacion (03/ago/2026)

Cambios aplicados despues de la fecha original, que actualizan los
estatus de las preguntas 4, 7, 11, 14 y 15.

### Actualizacion a la pregunta 4 ("Vida y muerte" aparece dos veces)

Se aplico normalizacion por **forma canonica** en el tablero:
`canonical_tema` colapsa variantes de mayusculas, espacios y typos
obvios al agrupar ("Vida/ muerte" y "Vida/ Muerte" → "Vida/Muerte").
El filtro de temas busca ambas grafias. **Resuelto en la
visualizacion**; sigue pendiente solo la normalizacion de datos para
duplicados que no sean variantes de escritura.

### Actualizacion a la pregunta 7 (conteo de canciones repetidas)

Se mantiene el conteo por filas/apariciones, pero las variantes
triviales (mayusculas, espacios, typos) ya se colapsan en el
conteo. **Mejorado.**

### Actualizacion a la pregunta 11 (solidarida vs solidaridad)

Se agrego un mapa de **errores tipograficos evidentes**
(`TEMA_TYPO_MAP`): "Solidarida/Individualismo" y
"Solidaridad/Individualismo" ahora se agrupan bajo
"Solidaridad/Individualismo", y filtrar por el tema encuentra ambas
grafias. **Resuelto** para errores de escritura; las decisiones sobre
binomios vs palabras sueltas siguen siendo editoriales.

### Actualizacion a la pregunta 14 (palabras encimadas en la nube)

La nube ahora muestra por defecto las **200 palabras mas frecuentes**
(antes 500), lo que reduce el encimamiento. El endpoint admite pedir
mas si se requiere. **Mejorado.**

### Actualizacion a la pregunta 15 (mayusculas/minusculas)

Se refuerzo la limpieza en el backend:
- normalizacion a minusculas antes del conteo (ya existia)
- se descartan tokens de 1 caracter, numeros, y los marcadores de
  metadatos por linea (`Dura:`, `Tema:`, `Personajes:`, `Autor:`)
- lista de stop-words ampliada (cuando, donde, que, todo, tan, va...)

La nube refleja ahora lexico real de las letras. **Resuelto.**

### Actualizacion a la pregunta 16 (titulo/autor en la nube)

Se agrego un paso de **normalizacion de datos** al pipeline de
construccion (`scripts/normalize_db.py`) que limpia el cuerpo de
cada letra: elimina la cabecera de la primera linea (titulo del
.txt), la atribucion "Autor:" bajo el titulo, los marcadores de
metadatos (Dura:, Tema:, Personajes:, Compositor:) y las iniciales
al pie (M.G.A.). El titulo y el autor siguen en sus propias
columnas (`songs.title`, `songs.autor`); solo se quitaron del texto
que alimenta la nube. Con los datos actuales, 0 de 3858 canciones
conservan marcadores residuales en la letra. **Resuelto.**

### Deteccion de letras mal asignadas

Se detecto que el antiguo constructor de la base asignaba letras con
un umbral de similitud demasiado laxo: por similitud de nombre, "Los
perritos" recibia la letra de "LOS PUERQUITOS.txt" (por eso al buscar
"oinc" aparecian los perritos). Correccion:

- el builder Go ahora exige un match con score >= 0.85 (antes 0.6),
- `scripts/normalize_db.py --fix-lyrics-match` re-valida cada letra
  contra los archivos `LetrasTXT/`: las que no tienen match fiable
  quedan **sin letra** (mejor que con la letra equivocada) y las
  correctas se releen del archivo fuente.

Con los datos actuales, 367 letras fueron re-validadas; quedan 126
con match fiable. Las canciones sin archivo de letra correspondiente
ya no muestran una letra ajena.

### Filtro "Sin tema" corregido

El filtro "Sin tema" del tablero no devolvia resultados (la busqueda
usaba el valor especial `__none__` que el backend no interpretaba).
Ahora devuelve las 3 534 canciones sin tema declarado, y se puede
combinar con otros filtros.

### Tablas normalizadas y ordenamiento por columna

- Todas las tablas (catalogo y panel admin) usan ahora `table-layout:
  fixed` con anchos de columna fijos via `<colgroup>`: no cambian de
  tamano al actualizar, paginar, ordenar o cambiar filtros.
- El catalogo permite ordenar haciendo click en cualquier cabecera de
  columna (antes solo desde el selector), y el backend acepta ordenar
  por todas las columnas (titulo, album, interprete, editora, pais,
  etc.), no solo por las 7 originales.
- El filtro de temas muestra ahora los 27 temas del catalogo (antes
  solo 24); la lista de filtros coincide con la grafica "Por tema".
