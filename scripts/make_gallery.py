"""Devpost gallery v3 — unified dark product-launch plates (1920x1280, 3:2).

  python -m scripts.make_gallery

One visual system for all eight plates, matching the product's own dark UI:
same background as the app (screenshots blend seamlessly), one accent (the UI's
pink), one type system. Every plate = one claim (headline) + what you are
literally looking at (subline) + a LARGE legible crop with pink spotlight
annotations pointing at the exact UI elements. 2x-DPR screenshots keep text sharp.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(".")
SRC = ROOT / "docs/devpost/source"
GAL = ROOT / "docs/devpost/gallery"
RUNS = ROOT / "runs"

W, H = 1920, 1280
BG = (10, 12, 17)            # exactly the app background
PANEL = (18, 21, 28)
BORDER = (42, 48, 64)
INK = (238, 241, 247)        # headline white
MUTE = (152, 160, 179)       # sub / captions
DIM = (96, 103, 120)         # footer
PINK = (255, 92, 122)        # the product's accent

HELV = "/System/Library/Fonts/HelveticaNeue.ttc"


def sans(size, face=0):      # 0 regular · 1 bold · 10 medium · 7 light
    return ImageFont.truetype(HELV, size, index=face)


def cjk(size):
    from showrunner.subtitle_render import _font
    return _font(size)


def tracked(d, xy, text, font, fill, tracking=5):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking
    return x


def tracked_w(d, text, font, tracking=5):
    return sum(d.textlength(c, font=font) + tracking for c in text) - tracking


def rounded(img, radius=14):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                                           radius=radius, fill=255)
    out = Image.new("RGBA", img.size)
    out.paste(img, (0, 0), mask)
    return out


def glow_card(canvas, img, x, y, radius=14):
    """Rounded screenshot card with border + soft ambient glow."""
    gl = Image.new("RGBA", (img.width + 120, img.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(gl).rounded_rectangle([60, 60, 60 + img.width, 60 + img.height],
                                         radius=radius, fill=(255, 92, 122, 26))
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    canvas.paste(gl, (x - 60, y - 60), gl)
    rimg = rounded(img, radius)
    canvas.paste(rimg, (x, y), rimg)
    ImageDraw.Draw(canvas).rounded_rectangle([x, y, x + img.width - 1, y + img.height - 1],
                                             radius=radius, outline=BORDER, width=2)


def chrome(c, d, idx, headline, sub):
    m = 96
    tracked(d, (m, 74), "AI SHOWRUNNER — VIRTUAL PRODUCTION STUDIO", sans(23), PINK, 6)
    folio = f"{idx:02d} / 08"
    f = sans(23)
    d.text((W - m - d.textlength(folio, font=f), 74), folio, font=f, fill=DIM)
    d.text((m, 126), headline, font=sans(62, 1), fill=INK)
    d.text((m, 216), sub, font=sans(29), fill=MUTE)
    d.line([m, H - 74, W - m, H - 74], fill=(30, 34, 46), width=1)
    tracked(d, (m, H - 56), "BUILT ON QWENCLOUD — QWEN3.7-MAX · QWEN-VL · WAN2.7 · QWEN3-TTS",
            sans(18), DIM, 4)


def spotlight(canvas, d, box, label, side="right"):
    """Pink rounded outline + connected label chip."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=PINK, width=3)
    f = sans(23, 10)
    tw = d.textlength(label, font=f)
    ch_h = 46
    pad = 18
    if side == "right":
        lx, ly = x1 + 46, (y0 + y1) // 2 - ch_h // 2
        d.line([x1 + 3, (y0 + y1) // 2, lx, ly + ch_h // 2], fill=PINK, width=2)
    elif side == "left":
        lx, ly = x0 - 46 - tw - 2 * pad, (y0 + y1) // 2 - ch_h // 2
        d.line([x0 - 3, (y0 + y1) // 2, lx + tw + 2 * pad, ly + ch_h // 2], fill=PINK, width=2)
    elif side == "above":
        lx, ly = (x0 + x1) // 2 - tw / 2 - pad, y0 - 46 - ch_h
        d.line([(x0 + x1) // 2, y0 - 3, (x0 + x1) // 2, ly + ch_h], fill=PINK, width=2)
    else:  # below
        lx, ly = (x0 + x1) // 2 - tw / 2 - pad, y1 + 46
        d.line([(x0 + x1) // 2, y1 + 3, (x0 + x1) // 2, ly], fill=PINK, width=2)
    d.rounded_rectangle([lx, ly, lx + tw + 2 * pad, ly + ch_h], radius=23,
                        fill=(26, 16, 22), outline=PINK, width=2)
    d.text((lx + pad, ly + 9), label, font=f, fill=PINK)


def evidence_plate(idx, out, headline, sub, shot, crop, spots, max_h=890):
    """The uniform plate: header + one big annotated screenshot crop."""
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    chrome(c, d, idx, headline, sub)
    img = Image.open(SRC / shot).convert("RGB").crop(crop)
    avail_w, avail_h = W - 260, max_h
    r = min(avail_w / img.width, avail_h / img.height)
    disp = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x = (W - disp.width) // 2
    y = 290 + (max_h - disp.height) // 2
    glow_card(c, disp, x, y)
    for (bx0, by0, bx1, by1, label, side) in spots:
        box = (x + (bx0 - crop[0]) * r, y + (by0 - crop[1]) * r,
               x + (bx1 - crop[0]) * r, y + (by1 - crop[1]) * r)
        spotlight(c, d, box, label, side)
    c.save(GAL / out)
    print("gallery:", out)


def hero():
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    m = 96
    tracked(d, (m, 74), "GLOBAL AI HACKATHON — TRACK 2 · AI SHOWRUNNER", sans(23), PINK, 6)
    f = sans(23)
    d.text((W - m - d.textlength("01 / 08", font=f), 74), "01 / 08", font=f, fill=DIM)
    d.text((m, 140), "One line in.", font=sans(96, 1), fill=INK)
    d.text((m, 258), "A finished vertical drama out.", font=sans(96, 1), fill=PINK)
    d.text((m, 404), "An autonomous studio on QwenCloud — it writes, casts, shoots, reviews "
                     "its own footage, and delivers.", font=sans(30), fill=MUTE)
    d.text((m, 448), "These three dramas were produced end-to-end by the system.",
           font=sans(30), fill=MUTE)

    stills = [(RUNS / "20260706-110141/cover.png", "夜班替身 · zh/en/es tracks"),
              (RUNS / "20260706-023130/cover.png", "完美不在场 · bilingual burn-in"),
              (RUNS / "20260706-021212/cover.png", "DEAD DROP ALIBI · suspense")]
    bw, bh = 356, 632
    gap = 60
    x0 = W - m - 3 * bw - 2 * gap
    fl = cjk(23)
    for i, (p, lbl) in enumerate(stills):
        img = Image.open(p).convert("RGB")
        r = min(bw / img.width, bh / img.height)
        img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
        x = x0 + i * (bw + gap)
        glow_card(c, img, x, 528)
        lw = d.textlength(lbl, font=fl)
        d.text((x + (bw - lw) / 2, 528 + bh + 22), lbl, font=fl, fill=MUTE)
    d.line([m, H - 74, W - m, H - 74], fill=(30, 34, 46), width=1)
    tracked(d, (m, H - 56), "BUILT ON QWENCLOUD — QWEN3.7-MAX · QWEN-VL · WAN2.7 · QWEN3-TTS",
            sans(18), DIM, 4)
    c.save(GAL / "01_hero.png")
    print("gallery: 01_hero.png")


def cast_plate():
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    chrome(c, d, 5, "One locked portrait. The same face in every shot.",
           "The cast library portrait (left) drives both shots via Wan2.7 image-to-video "
           "— no fine-tuning, no LoRA.")
    panels = [(RUNS / "20260706-103834/refs/lin.png", "LOCKED PORTRAIT — CAST LIBRARY"),
              (RUNS / "20260706-103834/cmp_s0_sh0.png", "SHOT 1 · CONSISTENCY 9/10"),
              (RUNS / "20260706-103834/cmp_s1_sh0.png", "SHOT 2 · CONSISTENCY 9/10")]
    bw, bh = 430, 760
    gap = 128
    x0 = (W - 3 * bw - 2 * gap) // 2
    f_l = sans(21, 10)
    for i, (p, lbl) in enumerate(panels):
        img = Image.open(p).convert("RGB")
        r = min(bw / img.width, bh / img.height)
        img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
        x = x0 + i * (bw + gap) + (bw - img.width) // 2
        glow_card(c, img, x, 316)
        lw = tracked_w(d, lbl, f_l, 3)
        tracked(d, (x0 + i * (bw + gap) + (bw - lw) / 2, 316 + bh + 26), lbl, f_l,
                PINK if i == 0 else MUTE, 3)
        if i < 2:
            ax = x0 + (i + 1) * (bw + gap) - gap / 2
            d.line([ax - 30, 316 + bh / 2, ax + 30, 316 + bh / 2], fill=PINK, width=3)
            d.polygon([(ax + 30, 316 + bh / 2), (ax + 14, 316 + bh / 2 - 10),
                       (ax + 14, 316 + bh / 2 + 10)], fill=PINK)
    c.save(GAL / "05_the_cast.png")
    print("gallery: 05_the_cast.png")


def node(d, x, y, w, h, title, sub=None, accent=False):
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=PANEL,
                        outline=PINK if accent else BORDER, width=3 if accent else 2)
    f_t = sans(30, 10)
    tw = d.textlength(title, font=f_t)
    ty = y + (h - (58 if sub else 34)) / 2
    d.text((x + (w - tw) / 2, ty), title, font=f_t, fill=INK)
    if sub:
        f_s = sans(21)
        sw = d.textlength(sub, font=f_s)
        d.text((x + (w - sw) / 2, ty + 40), sub, font=f_s, fill=MUTE)


def arrow(d, x0, y0, x1, y1, color=None):
    color = color or (120, 128, 148)
    d.line([x0, y0, x1, y1], fill=color, width=3)
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    for s in (-0.45, 0.45):
        d.line([x1, y1, x1 - 16 * math.cos(ang + s), y1 - 16 * math.sin(ang + s)],
               fill=color, width=3)


def gate(d, x, y, label):
    d.polygon([(x, y - 14), (x + 14, y), (x, y + 14), (x - 14, y)], outline=PINK, width=3)
    f = sans(19)
    tw = d.textlength(label, font=f)
    d.text((x - tw / 2, y + 24), label, font=f, fill=PINK)


def system_plate():
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    chrome(c, d, 8, "Write · cast · shoot · judge · deliver — one governed loop.",
           "Every artifact is replayable JSON; any shot re-runs alone. Humans approve at "
           "three gates; the budget gate can refuse spend.")
    ty = 560
    node(d, 120, ty, 240, 96, "Brief", "one line + budget")
    arrow(d, 360, ty + 48, 420, ty + 48)
    node(d, 420, ty, 280, 96, "Planner", "Qwen3.7-Max · four beats")
    gate(d, 740, ty + 48, "gate")
    arrow(d, 760, ty + 48, 820, ty + 48)
    node(d, 820, ty, 300, 96, "Storyboard", "ShotSpecs · cast reuse")
    gate(d, 1160, ty + 48, "gate")
    arrow(d, 1180, ty + 48, 1240, ty + 48)
    # the shoot/judge loop
    d.rounded_rectangle([1240, ty - 150, 1800, ty + 200], radius=18,
                        outline=PINK, width=3)
    tracked(d, (1290, ty - 132), "PER-SHOT LOOP · 3-WAY PARALLEL", sans(19, 10), PINK, 4)
    node(d, 1290, ty - 92, 460, 88, "Wan2.7 render", "i2v from locked portrait")
    arrow(d, 1520, ty - 4, 1520, ty + 32)
    node(d, 1290, ty + 32, 460, 88, "Qwen-VL critic", "narrative · consistency · quality")
    f = sans(21, 10)
    note = "fail — targeted retry, then best take wins"
    nw = d.textlength(note, font=f)
    d.text((1520 - nw / 2, ty + 140), note, font=f, fill=PINK)
    arrow(d, 1520, ty + 204, 1520, ty + 296)
    d.text((1544, ty + 232), "pass", font=sans(21), fill=MUTE)
    # editor + delivery row
    node(d, 640, ty + 300, 380, 96, "Editor", "ffmpeg · subtitles · cover")
    arrow(d, 1290, ty + 348, 1020, ty + 348)
    node(d, 1290, ty + 300, 460, 96, "approved takes", "version stacks · $0 re-cut")
    gate(d, 560, ty + 348, "final gate")
    arrow(d, 540, ty + 348, 500, ty + 348)
    node(d, 120, ty + 300, 380, 96, "Delivery", "final.mp4 · zh/en/es · AIGC label")
    c.save(GAL / "08_the_system.png")
    print("gallery: 08_the_system.png")


def main():
    GAL.mkdir(parents=True, exist_ok=True)
    hero()

    evidence_plate(
        2, "02_the_brief.png",
        "The exact price — before you generate.",
        "The New Production form: genre templates, locked-cast reuse, and a live estimate "
        "next to the Start button.",
        "hd_create.png", (870, 160, 2900, 1720),
        [(1290, 1385, 1680, 1465, "the estimate — before a single frame", "below"),
         (955, 1290, 2180, 1348, "Frame Gate: reject a $0.02 still, not a $0.30 clip", "right")])

    evidence_plate(
        3, "03_the_script.png",
        "The story earns approval before money moves.",
        "The Story view of Night Shift Double: logline, synopsis, cast — and the four-beat "
        "sheet (Hook · Friction · Spike · Button) that paces vertical drama.",
        "hd_bible.png", (880, 120, 3220, 1820),
        [(920, 150, 1845, 240, "human approval gates", "right"),
         (2060, 270, 2620, 322, "the four-beat sheet", "above")])

    evidence_plate(
        4, "04_the_critic.png",
        "Every take is scored. Failures get a targeted retry.",
        "The Production view: Qwen-VL rates each take on narrative / consistency / quality; "
        "every shot has Regen · Extend · Jump · Lock.",
        "hd_shots.png", (890, 280, 3180, 1740),
        [(1240, 530, 1740, 590, "Qwen-VL scores, per take", "below"),
         (2600, 360, 3130, 420, "director controls, per shot", "below")])

    cast_plate()

    evidence_plate(
        6, "06_the_final.png",
        "One master cut. Three languages. Ready to publish.",
        "The Final view of Night Shift Double: bilingual burn-in, subtitle tracks generated "
        "from one master script, auto cover, AIGC label.",
        "hd_final.png", (850, 140, 2960, 1420),
        [(1550, 470, 2160, 560, "zh · en · es from one master script", "right"),
         (910, 270, 1520, 1360, "auto cover + AIGC label", "below")],
        max_h=830)

    evidence_plate(
        7, "07_the_catalogue.png",
        "Four dramas. Every artifact replayable.",
        "The Productions wall: each run stores its story bible, shots, QA reports and EDL "
        "as JSON — open any of them and re-cut for $0.",
        "hd_runs.png", (880, 160, 3200, 1150),
        [(916, 214, 1342, 1090, "opens the full production state", "below")])

    system_plate()


if __name__ == "__main__":
    main()
