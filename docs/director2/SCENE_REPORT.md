# Comprobación del capítulo técnico

Ejecutado realmente en GitHub Actions, run **44921968829**, código `09e90e0`. Cinco párrafos distintos, cinco ilustraciones originales distintas, voz Álex local CPU y cama ambiental original provisional. **No es el capítulo de Hessdalen ni material proporcionado por el usuario.**

| Escena | Voz medida | Inicio de voz | Final de voz | Error visual máximo | Correlación PCM | Resultado |
|---|---:|---:|---:|---:|---:|---|
| paragraph-1 | 63.001 s | 0.000 s | 63.001 s | 0.000823 | 1.000000 | Aprobado |
| paragraph-2 | 61.855 s | 63.967 s | 125.821 s | 0.001591 | 0.993178 | Aprobado |
| paragraph-3 | 59.540 s | 126.767 s | 186.307 s | 0.000857 | 0.993523 | Aprobado |
| paragraph-4 | 58.827 s | 187.267 s | 246.094 s | 0.000817 | 0.993087 | Aprobado |
| paragraph-5 | 59.783 s | 247.033 s | 306.816 s | 0.000915 | 0.993146 | Aprobado |

Los instantes proceden del PCM y de los fotogramas medidos. Se comparan cinco fotogramas por escena con su render de origen, excluyendo las zonas de texto. El error es la diferencia RGB media normalizada; límite 0,055. La correlación se calcula sobre la narración PCM antes de mezclar música; mínimo 0,95. Estas métricas no equivalen a aprobación artística ni a una escucha humana.

[Informe JSON por escena](evidence/five-scene-correspondence.json).
