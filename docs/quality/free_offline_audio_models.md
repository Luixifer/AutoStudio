# AutoStudio — IA de audio gratuita y local

**Estado:** dos motores nuevos instalables desde GitHub Actions, ejecución real con voz española verificada (19-11-2026). No requiere claves de inferencia ni API comercial.

## Qué hay instalado

- `faster-whisper==1.2.1`: transcripción independiente en español mediante Whisper multilingüe `tiny`, CTranslate2, CPU/int8, con tiempos de palabras. Licencia del software MIT. El tamaño `base` queda disponible opcionalmente para pruebas de mayor calidad. El modelo se descarga en el runner durante el primer uso.
- `silero-vad[onnx-cpu]==6.2.3`: detección independiente de voz/silencio mediante ONNX y CPU. Licencia MIT. No necesita usar PyTorch para la inferencia ONNX.
- `kokoro-onnx`: **ya estaba instalado**, no se reinstala. Hemos añadido selección opcional de voces españolas `em_alex` y `em_santa`, manteniendo `ef_dora` como voz predeterminada para no modificar la producción existente sin comparar muestras.

## Prueba real

GitHub Actions [44590953775](https://github.com/Luixifer/AutoStudio/actions/runs/44590953775) instaló los motores en Ubuntu, generó una muestra WAV en español mediante eSpeak NG local y ejecutó ambas IA sin conexión a API de pago.

- Texto previsto: «Hola. Este es un ejemplo de voz para probar el sistema.»
- Whisper recuperó «Este es un ejemplo de voz para probar el sistema.» Omitió la primera palabra.
- Coincidencia de palabras: **95,24 %**, solo sobre esta muestra sintética.
- Silero encontró intervalos aproximados de voz `0,0–0,4 s` y `0,7–3,9 s`.
- Salidas: WAV, `informe.json` y registro de ejecución. Artefacto: `AutoStudio-Whisper-Silero-Speech-QA`.
- Ajuste posterior: el umbral se endureció a **98 %** para que una omisión como la del «Hola» active revisión, en lugar de marcar prematuramente que el audio está listo.

## Uso cuando tengamos voz definitiva

```bash
python -m pip install -r requirements-audio-qa.txt
python -m scripts.audio_ai_qa \
  --audio /ruta/al/render/narration.wav \
  --expected "Texto exacto del guion narrado" \
  --out /ruta/al/render/audio-qa.json \
  --model tiny
```

Para evaluar todas las escenas de un Short, habría que pasar sus audios y narraciones reales; no aceptar únicamente la transcripción del MP4 mezclado con música.

El reporte establece `review_needed` según texto y silencios, y siempre deja `voice_quality_approved=false`, `scientific_facts_verified=false`, `ready_to_publish=false` y `youtube_enabled=false`. El resultado de un ASR ligero no sustituye una escucha humana ni garantiza la naturalidad del acento.

## Restricciones

- El entorno GitHub Actions es temporal; estas dependencias **quedan declaradas en el repositorio** y se instalan cuando se ejecuta el trabajo correspondiente. No se instalan en el teléfono ni quedan perpetuamente encendidas.
- El flujo de producción principal sigue usando sus dependencias previas. Este QA es opcional hasta validar su rendimiento con la voz neuronal real.
- Chatterbox Multilingual, Wan, LTX o modelos GPU exigentes no se instalan en runners estándar de GitHub: podrían requerir equipos de pago.
- No activar publicación automática ni planes de pago.

## Referencias

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/snakers4/silero-vad
- https://github.com/thewh1teagle/kokoro-onnx
