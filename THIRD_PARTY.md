# Herramientas y procedencia

- Python: intérprete libre; distribución oficial/runner de GitHub.
- Pillow 12.3.0: procesamiento y dibujo de imágenes, licencia MIT-CMU (según metadatos de la distribución).
- eSpeak NG: sintetizador local libre, GPLv3 o posterior. El entorno de GitHub instala el paquete de Ubuntu; el entorno Cloud de prueba usa `espeakng-loader` 0.2.4 con su biblioteca/datos locales. No es un servicio de voz ni consume créditos.
- FFmpeg/libx264: programas libres disponibles en Debian/Ubuntu; los componentes habilitados determinan LGPL/GPL. No se redistribuyen ejecutables dentro del repositorio.
- DejaVu Sans: tipografías libres incluidas en `fonts-dejavu-core`; no se incluyen archivos TTF en el proyecto.
- GitHub Actions checkout/setup-python: acciones oficiales, fijadas a commits comprobados en sus repositorios oficiales. No se utilizan acciones de servicios de IA.
- actionlint 1.7.7 se ha usado como herramienta local de comprobación; descargado del repositorio oficial `rhysd/actionlint`, contrastando su SHA-256 con la lista de la misma publicación. No se requiere para generar vídeos.

Los esquemas se dibujan con código del proyecto. No se incorporan imágenes de Internet, vídeos de terceros, música comercial ni voces clonadas. Las referencias científicas son enlaces editoriales, no recursos gráficos descargados.

El ZIP original del usuario se conserva sin cambios; SHA-256: `4b6ac66a9f9f605f672fb96e23744b57b0d2f08e82d5069a08b5683485777be9`.

## Revisión audiovisual 0.2

- **Kokoro ONNX 0.6.1**, MIT; **modelo Kokoro 82M v1.0 y paquete de voces**, Apache-2.0 según la documentación del distribuidor. [README oficial, sección License](https://github.com/thewh1teagle/kokoro-onnx#license). Descargas desde su publicación `model-files-v1.1`; URLs y SHA-256 verificados con los digests del propio GitHub en `assets/voice-models.json`. Los modelos no se redistribuyen dentro del repositorio. Voz española `ef_dora`, sin clonación encargada de una persona ni servicio remoto de inferencia. No se afirma que su licencia garantice pronunciación o acento: revisar ambos antes de publicar.
- **ONNX Runtime** (MIT), **NumPy** (BSD-3-Clause), **phonemizer** (GPL-3.0) y **espeakng-loader/eSpeak NG** para fonemización local. Dependencias directas fijadas en `requirements-neural.txt`; eSpeak NG sigue siendo GPL-3.0 o posterior. No se distribuyen estas herramientas dentro del vídeo.
- **Blender 4.3.2**, GPL-2.0 o posterior: ilustraciones originales creadas mediante el script y el maestro editable del proyecto. No se incorporan modelos, texturas o fotografías de terceros. La licencia de Blender no impone su GPL al vídeo/render original.
- Ambiente sonoro generado mediante ruido filtrado reproducible y transiciones originales del proyecto; no se usa música ni efectos ajenos.
- `assets/cinematic/manifest.json` registra hashes, dimensiones, procedencia, iluminación virtual y el filtro espacial de reducción de ruido aplicado a los renders.

Las referencias científicas NOAA/WHOI siguen siendo enlaces editoriales. Su acceso está bloqueado en este entorno; no se presentan como páginas consultadas ni como licencias de imágenes. No se ha descargado material visual de esas fuentes. La evidencia y licencias del modelo se han consultado en GitHub; la ficha de voces enlazada en Hugging Face no era accesible aquí.
