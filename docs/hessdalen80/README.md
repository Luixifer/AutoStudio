# Hessdalen — incidencia 80

**Estado: capítulo bloqueado por falta de guion definitivo aprobado y recursos audiovisuales.** No se ha producido ni aprobado un documental de Hessdalen. El vídeo técnico anterior de 307,333 s no es ese capítulo.

## Punto de partida preservado

Se recuperó Director 2 en `codex/director-2-scene-integrity`, commit `f55a075`, con motor endurecido `632d423` y APK LAB4 procedente de `41ec018`. Las entregas verificadas se documentan en [incidencia íntegra](ISSUE_80.md) y [validación anterior](../director2/VALIDATION.md). No se partió de `main`, que no contiene necesariamente esa implementación. Trabajo independiente: `codex/hessdalen-issue-80`; no se ha fusionado con `main` ni modificado la APK instalada.

No se encontró el supuesto guion aprobado en la conversación disponible ni en el contenido recuperado del repositorio. Las plantillas anteriores y el vídeo técnico no lo sustituyen. Se solicitó su ubicación o texto y los recursos/licencias concretos. El resultado de consultar todos los comentarios públicos de #80 se conserva en la evidencia de Actions.

## Proyecto listo para completar

- [Plan estructurado](../../content/projects/hessdalen/chapter01.plan.json): 7 bloques, 30 planos, IDs estables. Es un **plan editorial**, deliberadamente distinto de un proyecto renderizable.
- [Guion técnico de planos](SHOT_LIST.md): motivo, clase propuesta, encuadre, movimiento y campos pendientes. No hay rutas ficticias, imágenes inventadas ni licencias supuestas.
- Cada duración de 10 s es un objetivo editorial, no un valor empleado por FFmpeg. Solo el audio definitivo medido podrá confirmar los 285–330 s solicitados.
- Las fechas 1981, 1984 y 1998 son temas del encargo, no afirmaciones aprobadas por este archivo. Consultar fuentes y revisar el contexto antes de grabar la narración.

### Material necesario del usuario

1. Guion definitivo completo con párrafos separados por líneas en blanco, en texto, Markdown o el JSON de Director existente; indicar que es la versión aprobada.
2. Imágenes y clips correspondientes, o sus enlaces descargables; autor/procedencia, permiso o licencia de cada archivo. Si faltan planos se conservarán como pendientes.
3. Audio WAV/MP3 si se quiere una locución humana. En su defecto se conserva Kokoro local, candidato `em_alex`; seleccionar `es-ES`/fonemizador castellano **no demuestra** acento ni interpretación documental aprobados.

No se necesita que el usuario invente tiempos: el motor los obtendrá del audio. Sí se necesita decidir qué recurso corresponde a qué frase. Para material de archivo se exige fuente verificable; una recreación o hipótesis deberá identificarse explícitamente, incluida rotulación en pantalla durante el montaje editorial. Esa revisión y rotulación definitiva están pendientes, no se han resuelto con un booleano automático.

## Implementación incremental

Se ha extendido el contrato `autostudio-director/1` con `scene.subshots`, sin cambiar las narraciones ni las escenas existentes. Los proyectos sin subplanos siguen el renderizador anterior.

```json
{
  "id": "parrafo-01",
  "narration": "Primera frase aprobada. Segunda frase aprobada.",
  "subshots": [
    {
      "id": "plano-01",
      "start_phrase": "Primera frase aprobada.",
      "end_phrase": "Primera frase aprobada.",
      "media": {
        "kind": "image",
        "path": "media/plano-01.jpg",
        "fit": "blur",
        "rights": {"license": "original_user", "credit": "Autor real"}
      },
      "camera": {"movement": "zoom_in"},
      "transition": {"type": "cut", "seconds": 0}
    },
    {
      "id": "plano-02",
      "start_phrase": "Segunda frase aprobada.",
      "end_phrase": "Segunda frase aprobada.",
      "media": {
        "kind": "video",
        "path": "media/plano-02.mp4",
        "rights": {"license": "original_user", "credit": "Autor real"}
      },
      "transition": {"type": "cut", "seconds": 0}
    }
  ]
}
```

El ejemplo explica el formato, **no es narración de Hessdalen ni declara que esos archivos existan**. Las frases deben cubrir íntegramente el párrafo, en orden, sin huecos ni solapamientos. Si se repiten, se requieren frases más específicas o `start_occurrence`/`end_occurrence` explícitos (desde 1). Una unidad acústica como una cifra no puede dividirse entre planos.

Una escena genera una sola locución medida. Cada corte se sitúa dentro de una pausa realmente disponible; la disolución solo se acepta si cabe completa sin invadir las palabras de ninguno de los planos. Se conserva un fotograma de margen antes de la nueva frase. Si no hay pausa suficiente, el render falla con el ID del párrafo: hay que elegir otro final de frase, no acelerar, cortar ni estirar el audio. Máximo 40 subplanos por párrafo.

El renderizador comparte cachés independientes de narración y plano. Cambiar una imagen invalida ese plano y el compuesto afectado, no la locución ni los demás planos. **El compuesto final sí se vuelve a ensamblar y validar**: no se promete modificar un MP4 terminado sin ese trabajo. Las huellas incluyen los medios, la configuración, el código relevante y la versión de FFmpeg.

El transporte opcional puede guardar cachés verificables en borradores privados del mismo proyecto, con límite acumulado de 512 MiB por producción y sin otra API/servicio. Está desactivado si no hay `project_id` válido en el proyecto y la solicitud. La APK LAB4 no emite todavía esa identidad: **no se afirma reutilización entre dos trabajos enviados por esa APK**. Su empaquetado seguro se prueba automáticamente; el ciclo privado de subida/restauración entre trabajos queda pendiente de una integración Android específica.

## Validar y compilar cuando se reciban materiales

```bash
python -m scripts.director.production_plan content/projects/hessdalen/chapter01.plan.json --out reports/hessdalen80/readiness.json
```

Actualmente termina con código **2 esperado**, enumerando el guion, anclajes, medios y permisos ausentes. No acepta un plan incompleto como éxito.

Con el proyecto Director aprobado junto a sus medios, actualizar en el plan `script.path`, su SHA-256, la aprobación y cada plano. Cada `scene_id` debe ser el ID del párrafo original. Se compila junto al proyecto original para conservar las rutas:

```bash
python -m scripts.director.production_plan RUTA/chapter01.plan.json --compile RUTA/DEL/GUION/project-with-shots.json
python -m scripts.director.engine RUTA/DEL/GUION/project-with-shots.json --out reports/hessdalen-chapter01
```

No dividir automáticamente el guion en siete párrafos por coincidir con siete bloques editoriales: los párrafos aprobados se conservan. Los bloques solo organizan los planos.

## Calidad y límites

QA técnico: rangos textuales completos, PCM y tiempos medidos, orden, SHA de recursos, muestras decodificadas de cada subplano, identidad íntegra de subtítulos, correlación de audio, decodificación final y controles existentes de vídeo/audio. Una prueba negativa sustituye un plano y verifica que el MP4 antiguo ya no pasa la comprobación.

QA editorial independiente y pendiente: pertinencia de las imágenes, autenticidad del archivo, formulación científica, derechos efectivos, ritmo, pronunciación de Hessdalen, escucha completa y calidad cinematográfica. La correspondencia automática demuestra el montaje conforme al manifiesto, **no que una imagen represente científicamente el texto**.

La prueba neuronal breve usa ilustraciones originales científicas existentes y texto explícitamente técnico; no es un nuevo capítulo ni se entrega como sustituto de Hessdalen. No hay escucha humana aprobada. No se afirma calidad cinematográfica ni resultados físicos Samsung.

No se ha cambiado Android en esta entrega y por tanto no se genera otra APK. El editor móvil de subplanos por frase y la sustitución de un solo plano desde su interfaz aún no están implementados; el backend acepta el JSON estructurado. Se conserva la APK estable y su editor de párrafos. No presentar el apartado Android de la incidencia como terminado.

Se mantienen los límites de infraestructura [documentados](../director/INFRASTRUCTURE.md): runners estándar públicos, procesos acotados, entradas de 200 MiB y capítulos de hasta diez minutos. No se activan servicios facturables ni publicación en YouTube. Acceso a una web o a un artículo no equivale a autorización de reutilizar sus fotografías.

## Confirmación del usuario

El usuario ha confirmado en esta sesión: «aún no los tengo», en respuesta a la solicitud del guion definitivo y los recursos. El bloqueo de producción es, por tanto, confirmado y no un fallo del renderizador. No se solicita otro enlace ni se redacta un documental de sustitución. El trabajo se retoma cuando esos materiales estén disponibles.
