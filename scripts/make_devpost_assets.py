"""Generate Devpost assets — editorial gallery (1920x1280, 3:2) + workflow demo reel (1920x1080).

  python -m scripts.make_devpost_assets

Design system: ivory editorial (gallery-window framing) — Didot display serif,
Helvetica Neue eyebrows, hairline rules, orange accent. Product screenshots and
real film stills carry every frame; graphics only frame them.
Uses only local artifacts (no API calls).
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(".")
SRC = ROOT / "docs/devpost/source"
GAL = ROOT / "docs/devpost/gallery"
OUT = ROOT / "docs/devpost"
RUNS = ROOT / "runs"

W, H = 1920, 1280            # gallery 3:2
RW, RH = 1920, 1080          # reel 16:9

IVORY = (245, 242, 235)
INK = (23, 21, 18)
ACCENT = (222, 96, 27)       # burnt orange
HAIR = (214, 208, 196)       # hairline rule
MUTE = (138, 133, 124)

DIDOT = "/System/Library/Fonts/Didot.ttc"
HELV = "/System/Library/Fonts/HelveticaNeue.ttc"


def serif(size, bold=False):
    return ImageFont.truetype(DIDOT, size, index=2 if bold else 0)


def sans(size, weight=0):
    # HelveticaNeue.ttc: 0 regular; try light face for large sizes
    return ImageFont.truetype(HELV, size, index=weight)


def eyebrow_text(d, xy, text, size=26, fill=MUTE, tracking=6):
    """Letter-spaced uppercase caption, the editorial 'eyebrow'."""
    f = sans(size)
    x, y = xy
    for ch in text.upper():
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking
    return x


def eyebrow_width(d, text, size=26, tracking=6):
    f = sans(size)
    return sum(d.textlength(c, font=f) + tracking for c in text.upper()) - tracking


def frame_shadowed(canvas, img, x, y, border=True):
    """Paste artwork with a soft drop shadow + hairline border, like a framed print."""
    sh = Image.new("RGBA", (img.width + 80, img.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([40, 46, 40 + img.width, 46 + img.height],
                                 fill=(23, 21, 18, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(sh, (x - 40, y - 40), sh)
    canvas.paste(img, (x, y))
    if border:
        ImageDraw.Draw(canvas).rectangle([x - 1, y - 1, x + img.width, y + img.height],
                                         outline=HAIR, width=1)


def fit(img, box_w, box_h):
    r = min(box_w / img.width, box_h / img.height)
    return img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)


def chrome(c, d, idx, total=8):
    """Shared page furniture: top rule + eyebrow left, folio right, bottom rule."""
    m = 90
    d.line([m, 84, W - m, 84], fill=INK, width=2)
    eyebrow_text(d, (m, 100), "AI Showrunner — Virtual Production Studio", 22, MUTE, 5)
    folio = f"{idx:02d} / {total:02d}"
    f = sans(22)
    d.text((W - m - d.textlength(folio, font=f), 100), folio, font=f, fill=MUTE)
    d.line([m, H - 96, W - m, H - 96], fill=HAIR, width=1)
    eyebrow_text(d, (m, H - 78), "Qwen3.7-Max · Qwen-VL · Wan2.7 — built on QwenCloud", 19, MUTE, 4)


def plate(idx, shot_path, headline, caption, out_name, crop=None):
    """One editorial plate: framed product screenshot + serif headline."""
    c = Image.new("RGB", (W, H), IVORY)
    d = ImageDraw.Draw(c)
    chrome(c, d, idx)
    img = Image.open(shot_path).convert("RGB")
    if crop:
        img = img.crop(crop)
    img = fit(img, W - 320, H - 470)
    x = (W - img.width) // 2
    frame_shadowed(c, img, x, 168)
    hy = 168 + img.height + 52
    fh = serif(58)
    d.text(((W - d.textlength(headline, font=fh)) / 2, hy), headline, font=fh, fill=INK)
    fc = sans(27)
    d.text(((W - d.textlength(caption, font=fc)) / 2, hy + 84), caption, font=fc, fill=MUTE)
    c.save(GAL / out_name)
    print("gallery:", out_name)


def hero(out_name):
    c = Image.new("RGB", (W, H), IVORY)
    d = ImageDraw.Draw(c)
    m = 90
    d.line([m, 84, W - m, 84], fill=INK, width=2)
    eyebrow_text(d, (m, 100), "Global AI Hackathon · Track 2 · Built on QwenCloud", 22, MUTE, 5)
    f = sans(22)
    d.text((W - m - d.textlength("01 / 08", font=f), 100), "01 / 08", font=f, fill=MUTE)

    t = "AI Showrunner"
    ft = serif(150)
    d.text(((W - d.textlength(t, font=ft)) / 2, 150), t, font=ft, fill=INK)
    sub = "One line in.  A finished vertical drama out."
    ew = eyebrow_width(d, sub, 30, 8)
    eyebrow_text(d, ((W - ew) / 2, 340), sub, 30, ACCENT, 8)

    stills = [RUNS / "20260706-110141/cover.png",
              RUNS / "20260706-023130/cover.png",
              RUNS / "20260706-021212/cover.png"]
    labels = ["夜班替身 — Night Shift Double", "完美不在场 — The Perfect Alibi", "Dead Drop Alibi"]
    bw, bh = 388, 690
    gap = 96
    x0 = (W - 3 * bw - 2 * gap) // 2
    from showrunner.subtitle_render import _font as cjk_font
    fl = cjk_font(24)
    for i, (p, lbl) in enumerate(zip(stills, labels)):
        img = fit(Image.open(p).convert("RGB"), bw, bh)
        x = x0 + i * (bw + gap) + (bw - img.width) // 2
        frame_shadowed(c, img, x, 430)
        lw = d.textlength(lbl, font=fl)
        d.text((x0 + i * (bw + gap) + (bw - lw) / 2, 430 + bh + 26), lbl, font=fl, fill=MUTE)
    c.save(GAL / out_name)
    print("gallery:", out_name)


def consistency_plate(out_name, idx):
    c = Image.new("RGB", (W, H), IVORY)
    d = ImageDraw.Draw(c)
    chrome(c, d, idx)
    panels = [(RUNS / "20260706-103834/refs/lin.png", "The locked portrait"),
              (RUNS / "20260706-103834/cmp_s0_sh0.png", "Shot 1 — consistency 9 / 10"),
              (RUNS / "20260706-103834/cmp_s1_sh0.png", "Shot 2 — consistency 9 / 10")]
    bw, bh = 430, 690
    gap = 120
    x0 = (W - 3 * bw - 2 * gap) // 2
    fl = sans(24)
    for i, (p, lbl) in enumerate(panels):
        img = fit(Image.open(p).convert("RGB"), bw, bh)
        x = x0 + i * (bw + gap) + (bw - img.width) // 2
        frame_shadowed(c, img, x, 200)
        lw = d.textlength(lbl, font=fl)
        d.text((x0 + i * (bw + gap) + (bw - lw) / 2, 200 + bh + 28), lbl, font=fl, fill=MUTE)
        if i < 2:  # arrow between panels
            ax = x0 + (i + 1) * (bw + gap) - gap / 2
            d.text((ax - 14, 200 + bh / 2 - 24), "→", font=serif(48), fill=ACCENT)
    hl = "One portrait drives every shot"
    fh = serif(58)
    d.text(((W - d.textlength(hl, font=fh)) / 2, 200 + bh + 90), hl, font=fh, fill=INK)
    cap = "Wan2.7 image-to-video from a reusable cast library — no fine-tuning, no LoRA"
    fc = sans(27)
    d.text(((W - d.textlength(cap, font=fc)) / 2, 200 + bh + 174), cap, font=fc, fill=MUTE)
    c.save(GAL / out_name)
    print("gallery:", out_name)


# ---------------- demo reel ----------------
def _encode_still(png, out_path, seconds, kenburns=True):
    zoom = ("scale=3840:-2,zoompan=z='min(zoom+0.00055,1.10)':d=%d:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" % int(seconds * 30)
            ) if kenburns else "scale=1920:1080:force_original_aspect_ratio=decrease," \
                               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf5f2eb"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(png),
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-t", str(seconds), "-r", "30", "-vf", zoom,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                    str(out_path)], check=True, capture_output=True)


def title_card(eyebrow, headline, out_path, seconds=2.6, sub=None):
    img = Image.new("RGB", (RW, RH), IVORY)
    d = ImageDraw.Draw(img)
    m = 120
    d.line([m, 130, RW - m, 130], fill=INK, width=2)
    d.line([m, RH - 130, RW - m, RH - 130], fill=HAIR, width=1)
    if eyebrow:
        ew = eyebrow_width(d, eyebrow, 28, 8)
        eyebrow_text(d, ((RW - ew) / 2, RH // 2 - 150), eyebrow, 28, ACCENT, 8)
    fh = serif(110)
    d.text(((RW - d.textlength(headline, font=fh)) / 2, RH // 2 - 90), headline, font=fh, fill=INK)
    if sub:
        fs = sans(32)
        d.text(((RW - d.textlength(sub, font=fs)) / 2, RH // 2 + 74), sub, font=fs, fill=MUTE)
    png = out_path.with_suffix(".png")
    img.save(png)
    _encode_still(png, out_path, seconds, kenburns=False)


def ui_seg(shot_path, out_path, seconds=4.2, crop=None):
    """Product screenshot on an ivory stage with a hairline frame, slow push-in."""
    stage = Image.new("RGB", (RW, RH), IVORY)
    img = Image.open(shot_path).convert("RGB")
    if crop:
        img = img.crop(crop)
    img = fit(img, RW - 220, RH - 140)
    x, y = (RW - img.width) // 2, (RH - img.height) // 2
    frame_shadowed(stage, img, x, y)
    png = out_path.with_suffix(".png")
    stage.save(png)
    _encode_still(png, out_path, seconds, kenburns=True)


def film_seg(src, out_path, seconds, start=0):
    subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", str(src), "-t", str(seconds),
                    "-vf", "scale=-2:1080,pad=1920:1080:(ow-iw)/2:0:color=0x0a0c11",
                    "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", str(out_path)],
                   check=True, capture_output=True)


def main():
    GAL.mkdir(parents=True, exist_ok=True)

    # ---- gallery: eight editorial plates ----
    hero("01_hero.png")
    plate(2, SRC / "fresh_create.png",
          "The brief — priced before a single frame",
          "Genre templates, locked-cast reuse, Frame Gate, and the exact cost next to Start",
          "02_the_brief.png", crop=(0, 0, 1800, 800))
    plate(3, SRC / "fresh_bible_110141.png",
          "A story bible before any spend",
          "Four-beat sheet (Hook · Friction · Spike · Button), logline, cast — human-approved",
          "03_the_script.png", crop=(0, 0, 1800, 924))
    plate(4, SRC / "fresh_shots_023130.png",
          "Every take judged, every retry targeted",
          "Qwen-VL scores narrative / consistency / quality per take — Regen · Extend · Jump · Lock",
          "04_the_critic.png", crop=(0, 0, 1800, 984))
    consistency_plate("05_the_cast.png", 5)
    plate(6, SRC / "fresh_final_110141.png",
          "One master cut, three languages",
          "Bilingual burned subtitles, zh · en · es tracks, auto cover, AIGC-compliance label",
          "06_the_final.png", crop=(0, 0, 1800, 700))
    plate(7, SRC / "fresh_runs.png",
          "Four dramas, every artifact replayable",
          "Each production is inspectable JSON end-to-end — story bible to EDL",
          "07_the_catalogue.png",
          crop=(235, 0, 1800, 620))
    arch = SRC / "architecture.png"
    if not arch.exists():
        subprocess.run(["qlmanage", "-t", "-s", "1920", "-o", str(SRC),
                        "assets/architecture.svg"], capture_output=True)
        g = SRC / "architecture.svg.png"
        if g.exists():
            g.rename(arch)
    plate(8, arch,
          "Planner · Executor · Critic · Editor",
          "Structured artifacts at every stage — any shot re-runs without redoing the pipeline",
          "08_the_system.png")

    # ---- demo reel: the full workflow, chaptered ----
    tmp = OUT / "_reel"
    tmp.mkdir(exist_ok=True)
    segs = []

    def S(name):
        p = tmp / f"{len(segs):02d}_{name}.mp4"
        segs.append(p)
        return p

    title_card("One line in — a finished vertical drama out", "AI Showrunner", S("open"), 3.2,
               sub="a virtual production studio on QwenCloud")
    title_card("Chapter 01", "The brief", S("c1"), 2.2, sub="price shown before a single frame is rendered")
    ui_seg(SRC / "fresh_create.png", S("ui_create"), 4.5, crop=(0, 0, 1800, 800))
    title_card("Chapter 02", "The script", S("c2"), 2.2, sub="four beats · story bible · human approval gates")
    ui_seg(SRC / "fresh_bible_110141.png", S("ui_bible"), 4.5, crop=(0, 0, 1800, 924))
    title_card("Chapter 03", "The cast", S("c3"), 2.2, sub="one locked portrait drives every shot")
    ui_seg(GAL / "05_the_cast.png", S("ui_cast"), 4.2, crop=(0, 130, 1920, 1210))
    title_card("Chapter 04", "The shoot", S("c4"), 2.2, sub="Wan2.7 renders — Qwen-VL judges every take")
    ui_seg(SRC / "fresh_shots_023130.png", S("ui_shots"), 4.5, crop=(0, 0, 1800, 984))
    film_seg(RUNS / "20260706-110141/final.mp4", S("film_night"), 11)
    title_card("Chapter 05", "The final cut", S("c5"), 2.2, sub="bilingual burn-in · zh/en/es tracks · cover · AIGC label")
    ui_seg(SRC / "fresh_final_110141.png", S("ui_final"), 4, crop=(0, 0, 1800, 700))
    film_seg(RUNS / "20260706-023130/final.mp4", S("film_alibi"), 9)
    film_seg(RUNS / "20260706-103834/final.mp4", S("film_loop"), 6)
    title_card("github.com/Yanjin-ai/showrunner", "Built on QwenCloud", S("close"), 3.4,
               sub="Qwen3.7-Max · Qwen-VL · Wan2.7 · Alibaba Cloud ECS")

    listfile = tmp / "concat.txt"
    listfile.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    reel = OUT / "demo_reel_draft.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-ar", "44100", str(reel)], check=True, capture_output=True)
    print("reel:", reel)


if __name__ == "__main__":
    main()
