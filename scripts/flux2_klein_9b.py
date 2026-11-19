"""Alternative FLUX.2 Klein 9B cloud image generator, 1 image per call.

The 9B model uses the same documented multipart request as 4B, but no
fallback to a paid model or an unbounded retry is permitted.
"""
from __future__ import annotations
import base64
import json
import re
import urllib.error
import urllib.request

from scripts.flux2_klein import build_form, WIDTH, HEIGHT
from scripts.image_generation import MAX_BYTES, image_dimensions

MODEL_9B = "@cf/black-forest-labs/flux-2-klein-9b"
ENDPOINT_9B = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/" + MODEL_9B


def generate_klein9b(prompt, account, token, timeout=120):
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account or ""):
        raise ValueError("Invalid Cloudflare account ID")
    if not token or len(token) > 4096:
        raise ValueError("Missing/invalid Cloudflare token")
    body, mime = build_form(prompt)
    request = urllib.request.Request(
        ENDPOINT_9B.format(account=account), method="POST", data=body,
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": mime})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            if resp.status != 200:
                raise RuntimeError("FLUX.2 Klein 9B non-200 response")
            raw = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("FLUX.2 Klein 9B HTTP " + str(exc.code)) from None
    if len(raw) > MAX_BYTES:
        raise ValueError("FLUX.2 Klein 9B response too large")
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("FLUX.2 Klein 9B returned malformed JSON") from None
    data = parsed.get("result") if isinstance(parsed, dict) and parsed.get("success") is True else None
    encoded = data.get("image") if isinstance(data, dict) else None
    if not isinstance(encoded, str):
        raise ValueError("FLUX.2 Klein 9B did not return a valid image")
    try:
        pixels = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        raise ValueError("Invalid FLUX.2 Klein 9B image base64") from None
    w, h, _ = image_dimensions(pixels)
    if (w, h) != (WIDTH, HEIGHT):
        raise ValueError("FLUX.2 Klein 9B produced unexpected dimensions")
    return pixels
