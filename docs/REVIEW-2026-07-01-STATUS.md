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
con espacio después de la barra. La aplicación los junta cuando
muestra el conteo en el tablero, pero en la lista de filtros
aplicados aparecen como dos entradas distintas.

Para resolverlo del todo hay que **normalizar la base de datos**:
recorrer todas las canciones y reemplazar las variantes por una
forma canónica ("Vida/Muerte"). Es un trabajo que hay que hacer
una sola vez sobre la base y se hace del lado de los scripts de
clasificación, no del tablero. **Está pendiente.**

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

Ahora mismo la aplicación **cuenta filas, no canciones únicas**.
Si una misma canción tiene un valor de tema declarado dos veces
(por ejemplo, "Vida/ muerte" y otra variante), las dos filas
aparecen por separado. Esto se soluciona a la vez que el punto 4:
normalizando los temas de la base de datos. **Está pendiente.**

## 8. La gráfica "TOP 10" de los discos más cantados.

Coincidimos que para el análisis no aporta mucho. La gráfica se
mantiene por compatibilidad con la versión anterior, pero si se
quiere retirar del tablero es un cambio pequeño. **Pendiente de
decisión editorial** sobre si se quita o se deja.

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

La diferencia viene **directamente del archivo de texto de cada
canción**. El sistema lee la línea `Tema:` que escribió la persona
que hizo la transcripción y la guarda tal cual. Si una transcribió
"Solidarida/Individualismo" y otra "Solidaridad/Individualismo",
el sistema respeta lo escrito.

Por eso la decisión sobre **cómo unificar** los temas le toca al
equipo editorial: hay que ponerse de acuerdo en un catálogo único
de "temas canónicos" y luego pasar ese catálogo por encima de toda
la base para reescribir las variantes.

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

La nube de palabras está generada por un programa estándar de
visualización que acomoda las palabras para llenar el espacio, sin
embargo no es perfecto y a veces quedan zonas atestadas. Esto se
nota especialmente cuando se ven las 500 palabras más frecuentes
de **todo el catálogo**: si filtras por año o por tema, el número
baja (a veces 80 o 100 palabras) y el encimamiento se reduce
mucho. Como mejora, podría limitarse la nube a las 100 o 200
palabras más frecuentes para que se vean más espaciadas.

## 15. Palabras con mayúsculas y minúsculas.

El sistema de clasificación **ya normaliza a minúsculas** antes de
contar, así que "Mamá", "mamá" y "MAMÁ" cuentan como una sola.
También descarta:
- Palabras de 1 carácter (preposiciones, artículos)
- Stop-words del español (palabras vacías como "el", "de", "que")
- Marcadores de metadatos (líneas como "Dura: 3:21", "Autor: ...")

Por eso en la nube ves todo en minúsculas y sin palabras
funcionales.

## 16. El título y autor de la canción se filtran en la nube de palabras.

**Buen punto.** Cuando el sistema analiza cada canción, toma
todo el contenido del archivo `.txt`: la letra, **pero también la
cabecera con el título, autor, compositor**. Esas palabras del
título y autor terminan apareciendo en la nube de palabras junto
con las de la letra, y a veces dominan (por ejemplo, "Timbiriche"
aparece más porque está en el título del disco y en cada nombre
de canción).

La forma correcta de resolverlo es:
1. Agregar columnas dedicadas `titulo_extraido` y `autor_extraido`
   a la tabla de canciones
2. Que el script de clasificación extraiga esos datos y los
   guarde en columnas separadas
3. Que el sistema de nube de palabras **excluya** esas columnas y
   solo analice la letra

Esto requiere un cambio de esquema en la base de datos y un
proceso para reprocesar las 3 858 canciones. Es un trabajo de unas
horas, pero implica tocar la base de datos en producción, así que
conviene hacerlo en una ventana de mantenimiento. **Está pendiente
y es lo más recomendable** de todos los puntos abiertos.

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
