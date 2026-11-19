# AutoStudio — auditoría real del primer piloto visual de KELT-9b

**Fecha:** 19 de noviembre de 2026  
**Estado:** tres escenas probadas con dos generadores, imágenes reales, **cero aprobaciones editoriales**. Las decisiones de Gemma no constituyen aprobación humana ni verificación científica. El canal YouTube sigue sin publicar.

## Evidencia reproducible en GitHub Actions

| Ensayo | Ejecución | Imágenes generadas | QA Gemma | Estado |
|---|---|---:|---|---|
| FLUX.1 Schnell, 1024×1024 | [44545992307](https://github.com/Luixifer/AutoStudio/actions/runs/44545992307) | 3/3 | 1 FAIL, 6 FAIL, 8 UNSURE | **No apto** |
| FLUX.2 Klein 4B, 1536×864 | [44547221810](https://github.com/Luixifer/AutoStudio/actions/runs/44547221810) | 2/3 | 1 PASS, 6 PASS; escena 8 HTTP 400 | **No apto** |
| FLUX.2 Klein 4B, órbita con instrucción concisa | [44548159087](https://github.com/Luixifer/AutoStudio/actions/runs/44548159087) | 1/1 | 8 PASS | **No apto editorialmente** |

Los artefactos de esas ejecuciones contienen JPEG reales, SHA-256, resoluciones, textos de entrada y manifest de control; son retenciones temporales de GitHub Actions.

## Hallazgos editoriales observados en las imágenes

- **Escena 1, planeta y estrella:** FLUX.1 tiende a superficie impactada/rocosa; FLUX.2 ofrece aspecto panorámico y atractivo, pero una paleta de colores fantasiosa y la estrella anfitriona no queda claramente representada.
- **Escena 6, disociación de H₂:** FLUX.1 produjo terreno/lava y esferas planetarias; FLUX.2 produjo dos esferas luminosas conectadas mediante arcos energéticos y otros elementos, sin mostrar de manera inequívoca el mecanismo de H₂ separándose en dos átomos neutros. Un PASS del detector multimodal no demuestra corrección molecular.
- **Escena 8, órbita de 36 horas:** FLUX.1 generó anillos con aspecto diagramático; la versión FLUX.2 de instrucción corta colocó dos cuerpos esféricos azulados superpuestos, ambos con apariencia planetaria. El cuerpo que debería ser una estrella no aparece claramente como estrella. **Gemma dio PASS a pesar de ese fallo visible.**
- **Formato:** FLUX.1 generó 1024×1024; FLUX.2 Klein permitió 1536×864. No confundir cambio de resolución con fidelidad científica.

## Diagnóstico y decisiones de ingeniería

1. **La integración real funciona.** AutoStudio creó imágenes por Cloudflare usando los secretos existentes; entregó artefactos de revisión.
2. **El límite de peticiones se respetó.** Tres solicitudes FLUX.1; tres intentos FLUX.2 en el lote (dos resultados); y una solicitud posterior aislada para la órbita.
3. **FLUX.2 Klein 4B es experimental y no pasa a proveedor definitivo.** Promete mejor encuadre, pero no garantiza representar fenómenos espaciales o moleculares.
4. **Gemma puede dar falsos PASS.** Su evaluación debe tratarse como *una señal*, nunca como autorización editorial o de publicación.
5. **Los modelos generativos de imágenes pueden confundir una estrella con un planeta.** La calidad del resultado se juzga por lo que realmente aparece, no solo por cumplir palabras del prompt.
6. **Para H₂ hace falta una visualización física controlada**, por ejemplo, una animación procedimental con dos átomos neutrales, enlace y separación. Representar cargas eléctricas o electrones arrancados sin respaldo es incorrecto.
7. **La última petición larga para escena 8 produjo HTTP 400**; una instrucción compacta sí funcionó. No se ha demostrado la causa exacta del 400 (no atribuirlo automáticamente a longitud, moderación ni cuota).

## Condiciones para continuar la producción

- Conservar siempre `human_visual_approved=false`, `scientific_facts_verified=false` y `ready_to_publish=false` hasta tener material realmente aprobado.
- Usar referencias astronómicas fiables y un modelo de imagen adecuado; preferir un enfoque híbrido de animaciones científicas controladas para procesos moleculares.
- Añadir una prueba de identificación de estrella y planeta, y otra para procesos moleculares, pero no confiar únicamente en un veredicto automático.
- Evaluar un nuevo conjunto pequeño antes de producir las diez imágenes, narrar y montar el documental final.
- No descargar ni subir manualmente archivos durante cada prueba: los artefactos y reportes quedan accesibles directamente desde GitHub Actions.

### Documentación técnica externa

- [Cloudflare: FLUX.2 Klein 4B](https://developers.cloudflare.com/workers-ai/models/flux-2-klein-4b/)
- [Cloudflare: FLUX.2 Klein multipart y parámetros](https://developers.cloudflare.com/changelog/post/2026-01-15-flux-2-klein-4b-workers-ai/)
- [Cloudflare: límites gratuitos y precios](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Guía científica del piloto](./kelt9b_science_brief.md)

**Resumen:** Tenemos generación y evaluación automática demostradas, pero ningún candidato alcanza todavía la aprobación editorial profesional. No se ha creado ni publicado un vídeo final con estos candidatos.
