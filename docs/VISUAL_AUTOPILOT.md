# AutoStudio: dirección y supervisión visual por IA (experimental)

Diseñado para trabajar con **cualquier narración de 1-24 escenas**, no contiene un prompt fijo de KELT-9b.

## Qué hace

- **Preproducción global**: Antes de llamar a FLUX, Llama propone una secuencia entera de planos con escala, ángulo, propósito narrativo, sujeto y acción visible; el plan exige combinaciones cinematográficas diferentes. Si es inválido, se corrige como máximo una vez con texto y, si sigue fallando, no se crea ninguna imagen. Esto no valida científicamente cada plano.\n- **Director**: Llama a `@cf/meta/llama-3.1-8b-instruct-fp8` para interpretar el texto de cada escena y crear una descripción visual inédita. No necesita que escribas diez prompts manuales.
- **Generador**: Crea imágenes con FLUX.1 Schnell.
- **Supervisor**: Envía la imagen *real* a `@cf/google/gemma-4-26b-a4b-it` para contrastar lo que es visible con la narración y la dirección. Exige `DECISION: PASS`, con observación visible; de otro modo la marca `needs_human_review`.
- **Reintento**: Opcionalmente repite la escena, como máximo una vez, incorporando a las instrucciones el motivo del rechazo visual.
- **Diversidad visual entre escenas**: Compara las observaciones visuales reales de cada imagen con las escenas previamente aprobadas. Puede rechazar una composición repetida incluso si Gemma devolvió PASS. Solo solicita otro intento si el presupuesto explícito permite generar una imagen más. No equivale a una validación científica ni detecta todos los duplicados visuales.
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
- Se verificó la inspección real de una imagen de KELT-9b con Gemma 4 (resultado PASS), pero todavía no se ha validado una producción completa con la nueva supervisión. El modelo puede fallar y la revisión editorial sigue siendo obligatoria.

## Resultados y limitaciones del primer ensayo de diez escenas

El primer ensayo de KELT-9b generó diez imágenes, ocho aprobadas individualmente por Gemma y dos ambiguas. Reutilizando todas las imágenes, se alcanzaron nueve aprobaciones, pero Gemma rechazó la escena 1 por una posible marca de agua. GitHub completó una vista previa de diagnóstico, no publicable. La revisión visual humana detectó repetición excesiva de remolinos en las imágenes, demostrando que una evaluación individual PASS no es suficiente para construir un documental variado. La nueva comprobación de diversidad es conservadora, requiere pruebas con nuevas escenas y todavía no se ha validado con otro ciclo completo de generación.

## Prueba de preproducción solo con texto (19/11/2026)

La primera prueba real produjo diez combinaciones de escala, cámara y propósito diferentes usando una llamada textual a Cloudflare, sin nuevas imágenes. Sin embargo, varias acciones propuestas fueron demasiado vagas (p. ej., «Gas composition» y «Orbital period»). Se ha endurecido la validación para exigir descripciones de acciones físicas visibles de 6 a 22 palabras y una corrección textual acotada. Aún es necesaria otra prueba real de esta validación mejorada. Los planes no demuestran que las imágenes finales tengan variedad ni precisión científica.
