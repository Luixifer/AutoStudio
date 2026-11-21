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
