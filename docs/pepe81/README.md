# Pepe el Gallo Travieso · El gran rescate de Pío · episodio 1

Producción a partir de la [incidencia 81](https://github.com/Luixifer/AutoStudio/issues/81), el encargo y los trece párrafos originales incorporados desde `origin/main`. Rama independiente `codex/pepe-episode-81`, basada en Director 2 verificado y la revisión móvil `6f5d3e6`. No se cambia la APK, su conexión, sus proyectos ni el motor funcional de Director 2. No se publica en YouTube.

## Contenido realmente producido

- Cuatro personajes originales modelados en Blender: Pepe naranja con cresta roja y cola turquesa, Pío amarillo sin accesorios, Lola de lana blanca y Nube gris con orejas rosadas. Una sola biblioteca geométrica y de materiales para todos los planos, sin regenerar caras por imagen.
- Un escenario 3D original compartido: granja roja, cobertizo, flores, árboles, arroyo somero, puente antiguo cerrado y nuevo paso de dos tablas con apoyos y barandillas. Pío queda a la derecha y regresa a la izquierda; no se muestra un salto sobre el agua.
- **26 ilustraciones individuales nativas 1920×1080**, renderizadas con Cycles CPU y limpiadas con Open Image Denoise. El último plano tiene una nota visual para las familias: «Cerca del agua, siempre con una persona adulta». No modifica la locución ni los trece párrafos originales.
- **84 fotogramas originales de animación 3D** del cruce de Pío, renderizados como escenas completas en Actions, a 1280×720 y 12 fps. Se ajusta el movimiento a la palabra «orilla», sin alterar la voz; FFmpeg interpola la presentación a 30 fps. No se presenta esta secuencia como animación nativa 1080p/30. Los demás planos son ilustraciones 3D con movimiento de cámara, no animación corporal completa.
- Narración neuronal femenina Dora, fonemizador castellano `es`, solicitada `es-ES`, síntesis nativa a velocidad 0,76 y pausas suaves. Cada párrafo tiene un WAV real y límites fonéticos medidos. La primera lectura a unas 153 palabras/min se sustituyó por una más pausada; la duración de montaje medida es aproximadamente **203,53 s**, sin estirar voz ni añadir relleno para llegar a 185 s.
- Música instrumental original de síntesis, «El paso de Pío»: timbres de campana, flauta suave y bajo, con fundidos y volumen reducido bajo la voz. Efectos originales sintetizados de gallo, pollito, pasos, mariposa, agua, madera y celebración. No son grabaciones reales de animales ni risas humanas.
- Los trece párrafos y su orden se conservan íntegros. Cada uno tiene dos subplanos con anclajes textuales explícitos; sus duraciones se resuelven sobre el audio real. Se exporta SRT; no se incrustan bloques de narración sobre las imágenes por defecto.

**No estaban disponibles las dos láminas PNG ni el MP3 original de 185 s del ZIP.** No se afirma haberlos utilizado. Todo el arte y la música de esta entrega son producciones nuevas, no recortes de aquellas referencias.

## Versiones y fuentes

- Ilustraciones y maestro corregido: Blender **4.3.2**, CPU, 16/32 muestras según plano; los PNG originales ruidosos se conservan en el espacio de producción. OIDN limpia el ruido a resolución nativa, sin reescalar los PNG.
- Cruce: Blender **4.0.2** del repositorio oficial Ubuntu 24.04, CPU, 12 muestras. [Ejecución real 45052820336](https://github.com/Luixifer/AutoStudio/actions/runs/45052820336). Se descargaron las cuatro partes de animación, se verificaron CRC y todos sus SHA-256 y se usaron sus 84 fotogramas completos. Los personajes proceden del mismo generador geométrico; no son diseños distintos.
- Open Image Denoise **2.3.3**, CPU: [fuente oficial](https://github.com/RenderKit/oidn/releases/tag/v2.3.3), Apache-2.0. Archivo Linux descargado: SHA-256 `3c385230d9e6f63527ba72f2229594dbac5051674219d72e0044b5d0b841796f`. No se cambia la resolución ni se inventa detalle de alta resolución.
- Kokoro 82M/ONNX y voces: fuentes, licencias y SHA fijados en `assets/voice-models.json`; inferencia local CPU, sin API de pago. La voz neuronal, su acento efectivo, pronunciación y naturalidad **no están aprobados por una escucha humana**.
- Materiales, mallas, música y foley originales de `scripts/pepe/`. Tipografía DejaVu Sans libre del sistema. No se usan modelos de pago, canciones comerciales ni imágenes ajenas.

## Correcciones reales durante la revisión

Se detectó que Nube quedaba oculto detrás de Pepe y de la barandilla: se reubicó a la izquierda y se renderizaron de nuevo P17, P18 y P22. El control de hashes detectó que P08 y P09 eran idénticos: se creó una cámara cercana distinta para la llamada de Pío y se volvió a renderizar P09. No se solucionó cambiando unos píxeles ni rebajando el detector de duplicados.

Se ensayaron pases 3D transparentes y recortes de render para abaratar la animación. Una prueba inicial reveló que las claves de visibilidad podían restaurar a Pío en el fondo; se corrigió la evaluación de visibilidad y se verificó la transparencia real. **El montaje entregado utiliza los fotogramas completos de Blender de Actions**, no esos ensayos ni un personaje plano desplazado.

## Proyecto editable

El paquete preparado incluye `project.json`, los 26 PNG, el clip 3D, los trece WAV, la música y SFX, los tiempos de palabra, los hashes, el maestro de escenas corregido y el maestro de animación del cruce. Incluye fuentes Python y configuración de modelos para reproducirlo con herramientas libres. Los fotogramas brutos de la animación se conservan además en las entregas de arte de Actions, con sus hashes.

**La APK actual no es un editor de subplanos de este episodio**: no se debe importar este ZIP en la APK esperando editar los 26 planos y generar el mismo montaje. El paquete funciona con el motor de esta rama y su workflow de producción. El MP4 se puede descargar y reproducir sin modificar la APK ni configurar otro token. No se ha generado una APK nueva.

Para cambiar una locución hay que realinear sus palabras, recalcular las duraciones y remontar. No reemplazar un WAV conservando timestamps antiguos. Para cambiar arte, renderizar la nueva revisión y actualizar sus hashes; Director reutiliza lo que no ha cambiado.

## Repetir el montaje de los recursos preparados

El workflow `.github/workflows/pepe81-episode.yml` verifica el paquete de entrada, ejecuta las regresiones, extrae únicamente datos sin ejecutar Python del ZIP, renderiza con Director 2, valida el MP4 real y publica los archivos en una versión preliminar de GitHub Releases. Usa solo un runner público estándar, con tiempo acotado, sin activar servicios facturables. No promete renderizado gratuito ilimitado.

Desde un entorno con Python/FFmpeg y las dependencias de `requirements-director.txt`:

```bash
python -m scripts.director.engine RUTA/project.json --out reports/pepe-render
python -m scripts.pepe.verify --input RUTA --render reports/pepe-render --out reports/pepe-render/episode-quality.json
```

La ruta debe contener el proyecto extraído y su carpeta `media`. El guion original del repositorio se utiliza para la validación independiente. El paquete de entrada versionado conserva los recursos de este episodio; el MP4 completo se entrega en Releases, no como un vídeo grande añadido al historial de código.

## Alcance de la validación

Además de las regresiones, se comprueba el MP4 real: decodificación completa, H.264/AAC, 1920×1080/30 fps, duración medida, orden y hashes de los 26 recursos activos, identidad textual del SRT, intervalos sin negros y ausencia de clipping digital. La verificación independiente compara el **AAC decodificado del MP4 final** con la narración original de cada párrafo; no se limita al WAV seco de montaje.

El informe de Blender registra geometría/materiales compartidos, estados de visibilidad, cámaras, orillas y aparición del nuevo paso. Se revisan imágenes de grupo y fotogramas del cruce. La hoja de contacto final se extrae del MP4 real.

Pendiente: escucha humana completa, prueba con familias/niños, prueba física en Samsung y aprobación artística. La animación corporal completa de los 26 planos, lip-sync y expresiones faciales más ricas no están implementadas. Esta entrega no acredita calidad comercial definitiva solo por pasar controles técnicos.
