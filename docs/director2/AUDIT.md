# Director 2 — auditoría y corrección de correspondencia

Base conservada: `2ec4e4d`, rama `codex/autostudio-director`. Desarrollo aislado: `codex/director-2-scene-integrity`. No se fusiona main, no se borra una versión anterior y no se publica en YouTube.

## Fallos localizados

1. **Importador sencillo 0.2:** `DirectorQuickPlan.split` agrupaba por unas cien palabras y por cantidad de imágenes, buscando finales de frase. `imageFor` distribuía imágenes proporcionalmente. El resultado no respetaba los párrafos y podía mantener un recurso durante varias escenas. Era un error del diseño introducido en el modo sencillo, no una obligación del usuario de editar después el montaje.
2. **Transiciones:** el motor añadía un margen visual a la escena anterior y comenzaba la disolución cuando arrancaba la siguiente locución. Durante ese intervalo podía verse todavía la imagen anterior. En el modo estricto la escena siguiente tiene un silencio inicial igual a la transición, más un fotograma de seguridad; la voz empieza con su recurso ya plenamente visible.
3. **Subtítulos:** el agrupador heredado usaba tres palabras por cue. Director 2 utiliza puntuación, longitud y frases, manteniendo texto y tiempos medidos dentro de cada escena. El estilo dinámico se elige expresamente.
4. **Voz en párrafos largos:** Kokoro puede unir lotes internos sin conservar ciertos separadores de sus tokens temporales. Se encontró una discrepancia real de 174 frente a 176 palabras. Se sintetiza por frases internas acotadas y se unen sus PCM usando cantidades exactas de muestras. Esto no divide la escena ni cambia la imagen. Si una marca no es comprobable se rechaza; no se asignan tiempos por caracteres.
5. **QA largo:** el lector de audio reutilizado tenía un límite de 180 s. El primer MP4 largo existía, pero su auditoría fallaba al leer la narración completa. Se creó un decodificador acotado para 600 s por escena y 3600 s de audio unido, conservando el límite histórico del lector antiguo. El MP4 existente se pudo verificar independientemente sin regenerarlo ni cambiar el estado de la ejecución original fallida.

## Componentes conservados

Python/FFmpeg, el transporte oficial GitHub, voces Kokoro verificadas por SHA, alineación local de WAV/MP3, importación que conserva bytes, AtomicFile, Android Keystore, firma debug, VideoView/MediaStore, mezcla con ducking/loudnorm/limiter, capítulos portátiles y todas las pruebas previas. No hay otro motor de vídeo ni API comercial.

El nuevo discriminador `scene_policy: paragraph/1` distingue la política estricta del formato heredado. El esquema base `autostudio-director/1` permanece legible. La rama anterior continúa disponible para recuperación; su modo antiguo no se convierte silenciosamente en escenas aprobadas.

## Asociación como fuente de verdad

`chapters[].scenes[]` guarda el ID estable, el párrafo y su `media`. Después de importar el guion, la interfaz edita ese registro. Mover una escena mueve el objeto completo. Añadir recursos en bloque solo llena posiciones sin recurso; no desplaza ni reemplaza asociaciones ya aprobadas. Los recursos repetidos por SHA se rechazan por defecto; el contrato permite `media.allow_reuse: true` solo como autorización explícita.

Un guion reemplazado requiere confirmación y deja las escenas nuevas pendientes de recursos. No se intenta adivinar cuáles de las imágenes antiguas encajan. Se conserva una instantánea JSON privada anterior y no se borran los originales importados. Para conservar un proyecto entero se utiliza su ZIP; un JSON de guion no puede abrir rutas de archivos externos del teléfono.

## Alcance de las pruebas visuales

La auditoría decodifica fotogramas al principio, un cuarto, mitad, tres cuartos y final de cada narración y los compara con su render de escena vinculado al hash del recurso. La región de comparación excluye títulos y subtítulos. Verifica también texto de cues, límites, hash de origen y correlación de la narración unida con cada audio original. La prueba negativa renderiza realmente un vídeo con dos imágenes intercambiadas y exige que falle al comprobarlo contra el manifiesto original.

Esto prueba correspondencia técnica con el manifiesto, no que una foto represente históricamente el contenido del texto. Tampoco equivale a escuchar cada palabra o aprobar la naturalidad de la voz. La selección y orden editorial de imágenes siguen perteneciendo al usuario.


## Reutilización de capítulos

Se detectó y cerró otra vía de asociación obsoleta: una huella calculada solo sobre el JSON no detectaba que los bytes de una imagen hubieran cambiado conservando su nombre. Las nuevas identidades portátiles incluyen hashes de archivos, código de render y versión de FFmpeg. Empaquetar vuelve a comprobar las claves de las escenas renderizadas; un resultado previo a un cambio se rechaza. Los planes y partes se generan con una cadena de herramientas consistente; un cambio de renderizador exige rehacer las partes afectadas. No se borra el material anterior.
