# Validación y estado de entrega · incidencia 80

## Verificado

Ejecución real: https://github.com/Luixifer/AutoStudio/actions/runs/44928112895

Código ejecutado: `93d74c8c2229e8f0bb7742c8b835997e776bd206`, rama `codex/hessdalen-issue-80`. La rama independiente conserva la historia de Director 2. No hay merge en `main`.

- **341 pruebas completas superadas en GitHub Actions**: [registro](evidence/github-regressions-341.txt). Incluyen renderizados reales de FFmpeg, regresiones Android/JVM existentes, contratos de párrafos y subtítulos, capítulos y recuperación de caché, además de pruebas nuevas de subplanos y plan editorial incompleto. Las comprobaciones de transporte de caché usan dobles explícitos; no se presentan como dos trabajos reales enviados por Android.
- **Prueba neuronal real de 13,966667 s**, 1920×1080 y 30 fps: [informe](evidence/subshot-proof.json). Un solo párrafo, tres recursos originales de comprobación y una sola locución Kokoro CPU. Se comprueba el vídeo renderizado, sus muestras por plano, subtítulos, audio y decodificación. Es una prueba técnica, NO Hessdalen.
- Reemplazo de la imagen central: el audio y los planos primero/tercero se reutilizan, el plano segundo se renderiza de nuevo. SHA del audio sin cambios; correspondencia de los tres planos aprobada. Se vuelve a ensamblar y validar el MP4 final.
- Copia de cachés a otra carpeta de ejecución: nuevo ensamblaje verificado sin rutas absolutas inválidas; narración y escenas reutilizadas.
- El callback de final de capítulo se ejecuta tras persistir su checkpoint. No se confunde con la ruta del archivo de checkpoint.
- Una prueba negativa del MP4 previo, comparado con los nuevos recursos, falla específicamente en el plano sustituido.
- Actionlint aprobó los workflows; no hay credenciales ni medios privados en la evidencia.
- **Plan de Hessdalen rechazado como incompleto**, correctamente: [informe de preparación](evidence/readiness.json). Tiene 30 planos y 7 bloques, pero no contiene guion, anclajes ni archivos inventados. Ese rechazo editorial no se oculta detrás del éxito de las pruebas técnicas.
- [Consulta real de fuentes](evidence/official-source-access.json): portada y `/reports` accesibles; las antiguas rutas `/reports/hpreport84.shtml` y `/station/` devuelven 404. La portada menciona 1984 y 1998; `/reports` contiene testimonios asociados a 1981. Son referencias del propio proyecto, no corroboración independiente ni licencia de metraje. Los extractos se conservan con URL, fecha y hash.
- [Comentarios públicos de #80](evidence/issue80-public-comments.json): lista vacía; no hay guion ni adjuntos allí.

Se añadió además una prueba real de subplano MP4 después de una disolución entre párrafos: verifica los tiempos de palabras desplazados por la transición, el audio intacto y la correspondencia visual. Su ejecución local aislada pasó. La batería local final completa también pasó: **342 pruebas en 80,927 s**, [registro local](evidence/local-regressions-342.txt), distinguiéndola de las 341 de Actions y su commit anterior. Los únicos cambios posteriores al motor probado en Actions son esta prueba adicional y documentación.

## No probado / no completado

- **El documental real de Hessdalen no existe todavía**. Falta el guion aprobado y sus recursos autorizados. No se ha estirado un texto de prueba a cinco minutos.
- Calidad cinematográfica, escucha humana, voz documental natural española y pronunciación de Hessdalen: pendientes.
- Revisión editorial y científica, pertinencia de cada plano y derechos efectivos: pendientes. Un recurso que pasa SHA y comparación de fotogramas puede seguir siendo editorialmente incorrecto.
- Rótulos definitivos de recreación/archivo/hipótesis: pendientes de los recursos reales y del montaje editorial.
- Editor Android de subplanos por frase y ciclo privado de reemplazo entre dos trabajos: pendientes. La APK estable no se ha cambiado, reconstruido ni presentado como una APK nueva.
- No hay nueva prueba física en Samsung; la evidencia nueva es CPU Linux/Actions, no rendimiento Android físico. Las pruebas JVM anteriores siguen incluidas, pero no equivalen a abrir una nueva APK en el teléfono.
- No se entrega otro MP4 técnico como si fuera el objetivo artístico. No se publica en YouTube ni se habilitan servicios de pago.

## Siguiente acción concreta

Recibir el guion definitivo y los archivos o enlaces con permisos. Importar los párrafos sin reescribirlos, asociar los 30 planos a frases reales, confirmar fuentes y permisos, medir la locución completa y ajustar el número de planos a su duración real. Solo entonces renderizar el capítulo, revisar escucha/imagen de principio a fin y entregar su MP4 con SHA-256 y sus dos informes de QA, técnico y editorial.

## Confirmación del usuario

El usuario ha confirmado en esta sesión: «aún no los tengo», en respuesta a la solicitud del guion definitivo y los recursos. El bloqueo de producción es, por tanto, confirmado y no un fallo del renderizador. No se solicita otro enlace ni se redacta un documental de sustitución. El trabajo se retoma cuando esos materiales estén disponibles.
