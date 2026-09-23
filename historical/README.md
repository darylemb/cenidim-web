# historical/

Material de trabajo previo a la automatización del pipeline. Se conserva
como referencia editorial e histórica; **no es entrada del pipeline actual**.

- `Clasificacion.csv` / `clasification.csv` — hoja de clasificación manual
  del cancionero (álbum, canción, autor, letra cruda y una columna
  `Clasifiacion` escrita a mano, con valores `ESPAÑOL_ESTANDAR` /
  `ESPAÑOL_REGIONAL`). Son dos versiones casi idénticas del mismo
  worksheet. La clasificación vigente vive en la base de datos y la
  calcula `scripts/classify_songs.py` (spaCy, umbrales OOV); el tema de
  cada canción proviene del campo literal `Tema:` de `LetrasTXT/*.txt`.

La base de datos se construye con `db_fonografia.csv` + `LetrasTXT/`
(véase `scripts/build_db.sh`). Nada en `historical/` participa en ese
proceso.
