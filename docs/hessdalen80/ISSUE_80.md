# Incidencia #80 — encargo íntegro

Fuente: https://github.com/Luixifer/AutoStudio/issues/80

## Objetivo
Producir **el primer capítulo REAL, de ~5 minutos, sobre las luces de Hessdalen** con AutoStudio Director 2, a partir del guion aprobado en la conversación con el usuario y **recursos visuales que realmente correspondan al significado de cada frase**. No considerar como capítulo real el demo de cinco escenas.

## Contexto verificable aportado por el usuario (2026-11-21)
- APK Director 2.0.0 LAB: https://github.com/Luixifer/AutoStudio/releases/download/director-check-44922919559/AutoStudio-Director-2.0.0-lab.apk
- Demo técnico 307,333333 s, NO Hessdalen: https://github.com/Luixifer/AutoStudio/releases/download/director-check-44921580504/Director-2-five-scenes-44921968829-NOT-HESSDALEN-documental-REVISION.mp4
- Android run 44922919559, render 44921968829, tests 44924706446.
- Según el informe, correspondencia texto-recurso ya validada en pruebas técnicas; aún no se ha revisado auditivamente ni producido Hessdalen.
- Atención: **la rama main accesible por el conector puede no contener Director 2**. Primero localizar commit/branch exacto de esas entregas y NO sobrescribir un código estable por una versión antigua. Si faltan archivos, reportar bloqueo con exactitud.

## Plan de ejecución por prioridad
1. Reconstruir el estado real de Director 2 desde commits/artefactos correspondientes, preservar una rama de trabajo y el baseline.
2. Crear plantilla de proyecto documental con capítulos, escenas y **subplanos** (varios planos visuales para un solo párrafo y una única narración, con tiempos delimitados). No confundir un párrafo con una sola imagen obligatoria.
3. Importar el **guion definitivo de Hessdalen aportado por el usuario**. Si no está disponible en el repositorio o sesión, ofrecer formato de importación y solicitar ese material concreto; no redactar contenido inventado ni usar texto de demo como sustituto.
4. Preparar **guion técnico/shot list** con ~25–35 planos organizados en 7 bloques: aparición nocturna; valle y testimonios de 1981; investigación 1984; vigilancia automatizada desde 1998; hipótesis físicas; límites del conocimiento; cierre y transición a señales de radio. Cada plano lleva: ID de escena, palabras/frase de inicio y fin, motivo visual, recurso exacto, duración objetivo, tipo de plano, movimiento y estado de derechos.
5. Distinguir **archivo real, recreación generada e hipótesis visualizada**; no atribuir como registro real imágenes de IA. Comprobar afirmaciones históricas y científicas con fuentes.
6. Aceptar imágenes JPG/PNG/WebP y clips IA MP4 proporcionados por el usuario. **No inventar recursos ni licencias**. Permitir previsualización por capítulo, reemplazo de planos, y guardado.
7. Narración: evaluar voz masculina español España (opciones existentes), pronunciación Hessdalen, cadencia de intriga, pausas, sonoridad y música con licencia. Escuchar o reportar explícitamente falta de escucha humana, sin afirmar aprobación artística automática.
8. Renderizar 1920×1080 30 fps H264/AAC, duración aprox. 4:45–5:30 guiada por voz real, movimientos fluidos, subtítulos opcionales discretos; **no estirar artificialmente texto**.
9. QA técnico: correspondencia subplano↔rango narrado, entradas/salidas, no escenas intercambiadas, decodificación completa, ausencia de negros accidentales, integridad de medios/sha, audio sin clipping, exportación y recuperación Android. QA editorial separado: imagen pertinente, narración convincente, tensión, ausencia de repetición visual, fuentes y licencias.
10. Entregar **MP4 real Hessdalen + proyecto editable/portátil + APK sólo si ha cambiado + informe de validación + lista de recursos pendientes y instrucciones de uso móvil**. No publicar en YouTube.

## Definición de terminado
- Se ve la escena correcta **mientras** se narra su contenido, sin saltos, imágenes equivocadas, ni repeticiones no deseadas.
- No hay evidencia visual falsa presentada como metraje histórico. Las hipótesis científicas no se presentan como hechos confirmados.
- Se verifican realmente audio y video renderizados; cualquier verificación no realizada figura como pendiente.
- El usuario puede reemplazar una imagen o clip de un plano desde Android sin rehacer todo el documental.
- Cuando la falta de imágenes/guion impida generar el capítulo verdadero, entregar el proyecto estructurado listo para rellenar, sin etiquetar el demo como terminado.

## Restricciones
Sin API de pago, sin publicación automática, sin eludir créditos o términos de plataformas, sin costes en GitHub o servicios cloud no autorizados. Avanzar de forma autónoma en tareas verificables; priorizar resultado reproducible sobre features decorativas.

