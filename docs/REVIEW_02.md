# AutoStudio 0.2 — revisión audiovisual

## Base conservada

La versión de 41,08 segundos sigue accesible por su commit fijo de resultados `81eb7dfb0874b4483c86b45b1894f1a7bf1ff95b` y por la etiqueta de código `baseline-mvp-41s`. El perfil `classic` mantiene sus tres diagramas, voz eSpeak y estimaciones temporales. El nuevo perfil no elimina esa opción.

## Diferencias comprobables en el producto

Ocho escenas editadas frente a tres; cinco imágenes 3D originales frente a esquemas planos; movimiento de encuadre, partículas y mezcla entre planos. No hay caja con narración completa. El texto aparece en grupos de hasta tres palabras y cambia de color según la duración de fonemas emitida por el modelo neural. Narración `ef_dora` sintetizada en CPU, no servicio online. Ambiente sintético a nivel bajo, voz normalizada y limitador.

La cobertura de cada palabra y el movimiento de cada plano se verifican durante el render. Las duraciones reales y los resultados de la ejecución se añadirán después de comprobar GitHub Actions; tener código escrito no cuenta como ejecución correcta.

## Revisión visual y límites honestos

- Las ilustraciones añaden relieve, perspectiva, iluminación, materiales y cambios de escala, pero tienen acabado estilizado y simplificado. No alcanzan todavía un documental cinematográfico competitivo ni son fotorrealistas.
- El filtro reduce ruido de los renders CPU a costa de suavizar detalles. Las partículas y movimientos de cámara no equivalen a animación 3D submarina completa: los animales y la salida de minerales están en imágenes fijas. El maestro y el generador permiten mejorarlos sin rehacer el montaje.
- La iluminación representa focos virtuales de exploración; el fondo marino no recibe luz solar. Las células son una ilustración explicativa, no fotomicrografía.
- La voz ahora utiliza un modelo neuronal, pero la naturalidad de España, acentos concretos y dicción científica necesitan escucha humana. No se afirma una evaluación física del audio en Samsung.
- Los tiempos provienen del modelo que genera el audio: mejor fundamento que proporciones por caracteres, pero pueden existir errores fonéticos. No se ha realizado una alineación independiente con ASR ni valoración auditiva humana de sincronía.
- La ausencia de clipping o silencio no prueba que la narración sea buena. El guion necesita comprobación científica antes de publicar; la precisión visual de especies y geometrías es ilustrativa.
- Las pruebas técnicas y las mediciones de cambio de píxeles no conceden aprobación estética automática.

## Siguiente salto de calidad

Primero evaluar el MP4 en móvil: voz, velocidad de lectura y comprensión. Después: rehacer el arte con mayor realismo, añadir animación real de fluidos o imágenes científicas con permisos comprobados y diseñar una banda sonora original más narrativa. No contratar ni activar servicios de pago para conseguirlo.
