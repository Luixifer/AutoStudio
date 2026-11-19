# AutoStudio — FLUX.2 Klein 4B vs 9B, inspección independiente

**Fecha:** 19 noviembre 2026. **Documento de evidencia real de una prueba**, no aprobación cinematográfica ni científica. Publicación automática: **NO**.

## Experimento real

- GitHub Actions: [44588237962](https://github.com/Luixifer/AutoStudio/actions/runs/44588237962). Resultado: success.
- Material: la **misma escena 8** de KELT-9b, la misma instrucción de imagen, el mismo formato 1536×864.
- Imagen 4B: recuperada del artefacto histórico [44548159087](https://github.com/Luixifer/AutoStudio/actions/runs/44548159087), con SHA-256 verificado.
- Imagen 9B: una única solicitud nueva a Workers AI.
- Evaluadores: Gemma 4 multimodal y Llama 4 Scout multimodal, ambos inspeccionando los píxeles reales.
- Artefacto de los resultados y las imágenes: `AutoStudio-FLUX9-Scout-vs-Gemma-Real-Comparison`.
- No se generaron vídeos ni se publicaron resultados en YouTube.

| Modelo | Veredicto Gemma | Veredicto Scout | Valoración independiente |
| --- | --- | --- | --- |
| FLUX.2 Klein 4B | PASS: dice ver una estrella y un planeta | FAIL: ve dos cuerpos planetarios y ninguna estrella clara | Rechazado |
| FLUX.2 Klein 9B | PASS: dice ver un planeta iluminado por su estrella | FAIL: ve un solo planeta, sin una estrella reconocible | Rechazado |

## Inspección directa de la comparativa

En 4B hay dos cuerpos esféricos con texturas de planeta, uno muy brillante. En 9B aparece un único planeta gaseoso grande, con un resplandor blanco intenso detrás; **no se distingue claramente la estrella como objeto separado**. El modelo 9B mejora la atmósfera y textura del planeta, pero no soluciona la relación visual principal de la órbita narrada.

Un `PASS` de Gemma no acredita fidelidad física: aquí fue contradicho por Scout y por la revisión visual directa. El control automático completo debe quedar `FAIL` si cualquiera de los dos encuentra un error. Si ambos dan PASS, el resultado sigue siendo `AUTOMATED_PASS_ONLY`, nunca `ready_to_publish=true`.

## Cambios permanentes añadidos en GitHub

- `scripts/flux2_klein_9b.py`: proveedor 9B por REST multipart de Cloudflare.
- `scripts/vision_scout.py`: inspector independiente con criterios distintos para órbita/estrella y disociación H₂; fallos y respuestas dudosas bloquean.
- `scripts/compare_visual_models.py`: una solicitud nueva como máximo, traza de procedencia y auditoría paralela.
- `scripts/cinematic_pilot.py`: proveedor 9B seleccionable y **dos revisiones por imagen** por defecto para las ejecuciones reales.
- Pruebas offline del control y de la selección de proveedor.

La ejecución real se hizo antes del cambio final de integración en el piloto; después se aprobaron **21 pruebas offline** en [44589431837](https://github.com/Luixifer/AutoStudio/actions/runs/44589431837). La comparación en sí ha sido verificada con imágenes reales; la integración final del piloto está verificada con pruebas de código, y necesitaría una ejecución visual posterior para validar ese punto extremo a extremo.

## Siguiente decisión

**No producir los diez planos solo con IA de imágenes.** Combinar imágenes generativas como recursos estéticos y animaciones deterministas para órbitas y H₂. Para futuras imágenes astronómicas, exigir una estrella de aspecto claramente estelar separada del planeta; ambos inspectores deben verificar objetos observables y el control editorial final permanece independiente.

**Costes:** se limitaron nuevas imágenes a una por ejecución de comparación. Workers AI concede asignación gratuita diaria, pero la posibilidad de cargos si la cuenta tiene plan Paid y supera los límites debe consultarse en su dashboard. Revisar también términos de uso del modelo 9B antes de explotar contenido comercial.

**Fuentes de modelos:** [Llama Scout en Cloudflare](https://developers.cloudflare.com/workers-ai/models/llama-4-scout-17b-16e-instruct/), [FLUX.2 Klein 9B](https://developers.cloudflare.com/workers-ai/models/flux-2-klein-9b/), [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/).
