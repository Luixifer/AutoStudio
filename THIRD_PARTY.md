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
