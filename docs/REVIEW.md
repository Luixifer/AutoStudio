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

El repositorio público `https://github.com/Luixifer/AutoStudio` existe y se ha leído su commit inicial. El intento de escritura por Git ha devuelto `Permission to Luixifer/AutoStudio.git denied to Luixifer` / HTTP 403. La API de GitHub también está bloqueada por la política de red del entorno. Son dos impedimentos distintos: lectura pública no equivale a permiso de escritura.

La autorización pendiente debe resolverse en la conexión GitHub de Codex, incluyendo el repositorio AutoStudio y permiso de escritura de su código y workflows. No se necesitan tokens pegados en el chat. La prueba se puede iniciar por etiqueta Git sin depender de la API cuando la escritura funcione.

## Evaluación de calidad

- **Voz:** sintetizada y robótica; no es narración profesional ni se ha acreditado una escucha física en Samsung.
- **Imagen:** diagramas originales sencillos, no documental cinematográfico ni filmación real.
- **Subtítulos:** aproximados; pueden adelantarse/retrasarse respecto a palabras concretas.
- **Edición:** cortes entre tres escenas, sin música, foley, investigación autónoma o composición cinematográfica.
- **Ciencia:** guion de prueba pendiente de revisión editorial. Los enlaces NOAA/WHOI aportados no pudieron recuperarse en este entorno por bloqueo 403; no se presentan como fuentes consultadas en esta ejecución.
- **Móvil:** codecs/dimensiones y reproducción de software verificables; la prueba física en el S25 Ultra la realizará el usuario.
- **Coste:** las herramientas y voces empleadas son locales y gratuitas; no hay APIs de pago. La configuración evita runners privados/grandes, GPU, Artifacts y automatismos periódicos. No se ha inspeccionado ni modificado la facturación de la cuenta GitHub.

Esto es una base verificable para un MVP, no una fábrica cinematográfica autónoma aprobada.
