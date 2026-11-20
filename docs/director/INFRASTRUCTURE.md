# Infraestructura gratuita: límites y decisiones

Consultado el 20-11-2026 en el código fuente oficial de documentación de GitHub, porque docs.github.com estaba bloqueado por la política de red del entorno. No se cambió esa política.

- [Límites de Actions](https://github.com/github/docs/blob/main/content/actions/reference/limits.md): un job alojado en GitHub tiene un máximo de **seis horas**; los límites de concurrencia dependen del plan. Director limita su job a **180 minutos** y la evaluación a 45.
- [Facturación](https://github.com/github/docs/blob/main/content/billing/concepts/product-billing/github-actions.md): no confundir computación gratuita en repositorios públicos con todos los tipos de almacenamiento o runners. Solo se usan runners **estándar `ubuntu-24.04`**, repositorio público, sin GPU, runners grandes, servicios IA ni suscripción nueva. El workflow rechaza repositorios privados; no cambia presupuestos ni facturación.
- [GitHub Releases](https://github.com/github/docs/blob/main/content/repositories/releasing-projects-on-github/about-releases.md): los adjuntos no están en Git; la documentación no fija límite total de tamaño ni ancho de banda para una Release, pero sí por archivo. Director impone entrada **200 MiB** y resultado **menos de 2 GiB**. Esto no es una promesa de disponibilidad o uso ilimitado.
- No se añade `actions/cache` ni se depende de almacenamiento de Artifacts para Director. Los informes y MP4 se adjuntan a un borrador; los ensayos técnicos públicos se entregan en una prerelease identificada. No se guardan vídeos grandes indefinidamente en Git.
- Los drafts y archivos se mantienen hasta su revisión; se documenta su limpieza manual. Antes de escalar deben automatizarse la retención y el listado del espacio ocupado, con protecciones que no borren originales.

## Capítulos y 60 minutos

El motor admite seleccionar un capítulo con `--chapter ID`, valida capítulos de hasta diez minutos y un total máximo de 60. Divide el trabajo en escenas reutilizables por SHA. Si un proyecto supera 200 MiB de entrada o el tiempo del runner, no se intentará un servicio de pago: habrá que enviar capítulos separados y añadir ensamblaje remoto verificado. Ese reparto automático **no está terminado**.

Un MP4 de una hora puede ocupar cientos de MB o varios GB según complejidad y CRF. No se garantiza que cualquier combinación de 60 minutos, 1080p/60 y clips externos quepa en estos presupuestos. Aún faltan mediciones de ese extremo.

## Voz y licencias

Se reutiliza Kokoro ONNX CPU, motor MIT/modelo Kokoro 82M Apache-2.0 según procedencia existente y pesos SHA fijados (`assets/voice-models.json`, `THIRD_PARTY.md`). Álex y Santa son opciones masculinas españolas del paquete; no se certifican acento ni naturalidad. Whisper/faster-whisper son alternativas locales gratuitas para tiempos de audio aportado. No se clona la voz de una persona ni se activa inferencia externa.

FFmpeg y libx264 tienen condiciones de distribución/licencia que deben revisarse al distribuir binarios; aquí se ejecutan en el runner, no se empaquetan en el teléfono. El usuario debe conservar derechos y atribuciones de imagen, vídeo, música y voz. «Aportado por el usuario» no significa «sin derechos de autor».
