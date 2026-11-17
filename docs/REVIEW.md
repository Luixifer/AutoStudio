# AutoStudio — revisión del MVP aportado y estado de pruebas

## Código recibido

El ZIP original era accesible, íntegro y contenía README, un workflow, un renderizador, un guion y una carpeta de pruebas vacía. Se conserva intacto en `source_upload/`.

Defectos detectados:

1. Se verificaba la resolución, pero no la existencia de narración audible, decodificación completa, clipping, duración coherente o fast-start.
2. El supuesto zoom dependía de `zoom` con `d=1`; podía reiniciarse por cada imagen de entrada. Tampoco había movimiento propio en los esquemas.
3. El texto se ajustaba por caracteres, sin comprobar anchura real ni posibles desbordamientos.
4. La codificación por segmentos con `-shortest` podía eliminar la pausa prevista. Concatenar AAC por segmentos podía introducir discontinuidades.
5. No había subtítulos, pruebas automatizadas, hashes ni procedencia de ejecución suficiente.
6. El guion podía sugerir independencia absoluta de la fotosíntesis. Se ha matizado la dependencia de algunas reacciones del oxígeno producido en la superficie.
7. El workflow usaba etiquetas móviles de acciones y no diferenciaba claramente las condiciones de coste de infraestructura ni la facilidad de descarga desde móvil.

## Cambios

- Tres esquemas animados con código original. No se incorporan imágenes o música externas.
- Voz española real mediante eSpeak NG local. Falla si la voz no está disponible; no la reemplaza por silencio.
- Salidas versionadas por ejecución, voz completa sin concatenar AAC intermedio y verificación del MP4.
- H.264/yuv420p, AAC estéreo, 720×1280, 25 fps y fast-start.
- Subtítulos incrustados y SRT separado con tiempos aproximados, declarados como tales.
- Validación de datos y áreas de texto por píxeles.
- 16 pruebas automatizadas, incluida la detección de un MP4 realmente silencioso usado solo como fixture temporal.
- Workflow para repositorio público, runner Linux estándar, ejecución manual/etiqueta, sin cron ni servicios de IA de pago.
- Descarga por la rama `video-preview`, sin usar almacenamiento de Artifacts. La rama registra intentos fallidos y no presenta un vídeo antiguo como una generación nueva.
- El publicador rechaza atribuir a GitHub Actions un vídeo producido fuera de esa ejecución.

## Ejecución y limitaciones

Se ha generado y verificado un MP4 narrado real en el entorno Cloud de desarrollo. Eso no demuestra que GitHub Actions se haya ejecutado: las pruebas de GitHub se registrarán únicamente cuando una ejecución real pueda verificarse.

El acceso de escritura se ha recuperado tras la actualización de permisos del usuario. Se recuperó el commit local `09592f1`, sin reconstruir ni sobrescribir el proyecto. Las 16 pruebas se repitieron antes de subirlo y pasaron.

El código está en `main`. La etiqueta `render-recuperacion-20261117T104811Z` inició una ejecución real de GitHub Actions:

- Ejecución: https://github.com/Luixifer/AutoStudio/actions/runs/44068185619
- Commit de código ejecutado: `09592f1810bd294856b25a3f953e9b85d419a09c`.
- Commit de resultados: `81eb7dfb0874b4483c86b45b1894f1a7bf1ff95b`, rama `video-preview`.
- Las 16 pruebas también pasan en el runner real, según `video-preview/logs/unit-tests.txt`.
- El workflow finalizó correctamente, incluida la publicación del resultado por Git.
- Se descargó el MP4 público y se volvió a verificar su decodificación y hash fuera de Actions.

La API de GitHub continúa bloqueada en este entorno; no ha impedido la ejecución: se activó por etiqueta Git y se verificó mediante la página pública y los archivos reales de la rama de resultados. El rechazo de escritura 403 anterior queda resuelto.

### MP4 generado en GitHub

- Duración: 41,08 segundos; 1027 fotogramas a 25 fps.
- Imagen: H.264 / yuv420p, 720×1280.
- Audio: eSpeak NG CLI, voz `es`, AAC estéreo de 48 kHz.
- Tamaño: 1.642.620 bytes.
- SHA-256: `e26c5500aaf0649db7c01ec3859a7ad68725e52d4c72a379443bee6dd70fbf6c`.
- Audio decodificado: RMS −20,83 dBFS; pico −3,81 dBFS; sin muestras a escala completa; no es una evaluación semántica ni de naturalidad.
- Descarga: https://raw.githubusercontent.com/Luixifer/AutoStudio/81eb7dfb0874b4483c86b45b1894f1a7bf1ff95b/short_ciencia_demo.mp4
- Informes: https://github.com/Luixifer/AutoStudio/tree/video-preview

La publicación en YouTube permanece desactivada. No se han utilizado servicios de IA facturados, GPU ni runners de pago. La prueba física y la valoración perceptiva en Samsung quedan a cargo del usuario.

## Evaluación de calidad

- **Voz:** sintetizada y robótica; no es narración profesional ni se ha acreditado una escucha física en Samsung.
- **Imagen:** diagramas originales sencillos, no documental cinematográfico ni filmación real.
- **Subtítulos:** aproximados; pueden adelantarse/retrasarse respecto a palabras concretas.
- **Edición:** cortes entre tres escenas, sin música, foley, investigación autónoma o composición cinematográfica.
- **Ciencia:** guion de prueba pendiente de revisión editorial. Los enlaces NOAA/WHOI aportados no pudieron recuperarse en este entorno por bloqueo 403; no se presentan como fuentes consultadas en esta ejecución.
- **Móvil:** codecs/dimensiones y reproducción de software verificables; la prueba física en el S25 Ultra la realizará el usuario.
- **Coste:** las herramientas y voces empleadas son locales y gratuitas; no hay APIs de pago. La configuración evita runners privados/grandes, GPU, Artifacts y automatismos periódicos. No se ha inspeccionado ni modificado la facturación de la cuenta GitHub.

Esto es una base verificable para un MVP, no una fábrica cinematográfica autónoma aprobada.
