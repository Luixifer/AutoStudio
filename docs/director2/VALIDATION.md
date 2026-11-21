# Validación real de Director 2 — 21 de noviembre de 2026

## Entregables descargables

- [APK Director 2.0.0 LAB](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44922919559/AutoStudio-Director-2.0.0-lab.apk).
- [Capítulo técnico de 5:07,333](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44921580504/Director-2-five-scenes-44921968829-NOT-HESSDALEN-documental-REVISION.mp4).
- [Prueba original del usuario corregida, privada](https://github.com/Luixifer/AutoStudio/releases/tag/untagged-8fb7717f71224f63922d). Requiere iniciar sesión como propietario del repositorio. No es un enlace público anónimo y sus imágenes/texto no se han publicado. Contiene también un ZIP del proyecto corregido para recuperarlo; la versión original permanece intacta.

## Auditoría de la prueba realmente enviada

Solicitud original `9126b046336b46028f9ffcd6b13ba31e`, render **44885499433**, código `2ec4e4d`, 5,466667 segundos. Había tres párrafos y tres escenas, **pero los textos no coincidían párrafo a párrafo**. No bastaba comprobar el número de escenas. [Informe sin contenido privado](evidence/android-source-audit.json).

Se reconstruyó la relación con el texto original y el orden original de los tres recursos en otra entrega privada. Run **44922706382**, código `e202956`, solicitud nueva `cb4e6a368114fa095418894c17f51840`: tres escenas, **6,566667 s**, validación técnica y correspondencia aprobadas. El MP4 entregado se volvió a descargar por la API oficial y su SHA coincidió: `4a026c7719168538c8d5564573c9b4f8f2380b6a1fdc06370606a376602b6946`. [Informe seguro](evidence/original-repair-safe-report.json). No se cambió el resultado ni los archivos del trabajo anterior.

Esta es la prueba breve recuperada; no sustituye el capítulo completo de cinco minutos de Hessdalen.

## APK verificada y recorrido Android

Ejecución **[44922919559](https://github.com/Luixifer/AutoStudio/actions/runs/44922919559)**, fuente APK `41ec018aaf05495093f5a90b62b420e209c3bd1f`, aprobada:

- Android 15 emulado, 450×800; no Samsung físico.
- Guion de dos párrafos, dos imágenes importadas en bloque mediante ContentResolver, escenas independientes y texto íntegro.
- Prueba de rechazo de un recurso faltante; reordenamiento conservando ID y recurso; importación JSON conservando IDs de capítulo y escena.
- Inicio real desde la APK → producción **44923292174** → descarga, SHA y reproducción nativa de un MP4 de **10,766667 s**; fotograma mostrado y avance de 3068 ms.
- Force-stop → proceso nuevo → mismo proyecto y credencial cifrada → reproducción → Guardar en Descargas. SHA exportado idéntico: `1ba342e0cdc1170ef7bdf1f71ad8a71ea492130288eab189a350f3f03764e5c6`.
- APK pública descargada y verificada con apksigner, firma debug **v2/v3**. **148.003 bytes**, SHA-256 `6bf1c7df1f5a98009c6ae7020a6e5489b7a19138291d1dc612674177fa70afe7`.
- Paquete `com.luixifer.autostudio.director.lab04`, `director-2.0.0-lab`; coexiste con LAB3. No borra sus proyectos ni copia credenciales entre aplicaciones.

[APK y procedencia](evidence/android-apk-info.json), [ida/vuelta](evidence/android-roundtrip.json), [recuperación](evidence/android-recovery.json), [firma](evidence/android-signature.txt), [captura real](evidence/android-simple-editor.png).

La selección visual en el selector SAF y la comodidad de edición siguen pendientes de prueba física. La automatización sí abrió URI reales y copió sus archivos; no se presenta como una interacción manual completa con el selector Samsung. El audio del emulador estaba desactivado: mostrar un fotograma y avanzar el reloj no aprueba la voz ni los altavoces.

## Capítulo de cinco minutos ejecutado y descargado

Ejecución **[44921968829](https://github.com/Luixifer/AutoStudio/actions/runs/44921968829)**, fuente `09e90e0`, aprobada:

- Cinco párrafos originales y cinco archivos originales distintos; 1920×1080, 30 FPS, H.264/yuv420p, AAC estéreo 48 kHz, faststart.
- **307,333333 s**, **23.998.671 bytes**, 89 cues. SHA-256 `1ef2ccdb8547d495840042de151898aeddc7eeec741106f21e43aa8ead89e2cc`.
- Se verificaron texto y límites de subtítulos, fuente y orden de cada escena, cinco muestras visuales por narración y correlación del PCM con el audio de cada párrafo. [Tabla por escena](SCENE_REPORT.md).
- El MP4 público se descargó de nuevo: mismo SHA, **decodificación completa aprobada**, sin errores ni intervalos negros detectados. Pico observado -4,280437 dBFS, sin clipping detectado. No equivale a medición de sonoridad percibida ni a escucha humana.
- Tiempo real del render/QA en runner: **452,187 s**, máximo de procesos hijos **940.004 KiB** (unos 918 MiB). Son contadores Linux, **no métricas del Samsung**.

[QA de nube](evidence/five-scene-validation.json), [QA de descarga](evidence/five-scene-downloaded-verification.json), [recursos](evidence/five-scene-resources.json), [fotograma 1](evidence/five-scene-scene-1.png), [fotograma 3](evidence/five-scene-scene-3.png), [fotograma 5](evidence/five-scene-scene-5.png).

## Regresiones y casos negativos

**331 pruebas Python locales aprobadas** después del endurecimiento de identidad de capítulos; [registro completo](evidence/regressions-331.txt). Incluyen FFmpeg real: cinco escenas, disoluciones solo en silencios, cambio de imágenes detectado como error, vídeo e imágenes mezclados, clip anamórfico a 24 FPS normalizado, captions, audio, capas, recuperación y conservación de pruebas antiguas. Se mantienen las 22 comprobaciones JVM anteriores y la suite de párrafos estrictos.

Las regresiones del motor también se ejecutaron en GitHub: **[44924706446](https://github.com/Luixifer/AutoStudio/actions/runs/44924706446)** aprobó el código `632d423` con la identidad reforzada de capítulos; también está aprobada **44922706282**. Los backends sintéticos de pruebas unitarias no se presentan como voces humanas o pruebas físicas. Las demostraciones narradas citadas arriba sí utilizaron Kokoro CPU real.

La prueba negativa produce un segundo MP4 intercambiando realmente dos imágenes y lo comprueba contra el manifiesto original: las dos escenas afectadas deben fallar y las tres restantes deben aprobar. Se comprueba además que cambiar los bytes de una imagen manteniendo nombre y JSON invalide un capítulo portátil anterior. Las identidades nuevas incluyen archivos y código del renderizador; no se acepta una caché solo porque conserve el nombre.

## Pendientes priorizados

1. Introducir y validar el capítulo completo de **Hessdalen** en la nueva APK: guion definitivo y recursos por párrafo. No se inventó ese material ni se usó la demostración técnica como sustituto.
2. Prueba física de esta revisión en Samsung: selector de documentos, edición, cambios de orientación, sonido, escucha completa y legibilidad.
3. Evaluación auditiva y editorial: naturalidad, interpretación, pronunciación de nombres y elección de imágenes. Una correspondencia técnica no determina el significado de una foto.
4. Render largo de 30–60 minutos, orquestación Android por capítulos y reutilización de caché entre runners. Existen herramientas portátiles; ese recorrido completo móvil todavía no está implementado.
5. Transferencias reanudables, reconciliación de envíos indeterminados, firma estable para actualizaciones y retención de adjuntos.
6. Edición avanzada de planos dentro de una escena, recorte semántico, Markdown completo y exportación de SRT desde la interfaz móvil. No se presentan como terminados.

El detector de negro es conservador: una escena nocturna legítima podría requerir revisión cuando se pruebe el material real. No se rebajaron sus límites para hacer pasar la demostración. No se publica en YouTube ni se activan servicios facturables.
