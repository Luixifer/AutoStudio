"""FLUX.2 Klein 4B via Cloudflare Workers AI multipart REST API.

Uses the existing account/token. One API call per requested image and no paid
third-party API. Never authorizes publication or stores credentials.
Official: https://developers.cloudflare.com/workers-ai/models/flux-2-klein-4b/
"""
from __future__ import annotations
import base64
import json
import re
import urllib.error
import urllib.request
import uuid

from scripts.image_generation import MAX_BYTES, MAX_PROMPT, image_dimensions

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/" + MODEL
WIDTH = 1536
HEIGHT = 864


def build_form(prompt, width=WIDTH, height=HEIGHT, boundary=None):
    if not isinstance(prompt, str) or not 20 <= len(prompt) <= MAX_PROMPT:
        raise ValueError("FLUX.2 Klein requires bounded non-empty prompt")
    if (not isinstance(width, int) or not isinstance(height, int) or
        not 256 <= width <= 1920 or not 256 <= height <= 1920 or
        width * height > WIDTH * HEIGHT):
        raise ValueError("Requested image dimensions outside pilot budget")
    boundary = boundary or uuid.uuid4().hex
    if not re.fullmatch(r"[a-zA-Z0-9]{8,64}", boundary):
        raise ValueError("Invalid multipart boundary")
    fields = {"prompt": prompt, "width": str(width), "height": str(height)}
    body = b"".join(
        ("--" + boundary + "\r\n"
         "Content-Disposition: form-data; name=\"" + field + "\"\r\n\r\n"
         + value + "\r\n").encode("utf-8")
        for field, value in fields.items()
    ) + ("--" + boundary + "--\r\n").encode("ascii")
    return body, "multipart/form-data; boundary=" + boundary


def generate_klein(prompt, account, token, *, timeout=115):
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account or ""):
        raise ValueError("Invalid Cloudflare account ID")
    if not token or len(token) > 4096:
        raise ValueError("Cloudflare API token is required")
    body, content_type = build_form(prompt)
    req = urllib.request.Request(
        ENDPOINT.format(account=account), data=body, method="POST",
        headers={"Authorization":"Bearer " + token, "Content-Type":content_type}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError("FLUX.2 Klein returned non-200")
            payload = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("FLUX.2 Klein HTTP " + str(exc.code)) from None
    if len(payload) > MAX_BYTES:
        raise ValueError("FLUX.2 Klein response exceeds maximum size")
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeError):
        raise ValueError("FLUX.2 Klein returned invalid JSON") from None
    if not isinstance(data, dict) or data.get("success") is not True:
        raise RuntimeError("FLUX.2 Klein did not confirm success")
    result = data.get("result")
    encoded = result.get("image") if isinstance(result, dict) else None
    if not isinstance(encoded, str):
        raise ValueError("FLUX.2 Klein response lacks base64 image")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception:
        raise ValueError("FLUX.2 Klein returned invalid base64") from None
    width, height, _ = image_dimensions(raw)
    if (width, height) != (WIDTH, HEIGHT):
        raise ValueError(f"FLUX.2 Klein unexpected dimensions: {width}x{height}")
    return raw
