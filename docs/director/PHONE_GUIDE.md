# Usar AutoStudio Director desde el Samsung

## Modo sencillo de Director Fácil 0.2

[Descargar APK verificada](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44843101009/AutoStudio-Director-0.2.0-lab.apk). Se instala aparte de LAB2; conserva la anterior y configura la conexión una vez en esta nueva instalación.

Pulsa **Crear un vídeo**, escribe el título, pega el texto completo y selecciona tus imágenes de una vez. Revisa las miniaturas en orden y pulsa **Crear vídeo**. No necesitas dividir el guion ni editar cada escena. La aplicación reparte el texto y prepara la voz, las transiciones y los subtítulos.

El botón principal queda fijo en pantalla. Cuando termina la producción, usa **Ver mi vídeo → Guardar en Descargas**. En **Más opciones** puedes elegir formato vertical u otra voz; los clips, música y ajustes de cada escena permanecen en la edición avanzada.

[Cómo funciona el reparto automático y límites](EASY_MODE.md).

## Configuración y edición avanzada


Esta es una APK **LAB**, con paquete separado de las versiones anteriores. No desinstales las aplicaciones anteriores ni borres sus datos.

1. Instala la APK Director. Concede «instalar aplicaciones desconocidas» únicamente al navegador/gestor que utilices y vuelve a desactivarlo después.
2. En Ajustes conecta un token GitHub limitado a **Luixifer/AutoStudio**, con `Actions: lectura y escritura` y **`Contents: lectura y escritura`**. Este último permiso permite adjuntar archivos a un borrador. Un token anterior limitado a Contents de lectura no basta. El token se cifra con Android Keystore; no se incluye en la APK ni en el ZIP del proyecto.
3. Crea «Las luces de Hessdalen». Escribe/pega el guion o importa TXT UTF-8. **Un párrafo por escena**, separado por una línea en blanco. Para capítulos, añade un bloque `# Título del capítulo` separado por líneas en blanco. Si quieres conservar un proyecto ya montado, crea otro antes de reemplazar sus escenas.
4. Abre cada escena y adjunta JPG, PNG, WebP o MP4. Reorganiza con Subir/Bajar. Los originales importados se copian sin recomprimir. Los MP4 se silencian y, si no cubren la locución, deben sustituirse, recortarse o autorizar explícitamente su repetición.
5. Elige Álex/Santa/Dora, o adjunta WAV/MP3 de locución **por escena**. Para voz externa, el texto debe coincidir con lo que se dice; la alineación local puede exigir correcciones. La selección de voz todavía requiere evaluación auditiva por tu parte.
6. Añade opcionalmente música propia/licenciada y elige horizontal 1920×1080 o vertical 1080×1920. La interfaz LAB registra titularidad propia declarada; para medios ajenos con atribución detallada, el contrato JSON admite licencia, autor y URL, pero su formulario Android avanzado está pendiente.
7. Pulsa Generar documental y confirma los derechos. El ZIP máximo es 200 MiB; mantén abierta la APK durante la subida. No se suben vídeos al historial Git ni se publica en YouTube.
8. Consulta el resultado. Tras el envío, el render continúa en GitHub aunque cierres la APK. Al recuperar el MP4 se comprueban tamaño y SHA-256. Abre Reproducir y guarda en Descargas.

**Diagnóstico:** Actions → workflow «Guion e imágenes propios» → ejecución con el UUID guardado en tu proyecto. El borrador de Release `director-UUID` contiene entrada, `result.json`, validación y MP4 cuando termina. Un resultado fallido no se muestra como éxito.

No pulses repetidamente Generar tras un corte de red. Primero consulta la solicitud existente: una respuesta perdida no demuestra que GitHub no haya arrancado el trabajo. La recuperación automática de subidas y envíos indeterminados aún está en desarrollo.

Para evaluar Hessdalen, revisa a velocidad normal toda la narración, los movimientos, la exactitud del guion y los permisos del material. Las luces deben identificarse como grabación real o recreación según su procedencia. No se afirmará haber producido tu documental hasta procesar esos recursos.

Tras descargar y comprobar una producción, puedes eliminar **su borrador de Release** desde GitHub para retirar los adjuntos temporales. No elimines el proyecto del teléfono si quieres volver a montarlo.


## Primera revisión verificada

[Descargar APK Director LAB 0.1.1](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44807042861/AutoStudio-Director-0.1.1-lab.apk) · [Ejemplo técnico de 25,2 segundos](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/ensayo-tecnico-NO-HESSDALEN.mp4).

Se han verificado en Android emulado la generación, la recuperación tras force-stop y Guardar en Descargas, comprobando hashes. Falta probar físicamente esta revisión en tu Samsung. Para incidencias, indica título del proyecto, UUID mostrado, fase donde se detuvo y ejecución de GitHub; nunca incluyas tu token.


## Compatibilidad entre laboratorios

Esta entrega es **LAB2**, paquete `com.luixifer.autostudio.director.lab02`, independiente de LAB1 y de Control 0.3. No actualiza ni borra sus datos. Si ya creaste proyectos en LAB1, expórtalos como ZIP y restáuralos en LAB2; conserva la aplicación anterior hasta comprobar la copia. Las firmas son únicamente de depuración; no existe todavía una clave de publicación estable.

[Descargar ensayo técnico real de 4 min 59,4 s](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/AutoStudio-Director-ensayo-5min-NO-HESSDALEN-44804915434.mp4). Este vídeo repetitivo prueba duración, voz, montaje y exportación; **no es Hessdalen ni una muestra editorial aprobada**.
