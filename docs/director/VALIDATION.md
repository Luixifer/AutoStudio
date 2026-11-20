# Validación de Director — 20-11-2026

## Evidencia técnica ya obtenida

- Base remota auditada `2a7f633`: **248 pruebas Python** después de instalar una dependencia declarable que faltaba (`imageio-ffmpeg` para los motores procedurales).
- Editor personal recuperado de `e722cf9`: se conservan sus pruebas y el modo anterior. Se corrigió conversión JPEG/rango de color en FFmpeg 7 sin rebajar H264/yuv420p.
- Últimas regresiones de Actions previas a la aceptación Android: **312 pruebas Python**, incluyendo contratos, ZIP seguro, caché, clips insuficientes, parallax, HDR técnico, transiciones, audio real, capítulos portátiles y subtítulos. El informe de la ejecución de aceptación determina el resultado final del emulador; no se deduce de estas pruebas.
- **22 comprobaciones JVM**: 12 de formato opaco de credencial y diez de firmas de medios. Compilación con SDK35/JDK17 y firma debug verificada por apksigner.
- Ensayo horizontal final: **299,4 s, 1920×1080, 30 FPS, H264/yuv420p + AAC estéreo 48 kHz**, 51.956.589 bytes, SHA-256 `200bcaea1956ad26b516b41b9278e3be51e1e36a890db188286b30cf6c9c1841`. Decodificación completa, sin intervalos negros detectados, 264 cues sin solapamientos. [Informe](evidence/five-minute-validation.json).
- Recursos de ese ensayo en Linux: **694,51 s** de pared; máximo de procesos hijos **786.768 KiB**, unos 768 MiB. [Contadores](evidence/five-minute-linux-resources.json). No son métricas de Samsung ni un presupuesto garantizado para una hora.
- Ensayo vertical real **1080×1920** con voz Álex, imágenes, capa alpha, MP4 a 24 FPS normalizado a 30, música atenuada, transiciones y subtítulos: [validación](evidence/vertical-validation.json).
- Prueba portátil real: separar dos capítulos, renderizar, empaquetar vídeo/PCM/subtítulos con SHA y ensamblar; rechaza una parte de otra revisión. Esta prueba utiliza tonos, no evaluación de calidad de voz.

Los ensayos usan ilustraciones originales del repositorio, un patrón de vídeo y repeticiones intencionales de voz para medir el montaje. **No contienen el material del usuario ni son un documental de Hessdalen**. Las secuencias científicas originales tampoco se presentan como filmaciones reales.

## Fallos observados y corregidos

1. FFmpeg 7 producía yuvj420p/rango completo desde JPEG: conversión a rango limitado antes de los subtítulos, preservando el validador estricto.
2. Encadenar xfade con una frecuencia indeterminada fallaba: se normalizan FPS/SAR/timebase de entradas y salidas intermedias.
3. MIME nulo al importar una imagen válida en Android: se identifican JPG, PNG, WebP, MP4, WAV y MP3 por firma real; se conserva cada byte del original.
4. El QA intentaba leer JSON vacío cuando fallaba el emulador: el informe registra fracaso y existe una rama de diagnóstico independiente; no se convierte en éxito.
5. La automatización de Android no veía inicialmente la raíz de accesibilidad: se pulsa el botón real del diálogo de confirmación y se exige un fotograma renderizado en VideoView.
6. DNS transitorio de api.github.com al arrancar el emulador: se reutiliza el bootstrap GET probado del proyecto, con reintentos solo de lectura. No se reenvía automáticamente una producción POST.
7. Espacio libre consultado sobre un archivo de destino inexistente devolvía cero: ahora se consulta su carpeta existente. Se comprobó el comportamiento real de File.getUsableSpace.
8. Los cues ASS heredados prolongaban 80 ms sin respetar el siguiente cue: se acotan al cue siguiente/final y se corrige el acarreo de centésimas a minutos. Se revisó el ASS realmente utilizado por el benchmark final.

## Qué no está aprobado o completado

- No se ha procesado el guion ni los recursos de Hessdalen. Se introducirán desde la APK.
- No hay prueba física de esta APK en el S25 Ultra ni aprobación auditiva de la voz. Las muestras Álex/Santa están generadas; su naturalidad, profundidad e interpretación requieren escucha.
- 60 minutos es un límite de contrato; no una duración validada físicamente ni una promesa de render gratuito ilimitado.
- El motor portátil de capítulos está probado, pero su reparto automático desde la APK entre varios runners no está terminado. La producción integrada actual admite un ZIP de hasta 200 MiB.
- Las subidas/descargas requieren primer plano; reconciliación de envíos con respuesta perdida y transferencias reanudables siguen pendientes. Consultar antes de reenviar.
- La edición Android inicial importa TXT y recursos por escena; no incluye aún un editor visual avanzado de keyframes, créditos de terceros ni gestión virtualizada de centenares de tarjetas.
- El audio de los clips se silencia. La narración sustituible se importa por escena; todavía no se divide automáticamente una locución externa de una hora.
- Las decisiones de composición y nitidez, y los permisos del material, necesitan revisión humana. Ningún `passed` técnico significa «documental profesional aprobado».

## Aceptación Android real superada

Ejecución **[44803232978](https://github.com/Luixifer/AutoStudio/actions/runs/44803232978)**, source `356b5f54a96c4584709d186a45d374e0bd6df6ec`:

- Emulador Android 15, 450×800, perfil independiente; no dispositivo físico.
- Importación de imagen y MP3 por ContentResolver conservando SHA; copia ZIP y restauración como otro proyecto.
- Confirmación mediante el botón real de Android → creación de borrador/subida → workflow **[44803832152](https://github.com/Luixifer/AutoStudio/actions/runs/44803832152)** → MP4 de **25,2 s**, H264/AAC 1920×1080.
- La primera escena utiliza MP3 importado sin tiempos: **Whisper CPU real**, no un resultado inyectado. Las demás utilizan Kokoro CPU. La coincidencia textual y los tiempos reales superaron la validación del motor.
- Descarga íntegra por la APK, SHA `35a06b9b272afbbcb4f149141540de6dae3c027903abf8e8a28faddc88f27997`, fotograma realmente mostrado y reproducción avanzando.
- Force-stop real, nuevo proceso: proyecto y credencial cifrada recuperados, misma solicitud, VideoView nuevamente reproduce.
- Botón Guardar en Descargas → MediaStore real → lectura del archivo exportado y **el mismo SHA-256**.
- **312 pruebas Python + 22 comprobaciones JVM**. Firma APK **v2 y v3**, debug, verificada después de descargar el archivo público.

[APK verificable](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/AutoStudio-Director-0.1.0-lab.apk), **119.331 bytes**, SHA-256 `e6bd6fb3dd38470585a31077f3539d5f3f7eaae88f69414ffea7ed66bda66e62`.

[MP4 realmente recuperado por la APK](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/ensayo-tecnico-NO-HESSDALEN.mp4).

[Informe de ida y vuelta](evidence/android-roundtrip.json), [reinicio/exportación](evidence/android-recovery.json), [APK](evidence/android-apk-info.json), [firma](evidence/android-signature.txt), [captura real del emulador](evidence/android-preview.png).

El selector SAF del sistema y la audición de altavoces no se consideran físicamente validados: la automatización importó archivos reales mediante ContentResolver y el emulador usa salida de audio desactivada. La app mantiene la opción normal ACTION_OPEN_DOCUMENT para las pruebas del usuario en Samsung.

## Entrega del benchmark largo en Actions

En el primer intento **44801864837**, el render y su validación acabaron correctamente. Falló exclusivamente crear una Release nueva (**HTTP 403**). Se recuperaron los registros oficiales en **44804137747**; no se confundió ese fallo de entrega con un vídeo disponible para descargar. El siguiente intento adjunta el resultado a la Release ya verificada y comprueba permiso de subida **antes** de gastar tiempo en el render. No se amplían permisos ni se cambian políticas de seguridad.


La prueba adicional con MP3 descubrió una incompatibilidad real de la versión actual de PyAV con faster-whisper (`metadata_errors`). Se corrigió reutilizando la decodificación PCM16 existente, no atribuyendo una transcripción inyectada a un modelo real. Las ejecuciones Android aceptadas **44801247644** y **44803232978** volvieron a ejecutar el modelo CPU y completaron ese caso correctamente.

La dependencia `imageio-ffmpeg` que faltaba en la declaración común neuronal se añadió también allí: conserva la ejecución de las pruebas procedurales ya presentes en main. El conjunto de dependencias de Director no cambia por este traslado; no se modifica main ni se sustituye el renderer de Shorts.
