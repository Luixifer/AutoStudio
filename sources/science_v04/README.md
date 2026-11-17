# Maestros científicos originales — AutoStudio 0.4

Tres archivos Blender 4.3.2 editables, con ocho escenas/cámaras por tema: auroras, biología molecular y volcanes. Se generan en CPU mediante `scripts/create_science_art.py`; ninguna malla, textura o imagen se descarga de terceros. Resolución nativa de cada render: 864×1536, montaje a 720×1280 con margen para cámara sin ampliar por encima de la imagen fuente.

```sh
blender -b -t 4 --python scripts/create_science_art.py -- "$PWD"
blender -b -t 4 --python scripts/project_science_motion.py -- "$PWD"
```

El segundo paso proyecta trayectorias realmente dibujadas en Blender para las animaciones ligeras. No calcula una simulación física. En las escenas de la Tierra, se ocultan destellos que quedarían detrás/dentro de la esfera, evitando representar partículas atravesando el planeta.

Los modelos son ilustraciones conceptuales: continentes procedurales, campos magnéticos esquemáticos, hélices sin secuencia genómica medida, células/ribosomas simplificados y magma/cenizas sin simulación de fluidos. El render mantiene grano residual y formas estilizadas. No se presentan como imágenes reales o acabado cinematográfico final. Véase `assets/science_v04/LICENSE_ART.md` para procedencia y derechos.
