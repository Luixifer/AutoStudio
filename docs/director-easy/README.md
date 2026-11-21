# AutoStudio Fácil · revisión móvil 2.1 LAB

Objetivo: reducir la preparación de un documental sin cambiar el motor estable, la narración ni las asociaciones texto–imagen. Rama independiente: `codex/director-mobile-simplify`. La APK estable LAB4 y su historial permanecen disponibles; no se hace merge en main.

## Uso desde el teléfono

1. **Crear un vídeo**. Escribir título y pegar el guion. Separar párrafos con una línea en blanco. Pulsar **Continuar · añadir imágenes**.
2. Elegir varias imágenes/vídeos o pulsar **Añadir imagen o vídeo** en cada tarjeta. Comprobar las miniaturas y su texto. Si algo no corresponde, usar **Cambiar imagen o vídeo** en esa tarjeta.
3. Cuando todas las escenas tengan recurso, pulsar **Generar documental**, confirmar los permisos sobre el material y esperar la producción. Después usar **Ver mi documental** y **Guardar en Descargas**.

No se necesitan archivos JSON, carpetas, nombres técnicos, tiempos por escena ni rellenar treinta filas de un guion técnico. La aplicación conserva cada párrafo con su recurso y mide la narración durante la producción. La selección múltiple usa el orden que entrega el selector de Android: por eso hay miniaturas para revisarlo y sustitución directa por escena. No se afirma que el orden de pulsación de todos los proveedores de archivos esté garantizado.

### Lo opcional queda separado

**Opciones**, junto al título, permite cambiar los valores predeterminados. La voz inicial sigue siendo Álex y el vídeo horizontal. La música es opcional; no se inventan derechos ni se descarga material comercial. Los subtítulos y el editor avanzado siguen disponibles.

**Texto y más opciones**, en una escena, permite leer/corregir su párrafo, subir/bajar la escena completa y abrir el editor avanzado. Reordenar conserva juntos texto y recurso. Una escena con subplanos estructurados no se modifica silenciosamente desde el editor simple: exige revisar sus anclajes.

## Cambios de interfaz

- Acción inferior contextual: continuar, completar imágenes o generar. Se evita ofrecer generación cuando falta texto o recurso.
- Estado de tres pasos y contador de escenas con imagen.
- Adjuntar/cambiar recurso directamente desde la tarjeta, sin entrar en una pantalla técnica.
- Texto resumido a tres líneas en la lista; texto completo accesible para revisar y corregir.
- Reordenación y controles avanzados en un menú; menos botones simultáneos.
- Cancelar el selector no cambia asociaciones. Se conserva el ID de la escena seleccionada al recrear la actividad mientras está abierto el selector.
- No se acepta la repetición accidental de una imagen en otra escena. Los archivos anteriores se conservan.
- El título y el borrador siguen guardándose al salir. El montaje no cambia de motor: utiliza la revisión verificada `codex/director-2-scene-integrity`.

## Identidad y conexión

Compilación aislada: `com.luixifer.autostudio.director.lab05`, nombre **AutoStudio Fácil LAB**, archivo `AutoStudio-Director-2.1.0-facil-lab.apk`. No desinstalar la versión anterior. Sus proyectos y su conexión permanecen en su propio espacio.

Por estar aislada, la nueva aplicación no puede leer automáticamente las credenciales cifradas de la anterior. Requiere conectar GitHub una vez en su propia configuración. No hay token dentro de la APK ni se pide conexión en cada vídeo mientras la autorización siga válida. La generación sigue en GitHub Actions, no en el teléfono, y no publica en YouTube. Esto no elimina las restricciones de tamaño, duración y permisos del sistema existente.

Para transferir un proyecto completo, usar su copia ZIP desde la versión anterior y restaurarla en la nueva mediante **Copias y herramientas avanzadas**. No hace falta trasladar proyectos para probar el nuevo flujo con un borrador.

## Validación

Workflow específico: `.github/workflows/director-easy-check.yml`, solo runner estándar público. Ejecuta las regresiones completas, compila y verifica la firma de depuración, instala en Android 15 y prueba la interfaz real, selección múltiple, cancelación y sustitución directa de una imagen, conservación de las otras escenas, generación real en Actions, descarga, reproducción nativa, cierre/reapertura y exportación con SHA.

La instrumentación intercepta el selector de documentos y entrega URIs locales por el flujo de ActivityResult: prueba la integración real con ContentResolver y la interfaz, pero **no sustituye una prueba manual del selector de Galería/Mis Archivos en Samsung**. El acceso a GitHub se prueba con un token efímero de Actions; la conexión con el token personal del usuario y la comodidad en el S25 Ultra requieren su evaluación.

La ejecución final pasó y sus resultados se detallan debajo. No se considera esta compilación probada físicamente ni se declara que se haya producido Hessdalen: su guion y recursos siguen pendientes.

## Repetir la compilación

```bash
AUTOSTUDIO_DIRECTOR_BUILD=1 AUTOSTUDIO_EASY_BUILD=1 python android/build.py
```

Requiere JDK 17 y SDK Android 35 según `android/README.md`. Sin `AUTOSTUDIO_EASY_BUILD`, se conservan las variantes anteriores. Solo firma de depuración; ninguna clave de publicación ni API de pago.

## Revisión visual

La primera captura con el flujo funcional mostró demasiado espacio ocupado por tres botones globales. La revisión compacta coloca Opciones junto al título, deja la importación de otro guion en ese menú cuando ya hay escenas y oculta la selección múltiple cuando no falta ningún recurso. La acción principal permanece visible en la parte inferior.

## Entrega verificada

- [Descargar APK AutoStudio Fácil LAB](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44946181033/AutoStudio-Director-2.1.0-facil-lab.apk).
- [Actions final 44946181033](https://github.com/Luixifer/AutoStudio/actions/runs/44946181033): **342 pruebas superadas en 53,964 s**, compilación y firma, Android 15 y recuperación correctos.
- Motor del trabajo real: [44946506953](https://github.com/Luixifer/AutoStudio/actions/runs/44946506953), iniciado desde la APK. Produjo un MP4 técnico de **10,766667 s**, no Hessdalen. Reproducción nativa con fotograma decodificado y reloj a 2719 ms; después del cierre, reproducción recuperada y exportación en Descargas con SHA idéntico al resultado de la nube.
- Código de la APK: `32e1274e574d5ce31e0fa22c36edb77607ed8759`, árbol limpio. Paquete aislado LAB5; APK de 152099 bytes, descargada del enlace público y verificada de nuevo mediante ZIP/CRC y `apksigner` (v2 y v3).
- SHA-256 APK: `5cd8d9d25c0e2f98a420694cb6317cec271c59a44b00a6cb3d22005ec3d06cf3`.
- [Comprobación integral](evidence/check.json), [recuperación](evidence/recovery.json), [descarga independiente](evidence/download-verification.json), [firma](evidence/signature.txt).
- Capturas reales a 450×800: [pegar guion](evidence/step1-script.png), [escenas preparadas y cambio directo](evidence/simple-editor.png).

La primera ejecución 44944972920 falló porque el filtro del selector en la instrumentación no incluía su MIME y categoría OPENABLE; no se presentó como éxito. Tras corregir la prueba, 44945503995 completó el ciclo real. La revisión visual de sus capturas llevó a compactar la cabecera; la ejecución final 44946181033 volvió a completar el ciclo con ese ajuste.

### Qué falta evaluar en Samsung

Comodidad subjetiva, selector real de Galería/Mis Archivos y autorización personal. La prueba automatizada intercepta el selector y usa archivos de ensayo mediante ContentResolver; no significa que se haya probado físicamente en el S25 Ultra. Instalar al lado de la anterior, conectar una vez y probar con dos párrafos y dos imágenes propias es suficiente para revisar el nuevo flujo. No desinstalar la aplicación anterior ni borrar sus datos.
