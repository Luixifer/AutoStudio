# AutoStudio — generación automática de imágenes de KELT-9b

Esta implementación añade el recorrido completo de **dirección visual → imágenes nuevas → storyboard → narración Álex → MP4 a 60 FPS**, en un workflow separado del sistema estable.

## Prueba realizada sin gasto ni credenciales

[Workflow de KELT-9b](../.github/workflows/kelt-image-pipeline.yml) genera las instrucciones de las 10 escenas a partir del guion real mediante el motor editorial congelado y produce un manifiesto auditable. La prueba de Pull Request ejecuta el recorrido **sin imágenes externas**. No afirmamos haber comprobado aún una inferencia real de Cloudflare.

[Generador](../scripts/image_generation.py) · [Adaptador de storyboard](../scripts/image_staging.py) · [Pruebas unitarias](../tests/test_image_generation.py) · [Pruebas de integración](../tests/test_image_staging.py)

## Producción real optativa

El workflow acepta `live=true` **solo por ejecución manual**, no automáticamente al modificar código. Se requieren dos secretos de Actions: `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN`, con permisos restringidos a Workers AI. **No pegues estas credenciales en un chat ni en archivos del repositorio.** Utiliza una cuenta Cloudflare Workers **Free**, sin actualización a modalidad de pago ni facturación activada, y revisa cuotas actuales de Cloudflare.

1. En GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Añade los dos secretos.
2. Abre **Actions → AutoStudio · KELT-9b imagenes a documental (experimental) → Run workflow**, selecciona la rama que contiene el código y activa **live**.
3. El trabajo generará 10 imágenes nuevas (una por escena) usando `@cf/black-forest-labs/flux-1-schnell`, guardará sus SHA-256 y verificará que todas existen.
4. Construirá un storyboard separado, obligatoriamente **no aprobado editorialmente** y YouTube desactivado; el motor fijado de AutoStudio narrará con Álex y tratará de crear el MP4.
5. Si alguna imagen falla, falta, se repite, o si el montaje/QA no pasa, el trabajo se declara fallido; no se presenta un resultado anterior como nuevo. El ZIP de resultados dura tres días.

**Límite técnico:** 10 peticiones como máximo en esta ejecución; esto **no sustituye** verificar el consumo de neuronas ni asegura que Cloudflare nunca facture si el usuario activa un plan de pago. En Workers Free, la cuota se agota y el servicio bloquea inferencias en vez de cobrar, según las condiciones vigentes. Verifica estas condiciones en la consola antes de activar.

## Revisión de calidad

El sistema comprueba el contrato de escena, cantidad, rutas, integridad SHA-256, cabecera/dimensiones PNG y QA del vídeo resultante. El motor audiovisual valida la decodificación de las imágenes al preparar el vídeo.

**No hay todavía una IA que inspeccione la fidelidad científica ni garantice composición extraordinaria**: la primera variante válida se utiliza para montaje, no se etiqueta como 'mejor' sin evaluación. El resultado es una **vista previa para revisión humana**, no publicación directa. Imágenes de referencia científica y la interpretación artística deben distinguirse.

La arquitectura deja disponible la sustitución futura del proveedor, las regeneraciones por escena y el control visual semántico. Estos son objetivos posteriores, no funcionalidades implementadas.

## Probar desde Python sin claves

```bash
python -m unittest tests.test_image_generation tests.test_image_staging -v
python -m scripts.image_generation --story visual-input/direccion-visual.json --out output/generated-images
```

El generador usa el campo `image_prompt` producido por la dirección visual real de AutoStudio; rechaza escenas sin descripción. La modalidad predeterminada produce **solo** JSON, no solicita red y no crea imágenes ficticias.

## Protección de la aplicación existente

No modifica el flujo de producción vigente de la APK ni incorpora credenciales en Android. Trabaja con el storyboard original de KELT-9b de la carpeta `requests/`, manteniendo sus imágenes antiguas sin tocar. La integración con el botón de generar imágenes de la APK aún requiere otra versión de interfaz y una validación física en el Samsung.
