# Image-level visual duplicate QA

`scripts/image_duplicate_qa.py` performs **zero AI API calls**. It uses Pillow (already required) to calculate an 8×9 difference hash per visual and compare scene pairs. Exact-byte duplicates are flagged immediately; very similar perceptual hashes are flagged for further review, while low-contrast images are marked UNSURE rather than receiving a misleading comparison.

```sh
python -m unittest discover -s tests -p test_image_duplicate_qa.py -v
python -m scripts.image_duplicate_qa scene01.png scene02.webp --out output/image-duplicate-audit.json
```

This is an **independent extra check**, not a replacement for `visual_distinctness.py` (which compares model-observed descriptions), Gemma, Scout or human scientific/artistic review. Perceptual hashes do not reliably detect two similarly composed but newly generated paintings or two near-identical celestial systems with different color/texture. They can also produce false positives with repeated geometries. Never automatically approve images based on a large hash distance. Production wiring requires a separate evaluated integration change. The report hardcodes `ready_to_publish=false`.
