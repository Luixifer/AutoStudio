# AutoStudio Personal LAB 0.7: guion e imágenes propias

## Qué permite
- Desde Android: título, 2–12 párrafos de narración y 2–12 imágenes ordenadas.
- Casilla obligatoria de autorización explícita para subir imágenes y guion al repositorio PÚBLICO Luixifer/AutoStudio.
- JPEG comprimido sin metadatos EXIF, SHA-256, bloqueos de duplicados y límites de tamaño.
- Workflow que recibe solo un ID y verifica el guion y las imágenes antes del render.
- Álex Kokoro neural, zoom/panorámica, subtítulos, MP4 y reportes de calidad.
- Copia privada del vídeo final en el teléfono, reproductor nativo y exportación a Descargas.
- Paquete Android independiente de la APK 0.6.

## Riesgo de privacidad importante
Los archivos subidos a GitHub son PÚBLICOS y pueden permanecer en el historial incluso tras ser borrados. No se deben subir fotografías privadas, documentos personales, imágenes familiares ni material sin derechos. El usuario debe dar su consentimiento por cada producción.

## Credencial GitHub
- Fine-grained PAT restringido al repositorio AutoStudio, Actions: lectura y escritura, Contents: lectura y escritura.
- El usuario debe actualizar voluntariamente el permiso Contents. La credencial se cifra usando Android Keystore; no se debe compartir en el chat.

## Cómo probar
1. Instalar AutoStudio Personal LAB 0.7 desde el artefacto de Actions.
2. Conectar GitHub en Ajustes con permisos adecuados.
3. Abrir Crear Short con mi guion y mis imágenes.
4. Escribir título y guion, una escena por línea.
5. Seleccionar y ordenar tantas imágenes como párrafos.
6. Autorizar el envío público solo para imágenes que pueden compartirse.
7. Generar, seguir el trabajo y reproducirlo desde la biblioteca.

## Lo que aún no hace
- No crea imágenes cinematográficas desde una frase; el usuario aporta imágenes y guion.
- No comprueba la exactitud científica de las afirmaciones ni certifica licencias aportadas por el usuario.
- No publica en YouTube.
- No existe todavía una validación de extremo a extremo en Samsung físico 0.7.
- Si se interrumpe una subida, pueden quedar imágenes públicas parciales en GitHub. No se ejecuta el vídeo sin manifiesto completo.

## Componentes
- Android: CustomVideoActivity, PersonalUploadClient, CatalogVideoClient, GitHubClient, PlayerActivity.
- Workflow principal: .github/workflows/personal-custom.yml.
- Motor fijado por commit: scripts/personal_custom_request.py, personal_prepare.py, personal_editor.py, personal_quality.py y personal_visual_audit.py.
- Pruebas: test_personal_custom_request.py y custom-video-smoke.yml.
