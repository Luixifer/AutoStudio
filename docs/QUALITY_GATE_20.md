# AutoStudio Personal · Quality Gate 20
**Estado:** rama de laboratorio. No sustituye la APK física 0.5 ni publica en YouTube.

## Veinte mejoras implementadas
1. Rama aislada que conserva el circuito Samsung → GitHub → MP4.
2. Perfil Short vertical 720×1280 / 25 fps.
3. Perfil documental horizontal 1280×720 / 25 fps.
4. Objetivos de duración recomendados: 35–55 s y 8–12 min.
5. Duraciones máximas y mínimas de seguridad diferentes de objetivos editoriales.
6. Esquema de entrada de guion + imágenes (schema 3).
7. Preparación automática de pistas de voz y manifest de render (schema 2).
8. Voz neuronal Álex em_alex exigida, sin cambio silencioso de voz.
9. Comprobación WAV PCM mono con frecuencia compatible.
10. Duración real y tiempos de palabras obtenidos del sintetizador.
11. Archivo SRT de subtítulos reutilizable.
12. Subtítulos ASS integrados e independientes del zoom.
13. Cámara: zoom in/out, pan left/right, focus y static.
14. Punto de interés [x,y] seguro y zoom máximo limitado.
15. Imágenes verticales a pantalla completa; horizontales con fondo adaptado.
16. Licencias y créditos declarados; referencias externas HTTPS obligatorias.
17. Rechazo de duplicados visuales/audio y rutas fuera del proyecto.
18. Control de calidad técnico: decodificación, codecs, duración, pista de voz, silencios y subtítulos.
19. Paquete manual de YouTube: título, descripción, fuentes, capítulos y miniatura de revisión.
20. CI de vídeo real: ocho escenas originales de auroras, voz neuronal Álex y QA medible.

## Cómo funciona
El usuario aporta el título, el guion dividido en escenas y las imágenes correspondientes.
El editor ejecuta preparación de voz Álex, tiempos por palabra, movimientos de cámara, subtítulos, codificación y verificación.
Comando de preparación y render:

    python -m scripts.personal_prepare proyecto/storyboard.json --out salida --render

Comando de exportación editorial:

    python -m scripts.personal_youtube_pack salida/input/studio-ready.json salida/render/quality-report.json --out salida/publicacion

Los formatos de entrada y el proceso se comprueban mediante pruebas automatizadas y un Short de ejemplo.

## Límites importantes
- Este bloque NO genera todavía guiones o imágenes desde una pregunta libre: requiere texto e imágenes apropiadas.
- Las pruebas técnicas no certifican la exactitud científica, derechos de autor, naturalidad humana ni atractivo artístico.
- El documental horizontal está soportado por esquema y motor de encuadre; no se ha validado un render real completo de 8–12 minutos.
- El vídeo no se sube automáticamente y nunca se marca como listo para publicar sin revisión.
- La APK instalada no cambia. Integrar schema 3 en el móvil requiere una futura versión específica.
- Los vídeos de laboratorio no deben presentarse como filmaciones científicas auténticas.

## Revisión conjunta siguiente
Comparar Short de auroras antes y después de corregir el recorte de títulos. Después probar un nuevo conjunto de diez imágenes aportadas por el usuario, antes de integrar esta rama en Android.
