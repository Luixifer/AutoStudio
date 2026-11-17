# AutoStudio Control LAB 0.3 — Android

Primera aplicación nativa de control. No es todavía el centro de producción completo. El APK contiene Java DEX, sin bibliotecas nativas: funciona en ARM64 (incluido S25 Ultra) y x86_64, Android 8 o posterior. Compila con SDK/target 35. La prueba física en Samsung la debe realizar el usuario; no se atribuyen al teléfono las pruebas de emulador.

## Descargar e instalar desde el móvil

[**Descargar APK verificada de LAB 0.3**](https://github.com/Luixifer/AutoStudio/raw/d0e5bfbede04afecc9abd561137bbe0d1d547087/AutoStudio-Control-0.3.0-lab.apk) · [ZIP alternativo verificado](https://github.com/Luixifer/AutoStudio/raw/d0e5bfbede04afecc9abd561137bbe0d1d547087/AutoStudio-Control-0.3.0-lab.zip)

La ejecución [44090864966](https://github.com/Luixifer/AutoStudio/actions/runs/44090864966) terminó correctamente: 57 regresiones Python, 12 comprobaciones JVM y recorrido completo real en Android 15 emulado. El APK publicado se descargó y verificó externamente (SHA-256 y firmas v2/v3). Estos enlaces están fijados a ese resultado para evitar descargar otro intento por error. Consulta [el informe y las limitaciones](VALIDATION.md).

SHA-256 del APK (66.018 bytes): `8d6d4c214471a109fef11ad7e81e1590052700d44cfde1d0058f52da61a341e7`.

La prueba usó una credencial temporal de GitHub Actions inyectada al test en ejecución; no forma parte del APK. **Tu cuenta personal y el S25 Ultra todavía requieren la configuración y la prueba descritas abajo.**

Abre el APK descargado desde Mis archivos. Si Android solicita permiso, autoriza la instalación desde el navegador o gestor de archivos que estés utilizando. Es una compilación de depuración, no una publicación en Google Play. Su identificador es `com.luixifer.autostudio.lab`: no utiliza datos de otros juegos ni aplicaciones anteriores.

## Conexión inicial, una sola vez

1. Abre **Conectar / ajustes de GitHub** → **Abrir GitHub para crear la credencial**.
2. En GitHub crea un **Fine-grained personal access token**, con propietario Luixifer y caducidad corta (por ejemplo, 30 días).
3. Selecciona **Only select repositories → AutoStudio**. En Repository permissions: **Actions: Read and write** y **Contents: Read-only**. Metadata se añade automáticamente. No autorices facturación ni otros repositorios.
4. Copia la credencial y pégala en la aplicación. Pulsa **Comprobar y guardar conexión**.

No envíes esta credencial a Codex ni a nadie por chat. La aplicación comprueba acceso de lectura; el permiso de ejecución se comprueba realmente al producir. No necesita claves de OpenAI ni de YouTube.

La credencial se cifra con AES-GCM y Android Keystore, se almacena únicamente en la instalación y se excluye de copias de seguridad/transferencia. No está incluida en el APK. Ajustes permite borrarla; GitHub permite revocarla. Esta solución no requiere servidor OAuth propio. Si caduca, vuelve a conectar. Un OAuth Device Flow cómodo requerirá registrar una aplicación de GitHub y será un incremento posterior, no un servicio de pago.

## Producir y recuperar el vídeo

Introduce **Fuentes hidrotermales**, **Quimiosíntesis** o **Vida sin Sol en el fondo del mar** → **Generar Short**. Estos temas usan el guion y las cinco ilustraciones originales ya revisadas del océano; no se genera un documental libre sobre cualquier asunto. El tema se registra y se valida: otros temas fallan expresamente, no se sustituyen a escondidas.

La app solicita `produce-short.yml` por HTTPS, guarda un identificador único antes de enviar y consulta exactamente ese trabajo. No escoge simplemente «el último vídeo». Si el envío queda incierto, busca el mismo identificador sin enviarlo otra vez automáticamente. No pulses otra producción ni ejecutes manualmente la misma solicitud.

Puedes salir: GitHub sigue trabajando. Al volver se reanuda la consulta, no la generación. La app necesita estar abierta para consultar y descargar; no promete ejecución Android permanente en segundo plano.

Cuando aparezca **Reproducir MP4**, el archivo ya se ha descargado y su tamaño/SHA-256 coinciden con el resultado de Actions. **Guardar MP4 en Descargas** crea una copia accesible desde Mis archivos. En Android 10+ no solicita permiso general de almacenamiento; en versiones anteriores usa el selector de archivos del sistema.

El tema, el guion, el MP4 y los registros son públicos en GitHub. No introduzcas datos privados. Los vídeos no se publican en YouTube.

## Qué está preparado y qué sigue pendiente

- Solicitudes y escenas versionadas: narración, duración real del audio/montaje, recurso, subtítulos, efectos y transición.
- Proveedores intercambiables `ScriptProvider` / `ImageProvider`; predeterminados gratuitos locales. El contrato de ChatGPT **rechaza su activación**: no hay cliente, clave ni llamada API.
- Biblioteca original con manifiesto, procedencia, resolución y hashes; historial de hasta 30 producciones del dispositivo y caché aproximada de 120 MiB como máximo tras una descarga. Los resultados remotos permanecen en Git.
- Vista de escenas **de revisión**, sin edición o regeneración parcial todavía.
- Un trabajo activo por instalación. Cola persistente, lotes, regeneración de una escena, nuevos proveedores temáticos y documentales quedan para después de validar este primer recorrido en el móvil.
- YouTube solo aparece como capacidad desactivada en los contratos. No hay publicación ni credenciales de YouTube.

No se ha rehecho el renderizador 0.2. Los perfiles `classic` y `cinematic` y sus salidas anteriores se conservan.

## Compilación en GitHub, sin ordenador

Desde GitHub en el navegador del móvil: **Actions → AutoStudio · APK Android y prueba integral → Run workflow**. En repositorio público y runner Linux estándar compila con herramientas gratuitas, inicia un emulador aislado y prueba el circuito completo. No usa Artifacts de pago: publica el APK y pruebas en la rama `android-preview`.

El workflow usa SDK oficial, JDK 17, `aapt2`, `javac`, D8, `zipalign` y `apksigner`, sin Gradle ni dependencias Android externas. `python android/build.py` reproduce el build con `ANDROID_HOME` y `JAVA_HOME` configurados.

La firma es de depuración. La clave privada se genera fuera de Git y del APK; no se publica. Las ejecuciones de CI pueden tener firmas diferentes: no se promete actualización sobre una APK previa con otra firma. Exporta tus MP4 y conserva la credencial de forma segura antes de cambiar de instalación; no desinstales una aplicación con datos importantes sin respaldarlos. Una firma estable de distribución se configurará por un canal seguro en una fase posterior.

## Pruebas físicas en Samsung

Comprueba conexión, un envío por pulsación, cambio de aplicación durante el render, retorno/reconexión, descarga, sonido, subtítulos, reproducción y Guardar en Descargas. Prueba Atrás y giro/multiventana. Comprueba que tras volver a abrir no se inicia otro trabajo y que el mismo MP4 sigue disponible sin red. Comunica versión, identificador de solicitud y enlace de Actions; nunca la credencial.
