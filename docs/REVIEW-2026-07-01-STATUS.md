# Respuestas a los comentarios sobre cenidim.darylemb.dev

Este documento responde, una por una, a las 16 observaciones que se
hicieron sobre el tablero del archivo musical. Las respuestas están
escritas pensando en un equipo de trabajo artístico, así que evité
términos técnicos y expliqué cualquier palabra que pudiera sonar
ajena.

El documento describe cómo va a funcionar el sitio **después del
despliegue de la nueva versión** (la migración del backend a
Python/FastAPI, que está en proceso). En el día a día, el usuario
no nota ningún cambio: la URL sigue siendo la misma, los datos son
los mismos, los botones están en los mismos lugares. La diferencia
importante es que por dentro se hicieron arreglos a varios
problemas que se habían detectado.

---

## 1. "Canciones indexadas" en la esquina superior derecha — ¿es un número fijo o cambia?

Es un **número fijo** que se refiere al total del archivo, no a lo
que se ve filtrado. Siempre dice la cantidad total de canciones que
existen en la base de datos (actualmente 3 858).

Cuando se aplican filtros (por año, por tema, por clasificación
lingüística, etc.), el total del catálogo no cambia. Lo que sí
cambia es el otro número de al lado, el de "Álbumes", que se
recalcula para mostrar sólo los que entran dentro del filtro.

Por eso las dos cifras nunca se contradicen: una cuenta "todo el
catálogo" y la otra cuenta "lo que se ve después de filtrar".

## 2. El número de "Álbumes" cambia al filtrar pero "Canciones indexadas" no — ¿no confunde?

Sí, puede confundir si no se lee con cuidado. La nueva versión
agregó debajo de cada cifra una pequeña aclaración en letra más
clara:

- **Catálogo** · 3 858 · **canciones indexadas** (texto en gris)
- **Álbumes** · 280 · **colección única por disco** (texto en gris)

Así una se lee como "el total del catálogo" y la otra como "lo que
entra en tu filtro actual". El texto pequeño debajo de cada número
aclara cuál es cuál.

## 3. Al poner un rango de años, el campo "Hasta" se borra.

Esto ya está arreglado. Antes pasaba porque el campo estaba
configurado de una manera que, al perder el foco, se vaciaba. Ahora
el campo conserva el valor que escribiste mientras pasas al otro
campo o presionas Enter. El rango se aplica inmediatamente y se ve
reflejado en el banner "Filtros aplicados" debajo del tablero.

## 4. "Vida y muerte" aparece dos veces.

Esto pasa porque la base de datos tiene algunas canciones con
variantes del mismo tema: por ejemplo, una canción puede decir
`muerte` (minúscula) y otra `Muerte` (mayúscula), o `Vida/ muerte`
con espacio después de la barra.

**Estado actual (03/ago/2026):** el tablero ya no muestra las
variantes por separado. `canonical_tema` colapsa capitalización,
espacios y errores tipográficos conocidos en una forma canónica
(`Vida/ muerte` → `Vida/Muerte`), y el filtro de temas expande esas
variantes para que un chip canónico siga encontrando las filas
almacenadas con la grafía original. Lo que queda por normalizar son
duplicados que no son variantes de escritura sino **conceptos
distintos con nombres parecidos**; eso sigue siendo una decisión
editorial sobre el catálogo canónico de temas.

## 5. El promedio de caracteres por canción no es relevante.

Coincidimos. La cifra existe en los datos que manda el servidor
(como dato histórico) pero la nueva versión no la destaca en
ningún lado del tablero. Si en el futuro se quiere eliminar del
todo, se puede borrar esa línea sin afectar nada más.

## 6. "33 temas distintos" vs "24 temas" en otro lado del tablero.

Son **dos mediciones distintas**, no un error:

- El KPI "**Temas distintos**" en la parte de arriba cuenta los
  temas que aparecen **dentro del filtro que tengas activo**. Si
  filtras por año 1970-1980, te dice cuántos temas únicos hay en
  ese rango (puede ser 24).
- El subtítulo pequeño de los **botones de tema** dice
  "(24 temas en catálogo completo)" porque esos son los temas que
  existen en toda la base de datos, no los filtrados.

Las dos cifras son legítimas y aparecen con copy distinto para que
se entienda cuál es cuál.

## 7. ¿Una canción que aparece varias veces se cuenta una sola vez o por aparición?

La aplicación **cuenta filas, no canciones únicas**. Si una misma
canción tiene un valor de tema declarado dos veces (por ejemplo,
"Vida/ muerte" y otra variante), las dos filas aparecen por
separado.

**Estado actual (03/ago/2026):** las variantes triviales (mayúsculas,
espacios, typos como `Solidarida`/`Solidaridad`) ya se colapsan en
el conteo gracias a `canonical_tema` + `TEMA_TYPO_MAP`. La
deduplicación de canciones con valores **semánticamente distintos**
depende de la normalización de datos y del catálogo editorial.

## 8. La gráfica "TOP 10" de los discos más cantados.

**Resuelto (03/ago/2026):** la gráfica fue retirada del tablero en
la versión actual. El endpoint del API todavía calcula `top_albums`
(para compatibilidad), pero la interfaz ya no lo muestra.

## 9. ¿Qué quiere decir "Tipología lingüística" en la gráfica de Clasificación?

Es la **forma en que el sistema clasifica el lenguaje** de cada
canción usando un programa de análisis de texto. Se hace en tres
categorías:

- **Estándar** — vocabulario cotidiano, menos del 5% de palabras
  que el analizador no reconoce.
- **Regional** — incluye regionalismos (palabras propias de
  regiones de México), entre el 5% y el 18% de palabras no
  reconocidas.
- **Indígena** — incluye palabras de la lista de léxico indígena
  que mantiene el archivo, o más del 18% de palabras no
  reconocidas.

Cada categoría tiene un ícono (ⓘ) en la cabecera del tablero
que abre un popover con esta misma explicación. Así cualquiera
puede entender el significado sin tener que preguntar.

## 10. Caracterizar cada categoría y homogeneizar la terminología.

El tablero actual tiene un **ícono de información (ⓘ)** al lado
del título de cada gráfica. Al hacer click, abre un recuadro con
una descripción corta de qué muestra esa gráfica y cómo se
interpreta. Así cualquier persona puede entender "Léxico", "OOV",
"Tipología lingüística", etc. sin tener que adivinar.

Lo que falta es **acordar el vocabulario final con el equipo
editorial** para que el ensayo, los documentos de trabajo y el
tablero usen exactamente las mismas palabras. Ese es un trabajo de
redacción, no de programación.

## 11. Temas como `solidarida/individualismo` vs `solidaridad/individualismo`.

**Resuelto parcialmente (03/ago/2026).** El sistema sigue leyendo
la línea `Tema:` del archivo tal como fue transcrita, pero ahora
aplica un mapa de **errores tipográficos evidentes**
(`TEMA_TYPO_MAP`: `Solidarida` → `Solidaridad`) antes de agrupar.
Con los datos actuales, `Solidarida/Individualismo` y
`Solidaridad/Individualismo` se colapsan en un solo bucket
(`Solidaridad/Individualismo`), y el filtro por ese tema encuentra
ambas grafías.

Queda fuera del mapa todo lo que no sea un error tipográfico
obvio: la decisión de si dos temas son el mismo concepto (p. ej.
binomios vs palabras sueltas) le corresponde al catálogo editorial.

## 12. ¿Qué es la gráfica de Léxico (OOV)?

Mide **qué tan cotidiano o especializado es el lenguaje** de las
letras. "OOV" significa "**Out Of Vocabulary**" — cuántas palabras
de la canción el analizador de texto no conoce, comparadas con su
diccionario estándar.

- **OOV bajo** = la letra usa palabras muy comunes
- **OOV alto** = la letra tiene palabras raras, antiguas o
  regionales

Los rangos son:
- **Baja** (letra fácil): menos del 5% de palabras desconocidas
- **Media**: entre 5% y 18%
- **Alta** (letra difícil): más del 18% de palabras desconocidas,
  o contiene palabras del léxico indígena registrado

## 13. ¿Por qué unas palabras se ven más grandes que otras en la nube?

El **tamaño de cada palabra es proporcional a la frecuencia** con
que aparece en el conjunto de letras que estás viendo. Las
palabras que más se repiten se ven más grandes; las que aparecen
pocas veces, más pequeñas. La escala se ajusta automáticamente
para que la palabra más frecuente ocupe el tope y las demás se
distribuyan proporcionalmente.

## 14. Hay una zona donde se enciman muchas palabras.

**Mejorado (03/ago/2026).** La nube ahora pide por defecto las
**200 palabras** más frecuentes (antes 500) vía el parámetro
`?limit=` del endpoint `/api/word-cloud`, lo que reduce notablemente
el encimamiento en la vista de catálogo completo. Con filtros por
año o tema el número baja aún más. El endpoint admite pedir más
(`?limit=500`) si algún día se necesita la vista densa.

## 15. Palabras con mayúsculas y minúsculas.

**Resuelto (03/ago/2026).** El backend normaliza a minúsculas antes
de contar ("Mamá", "mamá" y "MAMÁ" cuentan como una sola) y
`_extract_words` ahora además:
- descarta tokens de 1 carácter (iniciales como "M.G.A." → m, g)
- descarta tokens puramente numéricos ("2", "33")
- descarta los **marcadores de metadatos por línea**
  (`Dura:`, `Tema:`, `Personajes:`, `Autor:`, …) que un ~8% de los
  registros aún arrastra en la columna `lyrics`, en lugar de
  intentar listar cada palabra suelta
- aplica una **lista de stop-words ampliada** (incluye "cuando",
  "donde", "qué", "todo", "tan", "va", etc. que antes se colaban)

Con esto la nube refleja léxico real de las letras y no cabeceras,
iniciales o conteos.

## 16. El título y autor de la canción se filtran en la nube de palabras.

**Resuelto (03/ago/2026).** Cuando el sistema analizaba cada
canción, tomaba todo el contenido del archivo `.txt`: la letra,
**pero también la cabecera con el título, autor, compositor**. Esas
palabras del título y autor aparecían en la nube de palabras junto
con las de la letra, y a veces dominaban.

Lo que se hizo, de raíz:
- Se agregó el paso **`scripts/normalize_db.py`** al pipeline de
  construcción (`build_db.sh`), que limpia el cuerpo de la letra:
  elimina la cabecera de la primera línea (título del `.txt`),
  la atribución `Autor:` que a veces va bajo el título, las líneas
  de metadatos (`Dura:`, `Tema:`, `Personajes:`, `Compositor:`)
  y las iniciales sueltas al pie (M.G.A.).
- La limpieza es **idempotente** y conservadora: solo quita líneas
  que son claramente cabecera o metadato, nunca contenido de la
  letra (verificada con tests unitarios).
- Con los datos actuales: de las canciones con letra, **366** se
  limpiaron y **0** conservan marcadores residuales (antes ~300).
- El título y el autor siguen intactos en sus columnas
  (`songs.title`, `songs.autor`); solo se quitaron del cuerpo de
  la letra que alimenta la nube.

Con esto la nube refleja solo el léxico real de la letra. El plan
original de columnas dedicadas `titulo_extraido`/`autor_extraido`
ya no es necesario: como el título/autor viven en sus propias
columnas, la limpieza del cuerpo es suficiente y no hay pérdida de
datos.

---

## Sobre el despliegue técnico

La nueva versión de la plataforma se desplegará usando el mismo
archivo `docker-compose-coolify.yaml` que ya está en el
repositorio. **No es necesario modificar** el archivo de compose
para hacer el cambio: el backend ya está configurado para usar la
imagen de Python (FastAPI) en lugar de la anterior imagen de Go.

El único cambio necesario es **configurar la rama de origen** en
Coolify para que tome el código de la rama con la nueva versión
del backend. El compose se construye a partir de la rama
seleccionada y los nombres de imagen (`cenidim-backend:latest`,
`cenidim-frontend:latest`) siguen siendo los mismos. Los
volúmenes, las redes internas, los healthchecks y el resto de la
configuración de Coolify permanecen intactos.

En resumen, el despliegue de la nueva versión es un cambio
**simple y seguro** desde el punto de vista operativo.
