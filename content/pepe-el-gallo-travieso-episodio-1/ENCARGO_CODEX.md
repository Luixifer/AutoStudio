# AutoStudio Director — Pepe el Gallo Travieso / Episodio 1

**Guion fuente:** `content/pepe-el-gallo-travieso-episodio-1/guion.txt` (13 bloques, íntegro). Preserva texto y orden salvo corrección editorial justificada.

## Encargo ejecutable para Codex
Producir **«El gran rescate de Pío»**, cuento infantil para 2–5 años, ~3 minutos, MP4 1920×1080 30 fps H.264/AAC, narración española dulce y cálida. Reutilizar AutoStudio Director 2 del estado verificado, conservar versiones estables. No inventar pruebas aprobadas.

### Biblia de personajes y continuidad
- Pepe: gallo pequeño y simpático, plumas naranja cálido, gran cresta roja, pico dorado, ojos enormes, cola azul turquesa; personalidad alegre y protectora.
- Pío: pollito amarillo redondo y pequeño, ojos grandes, expresión curiosa, sin accesorios.
- Lola: oveja blanca de aspecto adorable, ojos amables.
- Nube: conejo pequeño gris claro con orejas largas rosadas.
- Escenario recurrente: granja cálida de madera roja, flores, bosque suave, arroyo pequeño, tabla y cuerda. Coherencia de escala, vestuario, dirección espacial y estilo 3D animado de calidad; NO fotorrealismo adulto.
- No sustituir héroes ni cambiar la historia: **Pío queda al otro lado del arroyo; Pepe con Lola y Nube construyen un paso para ayudarle a regresar**. No representar acciones peligrosas como juego a imitar sin acompañamiento de adultos; hacerlo fantástico y seguro.
- Las referencias visuales originales son orientativas, no imágenes individuales listas para edición.

### Producción
1. Analizar el estado real de Director 2; evitar sobrescribir la versión correcta si `main` está desfasada respecto a los builds recientes.
2. Importar guion completo en 13 escenas narrativas, con `scene_id` estables y planificación de **26 subplanos** (~2 por bloque), en orden; ajustar duración visual al audio REAL, no inventar tiempos.
3. Elaborar 26 briefs visuales autónomos de composición y acción antes de generar imágenes. Mantener diseño idéntico de personajes, localizaciones y accesorios con pruebas de continuidad. La duración media debe rondar 5–8 s; si el audio necesita más, insertar subplanos pertinentes sin rellenar con una misma imagen durante 20–30 s.
4. Generar/importar 26 imágenes INDIVIDUALES, o dejar sus recursos marcados como pendientes con instrucciones precisas; no recortar láminas de storyboard como si fueran planos definitivos sin verificar calidad. Verificar que los PNG/JPG están disponibles en el espacio de ejecución.
5. Audio: narradora dulce, expresiva, español de España, ritmo claro para 2–5 años, pronunciación y pausas naturales, sin voz robótica. Si la herramienta gratuita no logra esa calidad, indicar bloqueo y permitir importar voz WAV/MP3.
6. Música: existe una pista original de **185 s** en un paquete preparado fuera de GitHub, no asumir que está presente. Si no se dispone de ella, crear música instrumental propia/compatible de forma verificable, suave y alegre, volumen muy bajo debajo de la voz, con cambios armónicos discretos. NO inventar que se incorporó ese MP3.
7. SFX originales o licenciados: canto de gallo, pío-pío, pasos, vuelo de mariposa discreto, agua, crujido suave de tablas, aplausos/risas suaves, ambiente de granja. Evitar sonidos bruscos o sobresaltos. Mezcla sin clipping, voz siempre inteligible, final con cola musical.
8. Cámara y movimiento: panorámicas/zooms fluidos y moderados, parallax solo cuando existen capas reales; clips IA opcionales legítimos para gestos, saltitos, mariposa, rescate, abrazo; no prometer animación completa usando imágenes fijas. Transiciones discretas, sin flash ni parpadeos intensos.
9. Subtítulos opcionales infantiles legibles, ortografía española, limitados a la locución real. Título/intro breve, outro sin llamadas a compra.
10. Render por escenas con línea temporal y manifiesto explícito `narration_range→visual_asset_id→start/end`. No intercambiar imágenes por orden de importación. Reanudar render y utilizar caché validada si existe.
11. Verificación sobre MP4 final: decodificación, 1920x1080/30fps, duración, sincronización de subtítulos/voz con escenas, orden y hashes visuales de 26 subplanos, bandas negras/deformación, picos de audio, coherencia editorial y escucha real si posible. Declarar explícitamente qué no se comprobó.
12. Entregables: MP4 completo real, proyecto editable portátil, imágenes individuales con nombres, música y narración con licencia/procedencia, informe de QA y APK solo si hay cambios de app. No publicar en YouTube. Sin APIs de pago ni servicios facturables sin permiso.

### Plan de 26 planos (dos por párrafo)
1. Presentar granja luminosa y Pepe en el cercado.
2. Pepe en primer plano mirando curioso.
3. Amanecer y saludo del gallo.
4. Pío corriendo hacia Pepe.
5. Mariposa azul entre flores.
6. Pío siguiéndola hacia bosque.
7. Arroyo y puente viejo a distancia.
8. Pío aislado al otro lado.
9. Pío llamando desde orilla opuesta.
10. Pepe oyendo y echando a correr.
11. Reencuentro visual a distancia, orillas separadas.
12. Pepe pensando con expresividad.
13. Pepe midiendo el salto.
14. Pepe se detiene prudentemente.
15. Pepe descubre madera segura.
16. Pepe encuentra segunda tabla y cuerda.
17. Lola y Nube llegan para ayudar.
18. Los tres instalan paso estable fantástico.
19. Pío da primer pasito.
20. Pío termina de cruzar.
21. Abrazo de los amigos.
22. Lola, Nube y mariposa celebran.
23. Tarde dorada en granja.
24. Pepe y Pío juntos observando horizonte.
25. Pío avisa a Pepe antes de paseo.
26. Plano final de granja, guiño de próxima aventura.

**Advertencia de exactitud:** Este directorio contiene guion y especificación, pero NO contiene las dos láminas PNG de referencia ni el MP3 original del ZIP de 6,1 MB. La conexión disponible con GitHub solo permite enviar texto en esta sesión; no declarar esos medios subidos. Codex puede preparar el sistema y generar recursos nuevos si el entorno lo permite, y debe indicar cualquier falta de medios.
