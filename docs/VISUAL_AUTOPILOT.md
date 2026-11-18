# AutoStudio: dirección y supervisión visual por IA (experimental)

Diseñado para trabajar con **cualquier narración de 1-24 escenas**, no contiene un prompt fijo de KELT-9b.

## Qué hace

- **Director**: Llama a `@cf/meta/llama-3.1-8b-instruct-fp8` para interpretar el texto de cada escena y crear una descripción visual inédita. No necesita que escribas diez prompts manuales.
- **Generador**: Crea imágenes con FLUX.1 Schnell.
- **Supervisor**: Envía la imagen *real* a `@cf/moondream/moondream3.1-9B-A2B` para contrastar lo que es visible con la narración y la dirección. Exige `DECISION: PASS`, con observación visible; de otro modo la marca `needs_human_review`.
- **Reintento**: Opcionalmente repite la escena, como máximo una vez, incorporando a las instrucciones el motivo del rechazo visual.
- **Validación de integridad**: SHA256 y dimensiones, rechazo de recursos ausentes o duplicados, y adaptador que solo puede seleccionar escenas aprobadas.
- **Salida**: Si se aprueban todas, crea un nuevo storyboard, narración Álex y MP4 a 60 fps. Si alguna no pasa, conserva los ficheros y su informe para revisión; **no crea un vídeo marcado como aprobado**.

Esta evaluación visual automática **NO es una prueba científica**, no verifica afirmaciones del guion con fuentes externas y el evaluador puede equivocarse. Sigue estando prohibida la publicación automática. La revisión humana del documental final es necesaria antes de publicarlo.

## Cuota y seguridad

El modo predeterminado simula sin red. La ejecución real es manual con `live=true`, usando `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` ya almacenados como GitHub Secrets. Hay como máximo 10-20 llamadas de generación para el ejemplo de diez escenas, además de las llamadas al director y supervisor; cada una consume neuronas. El presupuesto de la aplicación solo **limita número de llamadas**, no mide consumo de neuronas. Mantén Workers Free y verifica el uso diario antes de ejecutarlo; si la cuota se agota, Cloudflare debería bloquear nuevas inferencias sin facturar.

[Workflow de prueba](../.github/workflows/supervised-kelt-video.yml).

```sh
python -m unittest tests.test_visual_autopilot -v
python -m scripts.visual_autopilot --story storyboard.json --out output/supervised
```

Para un video diferente solo debe cambiar el storyboard. El workflow actual está fijado al archivo KELT-9b únicamente como **caso de ensayo**: no se ha integrado todavía un selector de guiones libres desde la APK.

## Límites

- No es un motor de búsqueda científica ni una comprobación de verdades externas.
- La identidad visual se intenta preservar con el contexto textual anterior; no hay condicionamiento visual entre imágenes ni referencia img2img.
- Un `PASS` del modelo de visión significa **aprobación tentativa automática**, no calidad perfecta ni autorización editorial.
- La compatibilidad real de los dos nuevos modelos de IA todavía debe verificarse con una ejecución live, sus cuotas y políticas.
