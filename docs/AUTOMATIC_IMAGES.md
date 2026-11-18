# AutoStudio — imágenes generadas automáticamente (fase experimental)

Esta rama introduce una **ruta optativa**, separada del render y APK existentes. No sustituye imágenes existentes, no publica contenido y no afirma que la calidad visual esté aprobada.

## Uso seguro

```bash
python -m unittest tests.test_image_generation -v
python -m scripts.image_generation --story ruta/al/storyboard.json --out output/generated-images
```

El storyboard JSON debe contener `scenes`, cada una con `image_prompt`, `visual_prompt`, `prompt`, `visual_brief` o `description` explícito. Si la dirección visual usa otro formato, se necesita un adaptador validado. El modo predeterminado **no llama a la red** y produce únicamente un manifiesto de planificación.

Para una prueba real, configurar `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` como secretos de GitHub Actions o variables de entorno locales, nunca en archivos versionados, y ejecutar:

```bash
python -m scripts.image_generation --story storyboard.json --out output/generated-images --live --variants 1 --max-requests 10
```

Cloudflare Workers AI: modelo `@cf/black-forest-labs/flux-1-schnell`. Confirmar la disponibilidad, licencia y cuota vigente antes de usarlo en producción. No se solicita servicio de pago automáticamente. El límite de solicitudes es por ejecución, no un medidor de neuronas o de facturación de Cloudflare. Evitar activar pagos automáticos en la cuenta. Las imágenes se almacenan como PNG con SHA-256 y dimensiones; el manifiesto permite auditoría y reanudación manual, pero **no hay selección visual automática validada** ni conexión con el renderizador en esta fase.

### Pendiente antes de activar en la APK
- Adaptar el JSON real del director visual de KELT-9b y comprobar su contrato.
- Validar una imagen real con Cloudflare; verificar dimensiones, licencia y contenido.
- Añadir controles visuales genuinos (no confundir nitidez con fidelidad científica).
- Integrar las imágenes aprobadas al render y comprobar un trabajo completo de la APK.
- Verificar cuotas y consentimiento antes de consumir llamadas reales.

**Nunca se deben incluir tokens, imágenes privadas o respuestas de API con credenciales en commits o registros.**
