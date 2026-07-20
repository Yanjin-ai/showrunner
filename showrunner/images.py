"""Compressed data-URI helper. Uploading full-res PNGs (i2v reference frames, critic frames)
as base64 saturates the uplink and causes write timeouts under parallel load. Downscaling +
JPEG shrinks the payload ~10x, which fixes the timeouts and speeds every call up."""
import base64
import io
from pathlib import Path
from PIL import Image


def to_datauri(path, max_w: int = 768, quality: int = 85) -> str:
    img = Image.open(path).convert("RGB")
    if img.width > max_w:
        h = round(img.height * max_w / img.width)
        img = img.resize((max_w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/jpeg;base64," + b64
