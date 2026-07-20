"""Submission architecture diagram — docs/devpost/architecture.png (+ .pdf).

  python -m scripts.make_architecture

Frontend ↔ Alibaba Cloud ECS backend (+ file store) ↔ Qwen Cloud (DashScope),
in the same dark launch system as the gallery. 2400x1600, well under 35 MB.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

from scripts.make_gallery import (BG, PANEL, BORDER, INK, MUTE, DIM, PINK,
                                  sans, tracked)

W, H = 2400, 1600
OUT = Path("docs/devpost")


def node(d, x, y, w, h, title, lines=(), accent=False, tsize=34):
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=PANEL,
                        outline=PINK if accent else BORDER, width=3 if accent else 2)
    d.text((x + 28, y + 22), title, font=sans(tsize, 10), fill=INK)
    yy = y + 22 + tsize + 14
    for ln in lines:
        d.text((x + 28, yy), ln, font=sans(24), fill=MUTE)
        yy += 36


def container(d, x0, y0, x1, y1, label):
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=PINK, width=3)
    tracked(d, (x0 + 30, y0 + 24), label, sans(24, 10), PINK, 5)


def arrow(d, x0, y0, x1, y1, color=None, width=4):
    color = color or (130, 138, 158)
    d.line([x0, y0, x1, y1], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    for s in (-0.45, 0.45):
        d.line([x1, y1, x1 - 20 * math.cos(ang + s), y1 - 20 * math.sin(ang + s)],
               fill=color, width=width)


def label(d, x, y, text, fill=MUTE, size=24, center=True):
    f = sans(size)
    wdt = d.textlength(text, font=f)
    d.text((x - (wdt / 2 if center else 0), y), text, font=f, fill=fill)


def main():
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    m = 110
    tracked(d, (m, 84), "AI SHOWRUNNER — SYSTEM ARCHITECTURE", sans(26), PINK, 7)
    d.text((m, 140), "How Qwen Cloud powers the studio", font=sans(78, 1), fill=INK)
    d.text((m, 252), "A FastAPI backend and file store on Alibaba Cloud ECS; every "
                     "generative call goes to Qwen Cloud (DashScope, intl).",
           font=sans(32), fill=MUTE)

    # ---------- frontend ----------
    container(d, 110, 420, 700, 1050, "FRONTEND — BROWSER")
    node(d, 150, 500, 510, 210, "Studio dashboard",
         ["single-page app served by the backend",
          "live shot tree · takes · QA scores",
          "price shown before Start"], tsize=36)
    node(d, 150, 750, 510, 250, "Human-in-the-loop",
         ["approval gates: story · storyboard ·",
          "frames · final cut",
          "Regen / Extend / Jump / Lock per shot"], tsize=36)

    # ---------- backend on ECS ----------
    container(d, 860, 420, 1560, 1490, "ALIBABA CLOUD ECS — AP-SOUTHEAST-1")
    node(d, 900, 500, 620, 160, "nginx :80  ›  FastAPI",
         ["Bearer-token auth · request log",
          "GET /healthz self-attests the ECS instance-id"], tsize=36)
    node(d, 900, 700, 620, 105, "Job queue — one worker",
         ["serializes all paid generation"], tsize=32)
    node(d, 900, 845, 620, 230, "Orchestrator",
         ["Planner › Storyboard › per-shot loop",
          "(render › critic › targeted retry ×2)",
          "› Editor (ffmpeg · subtitles · cover · AIGC)"], tsize=36, accent=True)
    node(d, 900, 1115, 620, 105, "Cost governor",
         ["pre-flight estimate · budget admission"], tsize=32)
    node(d, 900, 1260, 620, 190, "File store  (the database)",
         ["runs/: story bible · ShotSpecs · QA · EDL ·",
          "events.jsonl · clips · finals  — all replayable",
          "library/: locked cast portraits · voices"], tsize=36)

    # ---------- Qwen Cloud ----------
    container(d, 1720, 420, 2290, 1330, "QWEN CLOUD · DASHSCOPE")
    node(d, 1760, 500, 490, 150, "Qwen3.7-Max",
         ["four-beat script · storyboard", "multi-language localization"], tsize=36)
    node(d, 1760, 690, 490, 150, "Qwen-VL",
         ["the critic — scores 3 frames/take", "narrative · consistency · quality"],
         tsize=36)
    node(d, 1760, 880, 490, 150, "Wan2.7  t2v / i2v",
         ["every shot's video", "i2v first_frame = locked portrait"], tsize=36)
    node(d, 1760, 1070, 490, 150, "Qwen3-TTS / Qwen-Image",
         ["dubbing voices · narration", "Frame Gate stills (wired)"], tsize=36)
    d.text((1760, 1355), "https://dashscope-intl.aliyuncs.com", font=sans(26), fill=DIM)
    d.text((1760, 1392), "compatible-mode/v1 (text · VL)  ·  api/v1 (async video/TTS)",
           font=sans(24), fill=DIM)

    # ---------- flows ----------
    arrow(d, 700, 600, 860, 600)
    arrow(d, 860, 660, 700, 660)
    label(d, 780, 552, "HTTPS", PINK, 26)
    label(d, 780, 684, "polling", MUTE, 24)

    arrow(d, 1520, 930, 1720, 930, color=PINK, width=5)
    arrow(d, 1720, 990, 1520, 990, color=PINK, width=5)
    label(d, 1620, 855, "HTTPS · JSON", PINK, 23)
    label(d, 1620, 1015, "clips · frames", MUTE, 22)
    label(d, 1620, 1050, "poll /tasks/{id}", MUTE, 22)

    arrow(d, 1210, 1220, 1210, 1260, width=4)
    arrow(d, 1300, 1260, 1300, 1220, width=4)
    label(d, 1258, 1178, "", MUTE)

    d.line([m, H - 84, W - m, H - 84], fill=(30, 34, 46), width=1)
    tracked(d, (m, H - 64),
            "DEPLOY: DEPLOY/DEPLOY.SH (SYSTEMD + NGINX) OR DOCKER COMPOSE — "
            "ONE ECS INSTANCE RUNS EVERYTHING", sans(20), DIM, 4)

    png = OUT / "architecture.png"
    c.save(png)
    c.convert("RGB").save(OUT / "architecture.pdf", "PDF", resolution=200)
    print("saved:", png, "and architecture.pdf")


if __name__ == "__main__":
    main()
