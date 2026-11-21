# Director Fácil — revisión 0.2.0 LAB3

## Recorrido habitual

1. Crear un vídeo.
2. Escribir título y pegar todo el texto.
3. Seleccionar varias imágenes de una vez y revisar sus miniaturas en orden.
4. Crear vídeo → confirmar permiso de uso → esperar → Ver mi vídeo → Guardar en Descargas.

La voz Álex, el formato horizontal Full HD, las disoluciones, el movimiento de cámara y los subtítulos ya están preparados. Formato vertical y otras voces están en Más opciones. La conexión GitHub es la configuración inicial, no un paso que haya que repetir para cada vídeo.

## Asociación de imágenes y texto

No se necesita separar párrafos ni asignar archivos a cada escena. El texto completo se agrupa de forma reproducible en fragmentos cercanos a cien palabras, buscando finales de frase próximos. Si hay más imágenes, se crean al menos tantos fragmentos como imágenes, siempre que haya texto suficiente. Las imágenes se utilizan consecutivamente; pueden mantenerse durante varios fragmentos largos. Los botones Antes/Después permiten cambiar el orden y Quitar elimina la asociación, sin borrar el archivo original importado.

Este reparto es editorial por orden: no identifica automáticamente el contenido de una imagen. No se presenta como montaje semántico mediante IA. Los espacios entre palabras se normalizan; no se eliminan palabras ni se cambia su orden. La duración final se sigue midiendo a partir de la voz real, no se estima con esta agrupación.

## Conservación y límites

Se reutilizan Profile de proyecto, importación, motor Director, conexión cifrada, generación, validación SHA y reproductor. No hay un segundo renderizador ni servicios de pago. Los proyectos anteriores mantienen su editor avanzado. Los nuevos se guardan automáticamente en el modo sencillo.

El modo sencillo acepta hasta treinta imágenes JPG/PNG/WebP y el presupuesto existente de 200 MiB por envío. Los MP4, música, locución propia y edición por escena siguen disponibles en el editor avanzado. Pasar a edición avanzada conserva las escenas compiladas y deja de regenerarlas automáticamente; sus cambios manuales no se sobrescriben al reabrir.

LAB3 utiliza otro paquete Android para coexistir con LAB2. Se conserva la aplicación anterior con sus proyectos y conexión: no hace falta desinstalarla. Las firmas de depuración de los runners son temporales, por lo que esta entrega no se presenta como actualización sobre la misma firma. La conexión GitHub tendrá que configurarse una vez en esta instalación separada; la versión comercial necesita una firma estable antes de distribuir actualizaciones.

## Validación

La compilación local con SDK35/JDK17 y las pruebas puras JVM del reparto ya se ejecutan como parte del build. La aceptación Android debe comprobar el formulario real, importación múltiple mediante ContentResolver, conservación del texto, compilación de escenas, envío al workflow, reproducción y exportación. La prueba automatizada no sustituye la elección manual de imágenes en el selector SAF de Samsung ni la evaluación física de comodidad.


## Primera comprobación real y revisión visual

En la ejecución 44842171362, el formulario sencillo produjo un MP4 de once segundos mediante la ejecución hija 44842610285. Android lo reprodujo, recuperó el proyecto tras force-stop y lo exportó por MediaStore con el mismo SHA. El informe registra selección múltiple y conservación íntegra del texto. Sin embargo, la captura del editor estaba tapada por un aviso ANR de **Pixel Launcher**, un proceso externo del emulador; esa imagen no se acepta como evidencia de una pantalla limpia.

La repetición cierra ese lanzador externo y exige que la ventana de accesibilidad en primer plano pertenezca realmente a la APK antes de capturar. No se elimina ni se maquilla el aviso de una imagen. La prueba funcional y la revisión visual se registran por separado; falta la evaluación física en Samsung.


## Entrega final verificada

[Descargar APK Director Fácil 0.2.0 LAB3](https://github.com/Luixifer/AutoStudio/releases/download/director-check-44843101009/AutoStudio-Director-0.2.0-lab.apk).

Ejecución **44843101009**, fuente `1ca9089`, aprobada. La producción real **44843473839** creó un MP4 de once segundos desde el formulario título/texto/imágenes. Se han comprobado reproducción nativa, recuperación tras force-stop, conexión cifrada y exportación en Descargas con el mismo SHA del MP4: `435f6bd89c5e2de5412967a9f8413f828c0df73ae04eaacdaeec5d884a7b27ac`.

APK pública descargada y verificada con apksigner (v2/v3), **135.715 bytes**, SHA-256 `c33b62a18bdbb2ab2cd1af1c2766ec1260de67dffea5dd0f15a8863858fafc0e`. Paquete `com.luixifer.autostudio.director.lab03`, versión `director-0.2.0-lab`. No contiene credenciales.

[Captura real y limpia del editor 450×800](evidence/easy-final-simple-editor.png), [ida y vuelta](evidence/easy-final-roundtrip.json), [recuperación/exportación](evidence/easy-final-recovery.json), [firma](evidence/easy-final-signature.txt), [regresiones completas](evidence/easy-final-tests.txt).

Las 323 pruebas Python siguen pasando, junto a las 22 comprobaciones JVM anteriores y la nueva suite del reparto automático. La captura limpia se ha inspeccionado visualmente: tres entradas principales, miniaturas, controles de orden y botón fijo sin solapamiento en la resolución probada. No se declara validación física en Samsung ni del selector SAF; las entradas automatizadas utilizan URI reales por ContentResolver.
