"""Render bilingual subtitles + titled cover with Pillow, then composite via ffmpeg overlay.

Why not ffmpeg's subtitles/drawtext filter? The available ffmpeg build ships without
libass/libfreetype. Rendering to transparent PNGs and using the (present) overlay filter is
fully self-contained, portable to the deploy box, and gives the CN-big / EN-small look that
vertical short dramas use."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W = 1080
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
]


def find_font() -> str:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return f
    raise RuntimeError("No CJK font found; set one from FONT_CANDIDATES or install Noto Sans CJK.")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(find_font(), size)


def _wrap(draw, text: str, font, max_w: int) -> list[str]:
    if not text:
        return []
    # word-wrap for latin, char-wrap for CJK-dense strings
    units = text.split(" ") if " " in text and text.isascii() else list(text)
    joiner = " " if " " in text and text.isascii() else ""
    lines, cur = [], ""
    for u in units:
        trial = (cur + joiner + u).strip() if cur else u
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = u
    if cur:
        lines.append(cur)
    return lines


def render_cue(zh: str, en: str, out_path) -> Path:
    """Transparent full-width strip: CN line(s) large on top, EN smaller below."""
    max_w = W - 120
    zf, ef = _font(50), _font(34)
    scratch = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    zh_lines = _wrap(scratch, zh, zf, max_w)
    en_lines = _wrap(scratch, en, ef, max_w)

    rows = [(l, zf, (255, 255, 255, 255), 60) for l in zh_lines] + \
           [(l, ef, (215, 220, 230, 255), 44) for l in en_lines]
    h = sum(r[3] for r in rows) + 24
    img = Image.new("RGBA", (W, max(h, 1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 12
    for text, font, color, line_h in rows:
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, y), text, font=font, fill=color,
               stroke_width=3, stroke_fill=(0, 0, 0, 235))
        y += line_h
    out_path = Path(out_path)
    img.save(out_path)
    return out_path


def build_slots(tracks, master_lang: str, sec_lang: str | None, outdir) -> list[dict]:
    """From SubtitleTracks build [{png,start,end}] for the overlay burn."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    by_lang = {t.lang: t.cues for t in tracks}
    master = by_lang.get(master_lang, [])
    sec = by_lang.get(sec_lang, []) if sec_lang else []
    slots = []
    for i, cue in enumerate(master):
        zh = (cue.get("text") or "").strip()
        en = (sec[i].get("text") if i < len(sec) else "") or ""
        if not zh and not en:
            continue
        png = render_cue(zh, en.strip(), outdir / f"cue_{i:03d}.png")
        slots.append({"png": str(png), "start": cue["start"], "end": cue["end"]})
    return slots


def render_aigc_badge(out_path, text: str = "AI生成") -> Path:
    """Small translucent corner badge required by CN AIGC labeling rules (explicit label).
    Rendered once per run and overlaid for the full duration of the final cut."""
    font = _font(28)
    scratch = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(scratch.textlength(text, font=font)) + 28
    img = Image.new("RGBA", (w, 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 45], radius=10, fill=(0, 0, 0, 110))
    d.text((14, 8), text, font=font, fill=(255, 255, 255, 210))
    out_path = Path(out_path)
    img.save(out_path)
    return out_path


def render_cover(frame_path, title: str, out_path) -> Path:
    """Draw the title near the bottom of an extracted frame (drawtext-free cover)."""
    img = Image.open(frame_path).convert("RGB")
    d = ImageDraw.Draw(img)
    font = _font(72)
    lines = _wrap(d, title, font, img.width - 120)
    y = img.height - 260 - (len(lines) - 1) * 84
    for line in lines:
        w = d.textlength(line, font=font)
        d.text(((img.width - w) / 2, y), line, font=font, fill=(255, 255, 255),
               stroke_width=4, stroke_fill=(0, 0, 0))
        y += 84
    out_path = Path(out_path)
    img.save(out_path)
    return out_path
