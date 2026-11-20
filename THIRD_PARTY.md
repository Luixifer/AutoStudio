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

## Control Android 0.3

Aplicación nativa original en Java, sin bibliotecas Android externas. Se compila con el SDK oficial Android (aapt2, D8, zipalign, apksigner y plataforma 35; términos oficiales de Android SDK) y OpenJDK 17/Temurin (GPL con Classpath Exception). El repositorio no redistribuye los SDK, JDK, imágenes de emulador ni claves privadas de firma. El APK contiene el código de la aplicación y recursos propios; usa el reproductor del sistema Android. GitHub REST y el token de acceso del usuario autorizan Actions: no son APIs de IA ni servicios facturados por tokens.

## Contenido científico 0.4

24 ilustraciones 3D y tres maestros Blender originales, sin fotografías, texturas ni modelos externos. Procedencia y derechos en `assets/science_v04/LICENSE_ART.md` y manifiestos por tema. Animación ligera original siguiendo trayectorias del maestro, sin simulación física a escala. No hay nuevas dependencias de pago. Las páginas NASA/NOAA/NHGRI/USGS se consultan como referencias científicas, no se descargan sus imágenes; el informe de recuperación conserva URLs, títulos, hashes y extractos limitados para revisión editorial.


## AutoStudio Director LAB

- **faster-whisper 1.2.1** y **CTranslate2**, MIT: reconocimiento/alineación local CPU, sin API de inferencia. [Código y licencia](https://github.com/SYSTRAN/faster-whisper). Modelo Whisper multilingüe `base`, procedente de la conversión pública de SYSTRAN de los pesos OpenAI Whisper, bajo su licencia MIT. La descarga de pesos no equivale a utilizar la API comercial de OpenAI. No se instalan modelos GPU de pago.
- **PyAV** es una dependencia de faster-whisper (BSD-3-Clause; FFmpeg subyacente tiene sus propias condiciones). El lector de archivos de PyAV cambió su API `metadata_errors`; Director reutiliza la decodificación **FFmpeg → PCM16** ya existente y entrega muestras a Whisper. No depende de ese lector incompatible ni afirma que un modelo ASR sustituya la revisión humana.
- **imageio-ffmpeg 0.6.0**, BSD-2-Clause para el envoltorio Python; el binario FFmpeg incluido por su distribución tiene las condiciones de su compilación. Se declara la dependencia que ya utilizaban los motores procedurales/pruebas del repositorio. No se añade al APK.
- Director utiliza las voces locales `em_alex`, `em_santa` y opcionalmente `ef_dora` del paquete Kokoro ya documentado. No se afirma naturalidad, edad percibida, acento ni aprobación artística sin escucha humana.
- Los ensayos Director usan recursos originales del repositorio y patrones/sonido generados localmente, etiquetados como ensayos. **No son imágenes ni documental de Hessdalen**.
- En producciones personales, las imágenes, vídeos, voz y música proceden del usuario. Su licencia, autor y URL cuando correspondan deben declararse en el contrato; aceptar un archivo no certifica sus derechos ni hechos científicos. No se descarga música comercial ni se llama a proveedores de pago.
- Los motores Python/FFmpeg/Whisper/Kokoro se ejecutan en GitHub Actions, **no dentro de la APK**. La aplicación nativa sigue usando las API Android sin bibliotecas móviles externas ni credenciales incrustadas.

- **num2words 0.5.14**, LGPL-2.1: expansión local de cifras españolas antes de síntesis y comparación acústica. Se preservan las cifras originales en subtítulos y se proyectan sobre los intervalos realmente medidos; no se estiman marcas por número de palabras. No se incluye en la APK. Procedencia: https://github.com/savoirfairelinux/num2words .
- El reintento acotado de audio importado utiliza opcionalmente **Whisper `small`** CPU, de la misma procedencia MIT que `base`; no API comercial. Mantiene la exigencia de coincidencia textual exacta normalizada y genera diagnóstico si no puede alinear la locución.
