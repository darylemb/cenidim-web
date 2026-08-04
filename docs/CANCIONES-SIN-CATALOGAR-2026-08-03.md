# Canciones del corpus sin catalogar en el catálogo (db_fonografia.csv)

Fecha: 3 de agosto de 2026

## Resumen

El corpus de letras `LetrasTXT/` tiene **175** archivos .txt. Al reconstruir la
base con el pipeline Python (build → clasificar → normalizar), el matcher por
**título interno** del archivo (la primera línea del .txt, la identidad real de
la canción) encontró correspondencia para **89** de ellos en el catálogo
(`db_fonografia.csv`, 3,858 canciones). Los otros **86** archivos corresponden
a canciones que **no están catalogadas** en el CSV (o están con un título que
no es la misma canción).

El número máximo de canciones con letra es ~89, no 175: el catálogo CSV no
incluye esas 86 canciones, aunque sus letras existen. Para llegar a 175 hace
falta agregar esas canciones al catálogo (o confirmar que no pertenecen).

## Listado por álbum

### A VIAJAR SE HA DICHO (12)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| Canción para arrullar a un grillito.txt | cancion para arreglar desorden | 0.62 |
| Capullito de algodón.txt | caballo de palo | 0.55 |
| Coco Rock.txt | disco rock | 0.70 |
| Dime, ranita.txt | dime nino | 0.64 |
| Gatoconcierto.txt | ratoncito | 0.61 |
| Lunes por la mañana.txt | linda manana | 0.56 |
| Mariana marinera.txt | maria maria | 0.69 |
| Morelia.txt | cortesia | 0.62 |
| Sara la tortuga.txt | susana oruga | 0.58 |
| Tango del perro y el tlacuache.txt | twist del perro | 0.41 |
| Una nueva escuela.txt | vamos a escuela | 0.60 |
| ¡A viajar se ha dicho!.txt | viaje de cricri | 0.45 |

### CANTACUENTOS (8)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| CHANEQUE DE PIEL MORENA.txt | canto a virgen morena | 0.52 |
| CUCARACHAS CALENTANAS.txt | cucaracha | 0.53 |
| EL MINUETO DE LAS TORTUGAS.txt | liebre y tortuga | 0.53 |
| EL POTRO Y EL ALACRÁN.txt | viboras y alacranes | 0.58 |
| IHUATSÏ.txt | aguas | 0.43 |
| JANIKUA.txt | ranitas | 0.43 |
| LAGARTIJA BESUCONA.txt | lagartija | 0.60 |
| MISITU SAPICHU TURHÍPITI.txt | indito y su burrito | 0.38 |

### CORRE TRENECITO (11)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| CLAUDIA LA LUCIÉRNAGA.txt | luciernaga | 0.66 |
| CORRE TRENECITO, CORRE.txt | trenecito correlon | 0.57 |
| CUMBIA DEL CANGREJO.txt | cumbia del perico | 0.68 |
| El sapo panzón.txt | tadeo pulgon | 0.50 |
| GATO CONCIERTO.txt | gato carpintero | 0.60 |
| HISTORIAS DEL ABUELO.txt | historia del astrodito | 0.64 |
| LUNA CARACOLITO.txt | caracolito | 0.77 |
| Lluviecita.txt | florecita | 0.60 |
| Los cien pies del ciempiés.txt | ven nino del cielo | 0.55 |
| SOL CHARALITO SAL.txt | soldaditos | 0.47 |
| Vuela papalote, vuela.txt | vuelta al mundo | 0.45 |

### EL DUENDE DE LOS CAMINOS (9)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| CANCIÓN PARA ARRULLAR A UN GRILLO.txt | cancion para arreglar desorden | 0.67 |
| DON GALLO.txt | don diablo | 0.70 |
| DOÑA LAGARTIJA.txt | lagartija | 0.74 |
| EL DUENDE DE LOS CAMINOS.txt | rueda de chicos | 0.65 |
| EL GRILLO MÚSICO.txt | grupo musical | 0.61 |
| MORELIA.txt | cortesia | 0.62 |
| PERICO MARCEÑO.txt | perrito maltes | 0.57 |
| PROTESTA DE LOS VILLANOS.txt | orquesta de payasos | 0.60 |
| TZINTZUN.txt | tin din | 0.50 |

### EL RINCÓN DE LOS NIÑOS VOL. 3 (1)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| RE-LA-MI-DO.txt | relojito | 0.62 |

### EL RINCÓN DE LOS NIÑOS VOL. 6 (13)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| AVESTRUZ.txt | travesuras | 0.50 |
| CANCIÓN DEL RELOJITO.txt | cancion del genio | 0.75 |
| CANCIÓN PARA DORMIR A UNA GARZA.txt | cancion para dormir al sapo | 0.81 |
| MARCHA DE LOS LAPICES.txt | marcha de canicas | 0.82 |
| MIRA QUE PRECIOSA ESTRELLA.txt | mi pequeno estrella | 0.58 |
| MUÑECA DE VERDAD.txt | muneca enferma | 0.69 |
| OSO PELUDO.txt | yo pecador | 0.50 |
| PAYASO DE CIRCO.txt | vamos al circo | 0.60 |
| PÁJARO CARPINTERO.txt | gato carpintero | 0.77 |
| TERRÓN DE AZÚCAR.txt | tema de abaco | 0.50 |
| TORTOLAS EN LA CONCHITA.txt | tortillerita | 0.45 |
| YO QUIERO SER MILLONARIO.txt | yo quiero ser mago | 0.71 |
| YO TE QUIERO, TU ME QUIERES.txt | yo no quiero hermanito | 0.50 |

### HUACHITO (9)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| EL CORRIDO DEL MURCIÉLAGO.txt | ven nino del cielo | 0.50 |
| EL GALLO MADRUGADOR.txt | gallito cantador | 0.56 |
| EL PERICO MARCEÑO.txt | perrito maltes | 0.57 |
| EL TORO Y EL BURRO.txt | zorra y cuervo | 0.57 |
| El kuinique y la lagartija.txt | lagartija | 0.55 |
| GATO LADINO.txt | gato feliciano | 0.64 |
| La iguana feliz.txt | tilin feliz | 0.58 |
| Pobres perros gatos.txt | tres reyes magos | 0.53 |
| SON DEL POLLITO.txt | rock del angelito | 0.59 |

### LOS RINCÓN Y DON PULPO (1)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| RE-LA-MI-DO.txt | relojito | 0.62 |

### SON DE LA CIUDAD (6)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| BLANCA FLOR.txt | blanca paloma | 0.69 |
| EL BAILE DE LAS BRUJAS.txt | cancion de brujas | 0.71 |
| EL ENGAÑO ¡AH ESPANTAPÁJAROS!.txt | cazadores antipaticos | 0.46 |
| EL GALLITO.txt | pollito | 0.71 |
| LA BOLA DE NIÑOS.txt | mundo de ninos | 0.64 |
| LAS DANZAS Y EL SOL.txt | plantas y arboles | 0.53 |

### UATSI SAPICHU (10)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| AUANI SAPICHU BLANCO.txt | juan pirulero | 0.45 |
| AXUNI Y AKUITSE.txt | quien dijo aburrirse | 0.40 |
| DUERME MI UÁTSÏ SAPICHU.txt | duermete mi nino | 0.43 |
| EL KOKI Y LA KUANASI.txt | ronda de gimnasia | 0.41 |
| KUARAKI.txt | karate | 0.57 |
| LA TSÍKATA Y EL KÚKUNO.txt | silvana y silvino | 0.47 |
| MI UARECITA.txt | mi vaquita | 0.64 |
| SOL CHARALITO, SOL.txt | ha salido sol | 0.53 |
| TSINTSUNI.txt | asi te senti | 0.50 |
| UN OLOROSO AMIGO.txt | somos amigos | 0.61 |

### UN MAULLIDO EN LA AZOTEA (6)

| Archivo | Mejor título en catálogo | Similitud |
|---|---|---|
| CHACARERA DE LOS GATOS.txt | chacarera de m | 0.72 |
| DRÁCULA.txt | caracola | 0.62 |
| LA BRUJA CIZAÑA.txt | bruja a | 0.58 |
| LOS GATOS BANDA.txt | banda | 0.56 |
| LOS GATOS LOCOS.txt | gato loco | 0.82 |
| ¿DÓNDE ESTÁ MI GATO?.txt | donde estan ninos | 0.61 |

## Nota sobre los casos "casi" (0.70-0.85)

Algunos archivos se parecen a un título del catálogo pero NO son la misma
canción (p. ej. "Pájaro Carpintero" vs "gato carpintero", "Don Gallo" vs "don
diablo"). Otros podrían ser variantes que el equipo debe revisar:
- **LOS GATOS LOCOS** vs "El gato loco" (0.82): posible plural/singular.
- **EL BAILE DE LAS BRUJAS** vs "La canción de las brujas" (0.71): posible variante.
- **MARCHA DE LOS LÁPICES** vs "marcha de canicas" (0.82): NO son la misma.

## Lenguas indígenas

Un grupo importante son canciones en lenguas indígenas (purépecha, etc.) que el
catálogo no incluye: AUANI SAPICHU BLANCO, AXUNI Y AKUITSE, IHUATSÍ, JANIKUA,
KUARAKI, MISITU SAPICHU TURHÍPITI, TSINTSUNI, TZINTZUN, DUERME MI UÁTSÍ SAPICHU,
EL KOKI Y LA KUANASI, LA TSÍKATA Y EL KÚKUNO, MI UARECITA, SOL CHARALITO.

