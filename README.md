# AutoStudio 0.2 — escenas y voz neuronal

Fábrica experimental de vídeos científicos con programas libres y **sin APIs de pago ni publicación en YouTube**. Montaje reproducible en GitHub Actions, administrable desde el móvil. No es un generador cinematográfico autónomo terminado.

## Aplicación Android de control — incremento 0.3

[Guía de instalación, conexión y prueba desde Samsung](android/README.md) · [Arquitectura y límites](docs/ANDROID_ARCHITECTURE.md)

Este incremento prioriza tema → solicitud a Actions → MP4 correlacionado → reproducción nativa. Conserva el renderizador 0.2 y solo utiliza el contenido gratuito realmente disponible. No promete todavía edición, lotes, documentales o temas científicos ilimitados. El estado de la compilación y las pruebas se registra en `android-preview/attempt.json`.

**Recorrido Android verificado:** [Descargar APK de LAB 0.3](https://github.com/Luixifer/AutoStudio/raw/d0e5bfbede04afecc9abd561137bbe0d1d547087/AutoStudio-Control-0.3.0-lab.apk) · [Ejecución integral correcta](https://github.com/Luixifer/AutoStudio/actions/runs/44090864966) · [Informe de correcciones y pruebas](android/VALIDATION.md). Se verificó en emulador Android 15 con credencial temporal, no en un Samsung físico. Tu conexión personal se configura una vez en el móvil.

## Prueba 0.2 ya ejecutada

[**Descargar el nuevo MP4 de 34,44 segundos**](https://github.com/Luixifer/AutoStudio/raw/efed2972fdad05c364512744fdf45ef1e1776ec3/short_ciencia_demo.mp4) · [Actions: SUCCESS, 34 pruebas](https://github.com/Luixifer/AutoStudio/actions/runs/44074329488) · [Comparativa real](docs/images/02-before-after.jpg)

Se descargó el resultado de Actions y se volvió a verificar. La nueva base mejora montaje y subtítulos; las ilustraciones siguen siendo estilizadas y la voz necesita tu evaluación. No se declara calidad cinematográfica final.

## Generar y descargar desde tu Samsung

1. Abre [Actions](https://github.com/Luixifer/AutoStudio/actions/workflows/create-short.yml) → **Run workflow**.
2. Selecciona **cinematic** para la nueva revisión; **classic** conserva el render anterior de tres diagramas y voz eSpeak.
3. Espera al resultado. La [rama de resultados](https://github.com/Luixifer/AutoStudio/tree/video-preview) contiene `attempt.json`, vídeo, subtítulos, tiempos y pruebas.
4. **[Descargar el último MP4](https://github.com/Luixifer/AutoStudio/raw/refs/heads/video-preview/short_ciencia_demo.mp4)**.

Si no ves Run workflow, activa «Sitio de escritorio» en tu navegador móvil. No requiere un ordenador. Si el intento falla, se registra; un MP4 anterior no se presenta como una salida nueva. El enlace estable contiene el último vídeo; el historial Git conserva los resultados anteriores.

## Qué cambia

- Ocho planos montados a partir de cinco ilustraciones 3D originales, con cámara animada, partículas sutiles y transiciones. Se retira la caja de párrafos. Los renders se producen en Blender; el montaje de cada vídeo reutiliza esas imágenes.
- Voz neuronal **Kokoro ONNX**, ejecutada localmente en CPU; voz española `ef_dora`, fonemizador castellano `es`. No se utiliza una API de voz. La naturalidad y el acento necesitan evaluación humana: seleccionar español no garantiza una locución profesional de España.
- Subtítulos de **hasta tres palabras**, con palabra activa resaltada. Los tiempos proceden de las duraciones de fonemas de la misma inferencia que genera el audio. Se rechazan desajustes de palabras; no se inventan tiempos por longitud. No es una alineación independiente con reconocimiento de voz ni una aprobación humana.
- Apertura directa «Aquí no llega el Sol»; conclusión sobre otra manera de obtener energía. Se conserva el matiz del oxígeno de superficie para evitar sugerir independencia absoluta de la fotosíntesis.
- Ambiente sonoro sintético original y discreto, normalización de voz y limitador; sin música descargada ni grabaciones ajenas.

**Las imágenes se identifican como ILUSTRACIÓN 3D**: no son filmaciones submarinas, imágenes fotográficas ni simulación completa de fluidos. Cámara y partículas se animan sobre renders fijos. El guion sigue necesitando revisión científica humana.

## Conservar la versión funcional

- Etiqueta [`baseline-mvp-41s`](https://github.com/Luixifer/AutoStudio/tree/baseline-mvp-41s): código anterior.
- [MP4 anterior de 41,08 s, enlace fijo](https://raw.githubusercontent.com/Luixifer/AutoStudio/81eb7dfb0874b4483c86b45b1894f1a7bf1ff95b/short_ciencia_demo.mp4).
- [Primera ejecución real](https://github.com/Luixifer/AutoStudio/actions/runs/44068185619).
- Los módulos `artwork.py`, `narration.py` y `ocean.json` conservan el modo clásico; no se han sustituido por el nuevo diseño.

## Coste y límites

- Python, Pillow, FFmpeg, Blender, eSpeak NG y Kokoro/ONNX locales; consulta [procedencia y licencias](THIRD_PARTY.md).
- Modelos gratuitos descargados de una publicación oficial de GitHub, con SHA-256 fijados. No se incluyen sus 354 MB en Git ni se consulta un servicio de inferencia.
- Solo **repositorio público y runner estándar `ubuntu-24.04`**, sin GPU, cron, Artifacts, cache de pago, runners grandes ni claves de servicios externos.
- Una ejecución concurrente, timeout de 15 minutos, MP4 máximo 20 MiB y 150 segundos. No hay render automático por cada cambio: manual o etiqueta `render-*`.
- El token automático de GitHub solo escribe resultados en `video-preview`; no es un token de IA facturado. La disponibilidad y políticas del servicio gratuito las determina GitHub; no se promete capacidad gratuita ilimitada ni se cambia la facturación.
- YouTube está desactivado: no hay integración de publicación.

## Reproducción en infraestructura cloud

El workflow instala `ffmpeg`, `espeak-ng`, fuentes DejaVu y Python 3.12, y ejecuta:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-neural.txt
.venv/bin/python scripts/fetch_voice.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/render.py --profile cinematic --out output
```

El perfil clásico también funciona con `requirements.txt` y `espeak-ng`, sin descargar modelos:

```sh
.venv/bin/python scripts/render.py --profile classic --out output
```

Para regenerar el arte en una máquina cloud con Blender 4.3.2, Python y FFmpeg gratuitos:

```sh
blender -b -t 4 --python scripts/create_cinematic_assets.py -- "$PWD"
```

El generador conserva renders sin filtro en `output/original-blender-stills/`, filtra ruido espacial y actualiza el manifiesto; no amplía imágenes para inventar detalle. El archivo editable está en `sources/ocean_environment_v02.blend`. El workflow de montaje habitual **no ejecuta Blender**, usa las ilustraciones versionadas. No se necesita un ordenador personal para usarlo; futuras revisiones de arte requieren un entorno cloud con Blender, no una API facturada.

## Controles verificables

Las 16 pruebas anteriores se conservan, con pruebas adicionales de subtítulos, límites, movimiento, integridad de recursos, voz ausente o alterada y ambiente reproducible. El render real añade `quality.json`: cobertura completa de palabras, tiempos dentro del audio, subtítulos de dos líneas como máximo y cambios medidos entre encuadres.

`validation.json` comprueba decodificación completa, H.264 720×1280/25 fps, AAC estéreo, duración, señal de audio, clipping, fast-start y SHA-256. Esto **no mide belleza, comprensión, pronunciación o rigor científico**. Consulta [la revisión](docs/REVIEW_02.md) para resultados y limitaciones.

El publicador solo acepta una salida de esa ejecución de GitHub Actions, verificando commit, run ID y hash. No puede etiquetar un render de desarrollo como una prueba de Actions.
