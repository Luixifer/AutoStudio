# KELT-9b — guía científica y editorial para AutoStudio

**Estado:** revisión documental externa para el piloto. No acredita la precisión de las imágenes generadas ni sustituye una revisión final de cada plano. **NO PUBLICAR automáticamente.**

**Guion fuente:** `requests/51cc3cfcdfef933be83eb3d4bb739472/storyboard.json`

**Fuentes prioritarias:** NASA, NASA/JPL, artículos científicos revisados y centros de investigación astronómica. Comprobadas el 19-11-2026.

## Hechos respaldados y representación por escena

| Escena | Afirmación narrada | Evaluación y fuente | Visualización propuesta (interpretación artística, no imagen observada) |
|---|---|---|---|
| 1 | Un planeta puede ser más caliente que la superficie de algunas estrellas. | Respaldado por NASA: su hemisferio diurno alcanza unos 4.300 °C, más que la superficie de algunas estrellas [1]. | Composición espacial de un planeta muy caliente próximo a su estrella, sin científicos hablando ni gráficos. |
| 2 | KELT-9b es un mundo gaseoso gigante. | NASA lo clasifica como gigante gaseoso [2]. | Silueta completa del planeta y capas atmosféricas, con la estrella en contexto. |
| 3 | La cara iluminada ronda los 4.300 °C. | Cifra aproximada publicada por NASA [1]. Es la temperatura diurna, **no una superficie sólida**. | Contraste visual entre el hemisferio iluminado intensamente y la atmósfera restante. Evitar representar lava, suelo o un número flotante. |
| 4 | Radiación intensa de una estrella muy cercana. | NASA describe su proximidad extrema y la alta irradiación [1], [3]. | Interacción luz-estrella-atmósfera a escala planetaria. No inventar chorros, llamaradas o impactos observados. |
| 5 | No hay un suelo de lava; es un gigante gaseoso. | Coherente con su clasificación como gigante gaseoso [2]. «No hay un suelo de lava» es una exclusión, **no una invitación a dibujar lava**. | Profundidad de nubes y gas sin terreno firme, sin superficie rocosa. |
| 6 | El calor puede separar moléculas de hidrógeno. | NASA informa de modelos de **disociación molecular** diurna [3]. | Visualización a escala molecular de H₂ separándose en dos átomos. No confundir disociación con ionización ni representar electrones arrancados. |
| 7 | En el lado nocturno pueden reformarse moléculas de hidrógeno. | NASA y estudios de curvas de fase sustentan disociación/recombinación [3], [4]. Es interpretación/modelado respaldado por observaciones, no una película directa de los átomos. | Reconstrucción molecular de átomos reuniéndose en H₂ en un entorno gaseoso oscuro. |
| 8 | El año de KELT-9b dura aproximadamente 36 horas. | Confirmado por NASA [1], [2]. | Vista orbital distinta: planeta recorriendo un arco cercano a su estrella. Una imagen fija no demuestra la duración; usar montaje/narración para comunicar la comparación con la Tierra. |
| 9 | La atmósfera está extendida y parte del gas podría escapar. | Observaciones espectroscópicas muestran una envoltura de hidrógeno extendida; la fuga atmosférica se considera probable [5], [6]. Evitar presentar una tasa exacta como hecho absoluto. | Gas tenue extendido desde el límite atmosférico, representado como visualización artística, sin sugerir una fotografía real del escape. |
| 10 | Es uno de los mundos más extremos conocidos; pregunta al espectador. | Cierre retórico coherente con las mediciones previas [1], [3]. No introduce nuevos fenómenos comprobados. | Plano heroico final, a gran escala, con KELT-9b y su estrella. **No inventar ionización, electrones expulsados, galaxias o terreno.** |

## Reglas de control antes de usar FLUX

1. El sujeto y el evento de cada descripción visual deben corresponder **a esa escena**, no solo al tema general del documental.
2. No repetir el mismo protagonista, escala y efecto físico de manera indistinguible en escenas consecutivas.
3. Las reacciones moleculares de las escenas 6 y 7 son representaciones ilustrativas de modelos físicos, no observaciones directas de átomos individuales.
4. Escenas 3–5: KELT-9b es gaseoso; no introducir corteza, volcanes, mares de lava ni suelo.
5. La escena 8 necesita resolver el concepto de 36 horas mediante narración y progresión de planos; no fingir que una sola foto muestra una órbita completa.
6. La escena 9 exige lenguaje cauteloso: «indicios», «probablemente», «puede escapar».
7. La escena 10 no debe añadir procesos científicos nuevos ausentes del guion.
8. Un JSON correcto o un PASS del revisor IA no constituyen por sí solos aprobación editorial, científica ni autorización para publicar.

## Fuentes verificables

[1] NASA, «NASA’s TESS Delivers New Insights Into an Ultrahot World»: https://www.nasa.gov/universe/nasas-tess-delivers-new-insights-into-an-ultrahot-world/

[2] NASA Science, «KELT-9 b» (catálogo de exoplanetas): https://science.nasa.gov/exoplanet-catalog/kelt-9-b/

[3] NASA/JPL, «For Hottest Planet, a Major Meltdown, Study Shows»: https://www.nasa.gov/centers-and-facilities/jpl/for-hottest-planet-a-major-meltdown-study-shows/

[4] A&A, «The stable climate of KELT-9b» (2022): https://doi.org/10.1051/0004-6361/202243823

[5] Nature Astronomy, «An extended hydrogen envelope of the extremely hot giant exoplanet KELT-9b» (2018): https://www.nature.com/articles/s41550-018-0503-3

[6] Max Planck Institute for Astronomy, «KELT-9b»: https://www.mpia.de/news/science/2018-07-kelt-9b

**Nota:** este archivo reúne evidencia y criterios de producción. Los campos automáticos `scientific_facts_verified` y `ready_to_publish` permanecen en `false` hasta que el conjunto final de imágenes, voz, edición y fuentes sea auditado.
