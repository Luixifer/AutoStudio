# AutoStudio Director LAB 0.1

Ampliación de AutoStudio, no sustitución de la APK estable. Revisión completa: [auditoría](AUDIT.md), [guía Samsung](PHONE_GUIDE.md), [infraestructura y límites](INFRASTRUCTURE.md).

## Ejecutar el motor existente y la ampliación

```sh
python -m pip install -r requirements-director.txt
python scripts/fetch_voice.py
python -m scripts.director.engine /ruta/proyecto/project.json --out /ruta/render
# Seleccionar una parte sin modificar las demás:
python -m scripts.director.engine /ruta/proyecto/project.json --chapter c1 --out /ruta/render-capitulo
# Ensayo explícito, sin material de Hessdalen:
python -m scripts.director.fixture --out /tmp/ensayo
python -m scripts.director.engine /tmp/ensayo/project.json --out /tmp/resultado
```

El JSON versionado agrupa `chapters[].scenes[]`: `id`, `narration`, `media` con `kind=image|video`, `path`, `rights`, `fit`, `trim_start` y `loop`; `voice` por proyecto/escena con Kokoro o WAV/MP3; `camera.keyframes` normalizados 0–1 y zoom 1–1,25; `transition`; efectos por tiempo. Música global con ganancia acotada y atenuación por voz. El generador de ensayo proporciona un ejemplo **realmente ejecutable**; la plantilla Hessdalen necesita tus archivos y no se presenta como validada.

## Compilar la APK separada

```sh
# JDK completo y Android SDK oficial: platform 35 + build-tools 35.0.0.
AUTOSTUDIO_DIRECTOR_BUILD=1 python android/build.py
```

Salida `build/android/AutoStudio-Director-0.1.0-lab.apk`; firma de depuración comprobada por apksigner. El build predeterminado anterior sigue disponible sin esa variable. No se incluyen credenciales ni claves de publicación.

El workflow `personal-custom.yml` conserva el editor personal original fuera de la rama Director. En `codex/autostudio-director`, recibe el mismo UUID ya soportado por GitHub y procesa el ZIP desde su borrador de Release. No hace falta sustituir ni fusionar main para probarlo.

## Evidencia y aceptación

- Pruebas heredadas y del editor recuperado; pruebas nuevas de contrato, rutas, ZIP, duraciones, caché, clips cortos, parallax, montaje real por capítulos, transiciones y audio.
- Prueba local 1080p con Álex: `smoke-local.json`. Es un ensayo corto; no el documental de cinco minutos.
- El workflow Director ejecuta una APK real en un emulador Android 15, inicia Actions con credencial temporal en memoria del test, recupera el MP4, comprueba SHA y decodifica con el reproductor nativo. Sus informes se entregan aunque la prueba falle. El resultado solo se marca aprobado cuando existe evidencia de esa ejecución.
- Ninguna prueba emulada demuestra funcionamiento físico en Samsung, naturalidad de la voz ni calidad cinematográfica. La importación mediante el selector de documentos del sistema requiere revisión física; la prueba automatizada importa archivos reales mediante ContentResolver.
- No se ha producido Hessdalen: el usuario entregará sus recursos desde la APK. Tampoco se certifica aquí un documental de una hora.

## Capítulos portátiles (motor probado; automatización Android pendiente)

```sh
python -m scripts.director.chapters split proyecto/project.json --out partes
# Extrae cada input-ID.zip y renderízalo con el mismo motor en un runner independiente.
python -m scripts.director.engine entrada/project.json --out render-ID
python -m scripts.director.chapters package entrada/project.json --render render-ID --chapter ID --out partes/rendered-ID.zip
python -m scripts.director.chapters assemble partes/assembly.json --bundles partes --out completo
```

El ensamblaje valida proyecto, orden, hashes, formato, duración PCM, vídeo y subtítulos de cada parte. No requiere volver a sintetizar voz ni disponer de todas las imágenes durante el ensamblaje. Se ha probado un recorrido real de dos capítulos con FFmpeg. El reparto automático de ZIPs desde la APK y entre jobs todavía falta; los efectos puntuales por escena se admiten en el montaje completo, pero se rechazan expresamente en este primer formato portátil.

La APK permite exportar una copia ZIP e importarla como otro proyecto, sin tocar el original. Estas copias evitan depender de una firma de laboratorio entre revisiones: **no desinstales una revisión con proyectos sin exportarlos primero**. Todavía no hay un almacén de firma de publicación ni se ha activado uno.
