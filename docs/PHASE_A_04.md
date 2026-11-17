# AutoStudio 0.4 — Fase A de la issue #1

Alcance: tres temas fuera del océano, contenido audiovisual diferenciado, catálogo honesto, pruebas y generaciones reales en Actions. No implementa cola, documentales o generación sobre temas arbitrarios.

## Contenido producido

| Tema | Desarrollo | Recursos |
| --- | --- | --- |
| Auroras polares | Viento solar, interacción magnética, colisiones atmosféricas, emisión y colores | Ocho renders originales: paisaje, Sol/Tierra, campo, excitación, emisión, colores, óvalos y plano final |
| ADN y lectura de instrucciones | Doble hélice, copia, mensajes temporales, ribosomas y expresión diferencial | Ocho renders originales: célula, hélice, copia, mensaje, proteína, regulación, señales y plano final |
| Volcanes: magma y lava | Manto principalmente sólido, fusión parcial, presión/gases, erupción, lava y viscosidad | Ocho renders originales: paisaje, sólido, fusión, burbujas, erupción, lava, comparación y plano final |

Cada tema tiene un guion redactado propio. Las ilustraciones no son reetiquetados del océano ni comparten archivos entre sí. Hay tres maestros editables y 24 JPEG originales, con manifiestos, SHA-256, procedencia, crédito y derechos del proyecto. No se usan imágenes de Internet ni modelos comerciales.

Las fuentes NASA, NOAA, NHGRI y USGS se consultan desde un runner de GitHub. `research/source-check-20261117.json` conserva respuestas HTTP, títulos, hashes y extractos. Una página secundaria BGS inicialmente devolvió 404 y se descartó; la comprobación se conserva en el historial de la rama `science-sources`. Las referencias activas del guion apuntan a páginas recuperadas. Recuperar una página no acredita automáticamente todas las interpretaciones: el texto y los gráficos siguen pendientes de revisión editorial humana.

## Integración incremental

Se conservan Kokoro, tiempos de fonemas, subtítulos de tres palabras, FFmpeg, normalización, decodificación completa, audio, UUID/run ID y SHA-256. El renderizador acepta manifiestos específicos por historia; su opción predeterminada sigue siendo el océano 0.2. El proveedor rechaza temas ambiguos o no publicados, en vez de elegir otro vídeo.

Las nuevas animaciones son pequeñas estelas/glints sobre trayectorias proyectadas desde las escenas 3D, encuadres y transiciones. El ambiente sonoro se distingue por tema y se sintetiza localmente; no se descarga música. Los recursos y el audio anteriores no se sustituyen.

## Android y conservación de 0.3

La revisión 0.4 usa el paquete independiente `com.luixifer.autostudio.lab04`, nombre «AutoStudio Control LAB 0.4», para convivir con la 0.3 ya probada físicamente por el usuario. No lee, borra ni migra sus preferencias, credenciales o MP4. Necesitará su propia autorización de GitHub, cifrada con Keystore; ningún secreto se compila dentro del APK.

El selector se construye a partir de una copia del catálogo publicada dentro del APK: océano y tres temas nuevos. No hay entrada que prometa tema libre. La prueba instrumental selecciona auroras, exige que el resultado real confirme ese tema y conserva las pruebas de recuperación. La instalación 0.3 y sus enlaces fijados permanecen disponibles en `android/VALIDATION.md`.

## Aceptación y límites

Las regresiones incluyen las 57 anteriores y nuevas comprobaciones de guiones diferentes, medios sin reutilizar, diferencia perceptual de imágenes, fuentes recuperadas, créditos, ausencia de fallback, subtítulos y recursos ausentes.

`review-phase-a.yml` es un ensayo fijo de aceptación: lanza tres trabajos reales de `produce-short.yml`, uno por tema, espera sus conclusiones, descarga cada MP4 y verifica voz/imagen/plan/hash. Es una secuencia de pruebas, no la cola móvil prometida para la Fase C. Los resultados reales se añadirán tras completar y comprobar las ejecuciones; el código preparado no se considera una generación exitosa.

Los renders son esquemáticos y estilizados, con ruido residual, iluminación de estudio e imperfecciones geométricas. No hay fotorrealismo, simulación científica de fluidos o estructuras medidas ni aprobación de calidad cinematográfica. La revisión auditiva y artística de los MP4 corresponde a la evaluación posterior.

El coste adicional previsto sigue siendo 0 €: herramientas locales libres y runners públicos estándar, sin APIs de inferencia, GPU, cron o Artifacts. Las cuotas, disponibilidad y límites de GitHub no equivalen a producción gratuita ilimitada. YouTube y ChatGPT siguen desactivados.
