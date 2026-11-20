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


## Entrega actual: LAB2 0.1.1

La ejecución **[44807042861](https://github.com/Luixifer/AutoStudio/actions/runs/44807042861)** está aprobada y conserva main intacta. Fuente APK `f4e7c07b543e9b692860f64d8e48477c0747af0e`. El cambio de configuración exige correctamente Contents lectura/escritura además de Actions; el paquete **`com.luixifer.autostudio.director.lab02`** coexiste con LAB1 y Control 0.3.

- [APK pública 0.1.1](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44807042861/AutoStudio-Director-0.1.1-lab.apk): **119.331 bytes**, SHA-256 **`94e0e9194675ff7aa0b687d4ae429ed8c13fc0caed5432a822911233a9c71318`**. Descargada y contrastada de nuevo. Firma debug v2/v3 comprobada con apksigner.
- Producción real iniciada por esta APK: [44807596572](https://github.com/Luixifer/AutoStudio/actions/runs/44807596572), 25,2 segundos. VideoView mostró un fotograma real y avanzó 2.790 ms. [Informe](evidence/lab02-roundtrip.json).
- Force-stop → arranque nuevo → misma solicitud y conexión cifrada → reproducción → exportación MediaStore: SHA **`3897fbe295b5a50b23dca93c3c7c6086867cc8621c6fb24bf0686b05013e1367`**, idéntico al original. [Recuperación](evidence/lab02-recovery.json), [firma](evidence/lab02-signature.txt), [captura](evidence/lab02-preview.png).
- Última ejecución local: **321 pruebas Python aprobadas, 49,719 s**. [Registro completo](evidence/regressions-321.txt). Incluye la prueba nueva de reintento ASR acotado y rechazo de discrepancias; no se presenta ese backend simulado como escucha física. La prueba Android anterior mantiene 22 comprobaciones JVM reales.

### Vídeo de cinco minutos realmente generado en GitHub

[Descargar MP4 técnico de 299,4 segundos](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/AutoStudio-Director-ensayo-5min-NO-HESSDALEN-44804915434.mp4).

**51.599.735 bytes**, SHA-256 **`2706ff5e9dfb46ed1445c7e6d5326bec04ac8093ac740b254e2ce70490f01813`**; 1920×1080, 30 FPS, H264/AAC, 264 cues. El archivo público se descargó y decodificó de principio a fin, sin errores ni intervalos negros detectados. [Verificación independiente](evidence/cloud-five-minute-delivery-verification.json).

La ejecución de render **44804915434** produjo y publicó correctamente vídeo e informes, pero su estado global es **fallido**: el último adjunto opcional `benchmark.log` estaba vacío y GitHub lo rechazó con HTTP 422. El fallo está identificado en registros oficiales; el publicador ahora omite adjuntos vacíos. No se atribuye estado verde a esa ejecución. Los contadores reales de ese runner fueron **456,378 s**, máximo de hijos **639.024 KiB**; no mediciones de Android.

### Cifras y audio importado: límite y diagnóstico

La ejecución adicional **44810268234** aprobó 320 regresiones y volvió a verificar el MP4 largo. Falló al alinear exactamente un MP3 con «1981, 3,5 y 60 minutos». El motor rechazó la discrepancia, sin inventar subtítulos. La revisión actual permite un único reintento CPU con Whisper `small` después de `base`, manteniendo la misma comparación exacta, y conserva texto detectado e intervalos en `alignment-diagnostic.json`.

Las cifras del guion se expanden antes de la síntesis, pero el texto original de los subtítulos se conserva mediante intervalos acústicos medidos. Una discrepancia sin resolver sigue siendo un error accionable. No se promete que un reconocedor automático transcriba correctamente cualquier nombre o cifra. La verificación adicional de esta revisión se registra separada del estado válido del MP4 ya entregado.


La ejecución **44836508982** también aprobó **321 pruebas en 48,203 s** y la verificación independiente del MP4. El diagnóstico acústico de ambos modelos reveló la causa concreta del rechazo de cifras: Whisper separa `3,5` en dos tokens consecutivos `3` y `,5`. No faltaba la palabra en la locución; fallaba la normalización de ese límite. [Transcripción real e intervalos](evidence/cloud-44836508982-alignment-diagnostic-0.json).

La corrección une únicamente esa sintaxis decimal cuando los tokens son acústicamente contiguos (máximo 80 ms), conserva el intervalo completo medido y sigue rechazando una cifra diferente o una separación temporal excesiva. Las pruebas correspondientes no aceptan `3,5` como `3,6` ni inventan tiempos. La comprobación real posterior se registra separadamente.


Tras corregir esa segmentación, la batería completa local aprobó **323 pruebas en 49,648 s** ([registro](evidence/regressions-323.txt)). Se volvió a aplicar el alineador a las transcripciones reales guardadas de `base` y `small`: ambas conservan las cifras y sus intervalos completos. Esta reproducción de diagnóstico no se confunde con una nueva inferencia: la inferencia y render nuevos se comprueban en la ejecución posterior de Actions.


## Verificación final en la nube: aprobada

La ejecución **[44836923942](https://github.com/Luixifer/AutoStudio/actions/runs/44836923942)**, código `1cc9fcc0770ce5babdb5bd1166de399e51d895a2`, terminó **correctamente**:

- 323 regresiones completas aprobadas en el runner.
- Descarga independiente del MP4 público de 299,4 s, verificación SHA y decodificación completa: **aprobado**; 264 cues. [Informe](evidence/cloud-44836923942-delivery-verification.json).
- Nueva síntesis Kokoro con cifras y nuevo MP3 importado con retardo real, transcrito por Whisper CPU y montado con FFmpeg: **aprobado**, conservando las cifras originales y los intervalos medidos. SHA del vídeo adicional: `5b03d806f832aedb6fcbe75ffe957a9c9d15d1a12020b19c39e3db7a38047d74`. [Informe](evidence/cloud-44836923942-language-verification.json).
- Los informes también se descargaron de los adjuntos públicos de Release para comprobar que la entrega existe. Este resultado resuelve el rechazo numérico anterior y confirma el MP4 largo existente; no cambia retrospectivamente el estado fallido de las ejecuciones antiguas.

La APK entregada sigue siendo LAB2 0.1.1, ya aceptada en Android emulado. Las correcciones de alineación se ejecutan en el motor de GitHub; no requieren reemplazar el binario del teléfono. La naturalidad de la voz, la revisión editorial de Hessdalen y la validación física de esta revisión continúan pendientes.
