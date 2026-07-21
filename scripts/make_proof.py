"""Compose the Alibaba Cloud deployment proof image — docs/devpost/proof_deployment.png.

  python -m scripts.make_proof

Real captures from the public URL (live studio + /healthz JSON) plus the
self-attested ECS identity, in the same dark launch system.
"""
import json
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

from scripts.make_gallery import (BG, PANEL, BORDER, INK, MUTE, DIM, PINK,
                                  sans, tracked, glow_card)

W, H = 2400, 1600
SRC = Path("docs/devpost/source")
OUT = Path("docs/devpost")
MENLO = "/System/Library/Fonts/Menlo.ttc"


def mono(size):
    from PIL import ImageFont
    return ImageFont.truetype(MENLO, size)


def main():
    healthz = json.loads(urllib.request.urlopen(
        "http://8.130.166.96/healthz", timeout=20).read())
    cloud = healthz["cloud"]

    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    m = 110
    tracked(d, (m, 84), "AI SHOWRUNNER — PROOF OF ALIBABA CLOUD DEPLOYMENT", sans(26), PINK, 7)
    d.text((m, 140), "Running live on Alibaba Cloud ECS", font=sans(76, 1), fill=INK)
    d.text((m, 250), "The backend serves the public internet from ECS and attests its own "
                     "instance identity via the on-instance metadata service.",
           font=sans(31), fill=MUTE)

    # left: live studio capture
    img = Image.open(SRC / "live_studio.png").convert("RGB").crop((0, 0, 3600, 1290))
    r = 1450 / img.width
    img = img.resize((1450, round(img.height * r)), Image.LANCZOS)
    glow_card(c, img, m, 380)
    tracked(d, (m, 380 + img.height + 26), "HTTP://8.130.166.96/  —  THE LIVE STUDIO, "
            "FOUR PRODUCTIONS SERVED FROM ECS", sans(21), MUTE, 4)

    # right: healthz terminal panel
    px, py, pw, ph = 1620, 380, 672, 560
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=16, fill=PANEL,
                        outline=BORDER, width=2)
    for i, col in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([px + 26 + i * 34, py + 24, px + 44 + i * 34, py + 42], fill=col)
    d.text((px + 130, py + 22), "GET /healthz", font=mono(24), fill=MUTE)
    y = py + 84
    d.text((px + 28, y), "$ curl http://8.130.166.96/healthz", font=mono(23), fill=MUTE)
    y += 56
    lines = [
        ('"ok"', "true", (56, 211, 159)),
        ('"auth"', "true", (56, 211, 159)),
        ('"cloud": {', "", None),
        ('  "provider"', f'"{cloud["provider"]}"', PINK),
        ('  "instance-id"', f'"{cloud["instance-id"]}"', PINK),
        ('  "region-id"', f'"{cloud["region-id"]}"', PINK),
        ('  "zone-id"', f'"{cloud["zone-id"]}"', PINK),
        ("}", "", None),
    ]
    for k, v, col in lines:
        d.text((px + 28, y), k, font=mono(22), fill=INK)
        if v:
            kw = d.textlength(k + ": ", font=mono(22))
            d.text((px + 28, y), k + ":", font=mono(22), fill=INK)
            d.text((px + 28 + kw, y), v, font=mono(22), fill=col or MUTE)
        y += 46

    # fact chips under the terminal
    facts = [("ECS INSTANCE", cloud["instance-id"]),
             ("REGION", cloud["region-id"] + " · " + cloud["zone-id"]),
             ("GENERATION", "Qwen3.7-Max · Qwen-VL · Wan2.7 via DashScope")]
    fy = py + ph + 46
    for label, val in facts:
        tracked(d, (px, fy), label, sans(19, 10), PINK, 4)
        d.text((px, fy + 32), val, font=sans(27), fill=INK)
        fy += 100

    d.line([m, H - 84, W - m, H - 84], fill=(30, 34, 46), width=1)
    tracked(d, (m, H - 64), "CODE EVIDENCE: GITHUB.COM/YANJIN-AI/SHOWRUNNER — "
            "SHOWRUNNER/CLIENTS/__INIT__.PY (ALIBABA CLOUD SERVICE MAP)", sans(20), DIM, 4)

    out = OUT / "proof_deployment.png"
    c.save(out)
    print("saved:", out)


if __name__ == "__main__":
    main()
