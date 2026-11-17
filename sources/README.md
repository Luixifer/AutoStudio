# Fuentes artísticas originales

`ocean_environment_v02.blend`: escena original editable de Blender 4.3.2. Cámaras, terreno, rocas, chimeneas y organismos ilustrativos, materiales procedurales, luces virtuales y volúmenes. No incluye imágenes externas. El script `scripts/create_cinematic_assets.py` reconstruye esta escena y genera también la ilustración microscópica.

Imágenes finales: `assets/cinematic/`; manifiesto con resolución, hashes y procedencia. El generador llama a `scripts/finish_assets.py` para aplicar reducción de ruido espacial con FFmpeg; los originales sin filtro quedan en `output/` (no versionados). No son grabaciones científicas, fotorrealismo aprobado ni una simulación física de vida submarina.
