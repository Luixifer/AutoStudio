# AutoStudio · Documento maestro de implementación audiovisual

## Objetivo y regla de seguridad

Convertir el storyboard `requests/51cc3cfcdfef933be83eb3d4bb739472/storyboard.json` en un **teaser real, reproducible y revisable**, manteniendo `ready_to_publish=false`, sin publicación automática ni confundir simulación artística con evidencia científica. La arquitectura debe poder reutilizarse para próximos documentales.

## Motor híbrido de cuatro módulos

1. **Motor orbital procedural (primero)**: 1280×720, 24 fps, MP4 H.264, 5 segundos; estrella amarilla-blanca y distinguible de planeta gaseoso azul. Órbita proyectada con movimiento continuo y profundidad. Recurso didáctico *no a escala*, no metraje de observación; sin relojes, líneas ni promesas de velocidad orbital inferida a partir del vídeo.
2. **Motor molecular (segundo)**: H₂ → H + H y H + H → H₂ con objetos/animaciones modelados explícitamente. No electrones arrancados, rayos ni ionización inventada. Deberá producir MP4 sin recurrir a imágenes IA para la física.
3. **Director híbrido (tercero)**: asigna ilustraciones generativas a escenas artísticas y animaciones por código a procesos y relaciones científicas. Debe registrar el tipo de fuente y derechos de cada plano y rechazar sustituciones no aprobadas.
4. **Montador (cuarto)**: usa el motor de vídeo/voz existente para composición, audio y subtítulos con control verificable de sincronía, decodificación y legibilidad. La muestra puede usar audio de prueba, pero NO debe presentarse como voz Álex hasta generar y validar la muestra real.

## Entregables auditables

- Código de render y tests en `scripts/procedural_orbit.py` y `tests/test_procedural_orbit.py`.
- Prueba GitHub Actions aislada que emite `orbit-preview.mp4`, primera imagen y manifiesto con SHA-256.
- Prueba de continuidad: sin saltos de posición, geometría de estrella y planeta distintas, fotogramas con cambios reales.
- Siguiente etapa: motor H₂ con prueba doble de disociación/recombinación.
- Siguiente etapa: teaser narrado y montaje; solo después revisión editorial y publicación manual.

## Limitaciones aceptadas

El render orbital es una **ilustración conceptual, no simulación gravitacional ni escala astronómica real**. El ciclo mostrado no demuestra por sí solo el periodo real de 36 horas; la narración y las fuentes de NASA aportan ese dato. Un test de software positivo no equivale a aprobación cinematográfica. Se registrarán errores y se conservarán resultados reproducibles.
