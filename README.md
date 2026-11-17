# AutoStudio — MVP 0.2

Fábrica experimental de vídeos científicos **sin APIs de pago ni publicación en YouTube**. Es una prueba real de montaje, no una IA autónoma de investigación ni un generador cinematográfico terminado.

## Usarlo desde tu Samsung, sin ordenador

El código ya está subido y la primera ejecución real de GitHub Actions ha terminado correctamente.

[Descargar el MP4 verificado de 41,08 segundos](https://github.com/Luixifer/AutoStudio/raw/refs/heads/video-preview/short_ciencia_demo.mp4) · [Ver ejecución real y sus pruebas](https://github.com/Luixifer/AutoStudio/actions/runs/44068185619)

Para generar otro vídeo desde el móvil:

1. Abre [Luixifer/AutoStudio](https://github.com/Luixifer/AutoStudio) en el navegador del móvil.
2. En **Actions**, selecciona **Crear vídeo científico de prueba (sin YouTube)** → **Run workflow**.
3. Espera a que termine. En la rama [`video-preview`](https://github.com/Luixifer/AutoStudio/tree/video-preview) aparecerá el resultado y su enlace de descarga.
4. [Descargar el último MP4](https://github.com/Luixifer/AutoStudio/raw/refs/heads/video-preview/short_ciencia_demo.mp4). Este enlace solo funciona tras una ejecución que haya generado el vídeo.
5. Revisa `attempt.json`, `validation.json` y `SHA256SUMS`. Si el último intento falló, el README lo indicará; un MP4 anterior no se presenta como un resultado nuevo.

Si la interfaz móvil oculta **Run workflow**, abre GitHub en Chrome/Samsung Internet con la vista de escritorio. Eso no requiere disponer de un ordenador.

No se usa almacenamiento de Artifacts: el MP4 pequeño y los informes se guardan por Git en una rama separada. El código permanece en `main`. Las etiquetas `render-*` también permiten iniciar una prueba explícita por Git cuando la API no está disponible. Un push normal a `main` no lanza renders automáticamente.

## Coste y límites

- Programas libres: Python, Pillow, eSpeak NG, FFmpeg y tipografías DejaVu.
- El render no solicita imágenes, audio ni texto a APIs externas. No necesita claves de pago.
- GitHub Actions solo permite el trabajo en **repositorio público y runner estándar `ubuntu-24.04`**. No usa GPU, runners grandes, suscripciones adicionales ni programaciones periódicas.
- No se necesitan credenciales de YouTube; no hay código de subida a YouTube.
- Límite por prueba: 150 segundos de vídeo y 20 MiB por MP4. Una única ejecución concurrente, con timeout de 15 minutos.
- El token automático de GitHub es una credencial técnica para escribir la rama de resultados; no es un servicio de IA facturado por tokens.
- El runner Linux estándar de repositorios públicos es la opción gratuita de GitHub. Su disponibilidad, límites y políticas no los controla AutoStudio. No actives opciones facturadas ni un presupuesto de pago para solucionar un bloqueo. No se promete una infraestructura gratuita ilimitada.

## Qué produce realmente

Tres escenas con diagramas originales animados, narración española local y subtítulos aproximados. Exporta H.264 720×1280, 25 fps, AAC estéreo 48 kHz y MP4 fast-start compatible con reproductores móviles habituales. La voz original se sintetiza a la frecuencia de eSpeak; convertirla a 48 kHz no la convierte en una voz de estudio.

La validación decodifica todo el MP4, comprueba audio/vídeo, duración, presencia de señal sonora, clipping, tamaño, fast-start y SHA-256. Esto no sustituye escuchar la voz ni comprobar los hechos científicos.

Los diagramas **no son filmaciones submarinas**, ni imágenes fotorrealistas generadas por IA. Los subtítulos usan estimación temporal, no alineación palabra por palabra. El guion está escrito y requiere revisión editorial humana. Las referencias del ejemplo no equivalen a una investigación autónoma.

## Ejecución reproducible en la nube

GitHub Actions instala los programas libres y ejecuta:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/render.py --out output
```

Cuando no hay ejecutable `espeak-ng`, el entorno de desarrollo puede instalar `requirements-local.txt`: incluye una biblioteca local de eSpeak NG. No utiliza un servicio remoto.

Cada ejecución crea una carpeta nueva en `output/`; no sobrescribe vídeos anteriores. `output/latest.json` apunta al último resultado verificado. El publicador solo acepta una salida de **esa ejecución real de GitHub Actions**, con commit y hash coincidentes. Rechaza presentar un render local como un run de GitHub.

## Estructura

- `.github/workflows/create-short.yml`: ejecución manual o por etiqueta, solo en público.
- `scripts/render.py`: montaje y exportación.
- `scripts/narration.py`: voz local, sin sustitución silenciosa por silencio.
- `scripts/artwork.py`: esquemas originales y tipografía segura.
- `scripts/validate_video.py`: verificación del MP4 real.
- `scripts/publish_result.py`: resultado descargable mediante Git; nunca cambia `main` ni fuerza pushes.
- `scripts/ocean.json`: guion y referencias del ejemplo.
- `tests/`: pruebas de datos, seguridad, diseño y detección de silencio.
- `source_upload/`: ZIP original aportado, conservado para auditoría.
- `docs/REVIEW.md`: revisión de defectos y estado real de la entrega.

El repositorio público deja visibles el código y los guiones. No subas credenciales ni datos personales. No se ha impuesto una nueva licencia al código aportado; la gratuidad de las herramientas no modifica por sí sola la titularidad del proyecto.
