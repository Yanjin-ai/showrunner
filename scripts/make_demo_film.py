"""Build the narrated Devpost demo film — docs/devpost/demo_reel.mp4 (1920x1080).

  python -m scripts.make_demo_film            # full build (VO via Qwen-TTS, cached)
  python -m scripts.make_demo_film --no-vo    # silent build (skip TTS)

Design: the reel is the editorial system in motion — animated ivory title cards
(hairline draws in, eyebrow tracking settles, Didot headline rises), slow push-ins
on real product screenshots, real drama footage, 0.5s cross-dissolves throughout.
Narrated by the product's own TTS (qwen3-tts-flash, voice Ethan); an ambient
drone bed sits under everything and the dramas keep their native score.
"""
import math
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from scripts.make_gallery import (BG as IVORY, INK, PINK as ACCENT,
                                  BORDER as HAIR, MUTE, sans,
                                  glow_card as frame_shadowed)


def fit(img, box_w, box_h):
    r = min(box_w / img.width, box_h / img.height)
    return img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)

ROOT = Path(".")
SRC = ROOT / "docs/devpost/source"
GAL = ROOT / "docs/devpost/gallery"
OUT = ROOT / "docs/devpost"
RUNS = ROOT / "runs"
TMP = OUT / "_film"
VO_DIR = OUT / "_vo"
RW, RH = 1920, 1080
FPS = 30
XF = 0.5          # crossfade seconds


def ease(p):
    return 1 - (1 - p) ** 3


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------- narration ----------------
VO_LINES = {
    "open":  "This is AI Showrunner — a virtual production studio built on Qwen Cloud. "
             "One line in. A finished vertical drama out.",
    "brief": "Every production starts with a single line — and a price. "
             "The studio quotes the exact cost before a single frame is rendered.",
    "script": "Qwen Max writes a four-beat script and a story bible. "
              "A human approves the story before any money moves.",
    "cast":  "One locked portrait drives every shot through image-to-video. "
             "The same face, scene after scene — scored nine out of ten.",
    "shoot": "Wan renders every take, and a Qwen vision critic reviews each one. "
             "When a take fails, the critic writes the retry note itself.",
    "film1": "Every frame you are watching was generated, judged, and cut by the system.",
    "final": "One master cut becomes bilingual burned-in subtitles, three language tracks, "
             "cover art — and an A I G C compliance label.",
    "close": "AI Showrunner. Open source, built on Qwen Cloud. Even this voice is Qwen's.",
}


def make_vo():
    """Synthesize narration with the product's own TTS client (cached on disk)."""
    from showrunner.clients import tts
    VO_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, text in VO_LINES.items():
        wav = VO_DIR / f"{key}.wav"
        if not wav.exists():
            tts.synthesize(text, wav, voice="Ethan", lang="en")
            print("vo:", key, "synthesized")
        out[key] = wav
    return out


def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


# ---------------- animated title cards ----------------
def render_card_frames(frames_dir, seconds, eyebrow, headline, sub=None, closing=False):
    """Editorial card, animated: rule wipes in, eyebrow tracking settles, headline rises."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    n = int(seconds * FPS)
    m = 120
    f_h = sans(94, 1)
    f_s = sans(32)
    f_e = sans(28)
    for i in range(n):
        t = i / FPS
        img = Image.new("RGB", (RW, RH), IVORY)
        d = ImageDraw.Draw(img)
        # 1) hairline rules draw outward from center (0 → .55s)
        p = ease(min(1.0, t / 0.55))
        half = (RW - 2 * m) * p / 2
        d.line([RW / 2 - half, 130, RW / 2 + half, 130], fill=INK, width=2)
        d.line([RW / 2 - half, RH - 130, RW / 2 + half, RH - 130], fill=HAIR, width=1)
        # 2) eyebrow: alpha + tracking settles 22 → 8  (.15 → .85s)
        if eyebrow:
            pe = ease(max(0.0, min(1.0, (t - 0.15) / 0.7)))
            trk = 22 - 14 * pe
            a = int(255 * pe)
            if a > 0:
                layer = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
                dl = ImageDraw.Draw(layer)
                text = eyebrow.upper()
                wdt = sum(dl.textlength(c, font=f_e) + trk for c in text) - trk
                x = (RW - wdt) / 2
                for ch in text:
                    dl.text((x, RH / 2 - 150), ch, font=f_e, fill=(*ACCENT, a))
                    x += dl.textlength(ch, font=f_e) + trk
                img.paste(layer, (0, 0), layer)
        # 3) headline rises 26px + fades  (.3 → 1.1s)
        ph = ease(max(0.0, min(1.0, (t - 0.3) / 0.8)))
        if ph > 0:
            layer = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
            dl = ImageDraw.Draw(layer)
            w = dl.textlength(headline, font=f_h)
            dl.text(((RW - w) / 2, RH / 2 - 90 + 26 * (1 - ph)), headline,
                    font=f_h, fill=(*INK, int(255 * ph)))
            img.paste(layer, (0, 0), layer)
        # 4) sub fades (.75 → 1.45s)
        if sub:
            ps = ease(max(0.0, min(1.0, (t - 0.75) / 0.7)))
            if ps > 0:
                layer = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
                dl = ImageDraw.Draw(layer)
                w = dl.textlength(sub, font=f_s)
                dl.text(((RW - w) / 2, RH / 2 + 74), sub, font=f_s, fill=(*MUTE, int(255 * ps)))
                img.paste(layer, (0, 0), layer)
        # closing card: gentle breathe on the accent dot row
        if closing and t > 1.2:
            tw = 6 + 2 * math.sin((t - 1.2) * 2.2)
            d.ellipse([RW / 2 - tw, RH / 2 + 190 - tw, RW / 2 + tw, RH / 2 + 190 + tw],
                      fill=ACCENT)
        img.save(frames_dir / f"{i:04d}.png")


def card_seg(name, seconds, eyebrow, headline, sub=None, closing=False):
    frames = TMP / f"f_{name}"
    if not (frames / "0000.png").exists():
        render_card_frames(frames, seconds, eyebrow, headline, sub, closing)
    seg = TMP / f"{name}.mp4"
    run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames / "%04d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(seg)])
    return seg, seconds


def ui_seg(name, shot_path, seconds, crop=None):
    """Framed screenshot on ivory, slow push-in (Ken Burns)."""
    stage = Image.new("RGB", (RW, RH), IVORY)
    img = Image.open(shot_path).convert("RGB")
    if crop:
        img = img.crop(crop)
    img = fit(img, RW - 220, RH - 140)
    frame_shadowed(stage, img, (RW - img.width) // 2, (RH - img.height) // 2)
    png = TMP / f"{name}.png"
    stage.save(png)
    seg = TMP / f"{name}.mp4"
    zoom = ("scale=3840:-2,zoompan=z='min(zoom+0.00055,1.10)':d=%d:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" % int(seconds * FPS))
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", str(seconds),
         "-vf", zoom, "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(seg)])
    return seg, seconds


def rec_seg(name, src, t0, t1, crop=None, speed=1.0):
    """Trim a live session recording; optional punch-in crop and speed-up."""
    seg = TMP / f"{name}.mp4"
    vf = []
    if crop:
        vf.append(f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}")
    vf.append("scale=1920:1080")
    if speed != 1.0:
        vf.append(f"setpts=PTS/{speed}")
    vf.append("fps=30")
    run(["ffmpeg", "-y", "-ss", str(t0), "-t", str(round(t1 - t0, 3)), "-i", str(src),
         "-vf", ",".join(vf), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(seg)])
    return seg, round(dur_of(seg), 3)


def lower_third(text):
    """Translucent ivory chip with eyebrow text, for film overlays (CJK-capable)."""
    from showrunner.subtitle_render import _font as cjk_font
    f = cjk_font(26)
    tmp = Image.new("RGBA", (10, 10))
    dl = ImageDraw.Draw(tmp)
    trk = 6
    wdt = int(sum(dl.textlength(c, font=f) + trk for c in text.upper()) - trk)
    pad = 34
    chip = Image.new("RGBA", (wdt + pad * 2, 92), (14, 17, 24, 226))
    d = ImageDraw.Draw(chip)
    d.line([0, 0, chip.width, 0], fill=(*ACCENT, 255), width=3)
    x = pad
    for ch in text.upper():
        d.text((x, 28), ch, font=f, fill=(*INK, 255))
        x += d.textlength(ch, font=f) + trk
    return chip


def film_seg(name, src, seconds, caption, start=0):
    """Drama footage, native audio kept, editorial lower-third fades in."""
    chip = lower_third(caption)
    chip_png = TMP / f"{name}_chip.png"
    chip.save(chip_png)
    seg = TMP / f"{name}.mp4"
    fc = ("[0:v]scale=-2:1080,pad=1920:1080:(ow-iw)/2:0:color=0x0a0c11[bg];"
          "[1:v]format=rgba,fade=t=in:st=0.8:d=0.6:alpha=1[chip];"
          "[bg][chip]overlay=64:H-160[v]")
    run(["ffmpeg", "-y", "-ss", str(start), "-i", str(src), "-loop", "1", "-i", str(chip_png),
         "-t", str(seconds), "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
         "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ar", "44100", "-ac", "2", str(seg)])
    return seg, seconds


# ---------------- music bed ----------------
def music_bed(seconds):
    """Dark-ambient drone: detuned minor stack, slow tremolos, soft brown noise, echo."""
    out = TMP / "music.wav"
    fc = ("sine=frequency=55:duration={d}[s1];"
          "sine=frequency=110:duration={d},tremolo=f=0.11:d=0.7[s2];"
          "sine=frequency=130.81:duration={d},tremolo=f=0.10:d=0.8[s3];"
          "sine=frequency=164.81:duration={d},tremolo=f=0.12:d=0.75[s4];"
          "sine=frequency=220:duration={d},tremolo=f=0.13:d=0.6[s5];"
          "anoisesrc=color=brown:duration={d},lowpass=f=320[nz];"
          "sine=frequency=55:duration={d},tremolo=f=1.7:d=0.95[pl];"
          "[s1][s2][s3][s4][s5][nz][pl]amix=inputs=7:"
          "weights='0.9 1.0 0.62 0.55 0.3 0.5 0.55',"
          "lowpass=f=1400,aecho=0.7:0.55:410|780:0.24|0.16,"
          "afade=t=in:d=3,afade=t=out:st={fo}:d=4,volume=5.0[a]").format(
              d=seconds + 1, fo=seconds - 4)
    run(["ffmpeg", "-y", "-filter_complex", fc, "-map", "[a]",
         "-ar", "44100", "-ac", "2", "-t", str(seconds), str(out)])
    return out


# ---------------- assembly ----------------
def main():
    no_vo = "--no-vo" in sys.argv
    TMP.mkdir(parents=True, exist_ok=True)
    vo = {} if no_vo else make_vo()
    vd = {k: dur_of(p) for k, p in vo.items()}

    REC = OUT / "_rec"
    segs = []   # (path, dur, vo_key_starting_here)

    def add(path_dur, key=None):
        segs.append((*path_dur, key))

    # cold open, then a LIVE session end to end — Manus-launch pacing
    add(card_seg("open", 2.8, "One line in — a finished vertical drama out",
                 "AI Showrunner", "a live session · nothing staged"), "open")
    add(rec_seg("liv_create", REC / "create.webm", 0.3, 6.8), "brief")
    add(rec_seg("liv_estimate", REC / "create.webm", 6.0, 9.4,
                crop=(120, 282, 1200, 675)))
    add(card_seg("c_script", 1.8, "Live", "The script",
                 "four beats · approved by a human"), "script")
    add(rec_seg("liv_bible", REC / "run.webm", 0.6, 4.2))
    add(rec_seg("liv_shots", REC / "run.webm", 4.2, 8.6), "shoot")
    add(rec_seg("liv_qa", REC / "run.webm", 7.6, 11.8, crop=(300, 0, 1200, 675)))
    add(card_seg("c_cast", 1.8, "Live", "The cast",
                 "one locked portrait — every shot"), "cast")
    add(ui_seg("ui_cast", GAL / "05_the_cast.png", 5.6, crop=(0, 130, 1920, 1210)))
    add(card_seg("c_final", 1.8, "Live", "The final cut",
                 "zh · en · es from one master script"), "final")
    add(rec_seg("liv_final", REC / "final.webm", 0.5, 6.0))
    add(rec_seg("liv_player", REC / "final.webm", 6.0, 13.5,
                crop=(188, 138, 960, 540)))
    add(rec_seg("liv_wall", REC / "wall.webm", 0.3, 6.9, speed=1.35))
    add(film_seg("film_night", RUNS / "20260706-110141/final.mp4", 6,
                 "夜班替身 · generated / judged / cut by the system"), "film1")
    add(film_seg("film_alibi", RUNS / "20260706-023130/final.mp4", 5,
                 "完美不在场 · bilingual burn-in"))
    add(film_seg("film_loop", RUNS / "20260706-103834/final.mp4", 4.5,
                 "the sandbox loop · locked cast, same face"))
    add(card_seg("close", max(4.2, vd.get("close", 0) + 1.8),
                 "github.com/Yanjin-ai/showrunner", "Built on QwenCloud",
                 "narrated by qwen3-tts · every frame by the system",
                 closing=True), "close")

    # ---- xfade chain (video) + start-time bookkeeping ----
    starts = []
    cum = 0.0
    for i, (_p, dur, _k) in enumerate(segs):
        starts.append(cum)
        cum += dur - (XF if i < len(segs) - 1 else 0)
    total = cum
    inputs = []
    for p, _d, _k in segs:
        inputs += ["-i", str(p)]
    fc, prev = [], "0:v"
    for i in range(1, len(segs)):
        off = starts[i]
        lab = f"v{i}"
        fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[{lab}]")
        prev = lab
    video_fc = ";".join(fc)

    # ---- audio: music bed + film native audio + narration ----
    bed = music_bed(total)
    a_inputs = ["-i", str(bed)]
    a_fc, mixes = [], ["[bed]"]
    a_fc.append("[0:a]volume=0.42[bed]")
    ai = 1
    for i, (p, d, _k) in enumerate(segs):
        if Path(p).name.startswith("film_"):
            a_inputs += ["-i", str(p)]
            a_fc.append(f"[{ai}:a]volume=0.9,adelay={int(starts[i]*1000)}|{int(starts[i]*1000)},"
                        f"afade=t=in:st={starts[i]:.2f}:d=0.5[fa{i}]")
            mixes.append(f"[fa{i}]")
            ai += 1
    prev_end = 0.0   # narration never overlaps itself: late lines queue up
    for i, (_p, _d, k) in enumerate(segs):
        if k and k in vo:
            a_inputs += ["-i", str(vo[k])]
            start = max(starts[i] + 0.55, prev_end + 0.35)
            prev_end = start + vd[k]
            delay = int(start * 1000)
            a_fc.append(f"[{ai}:a]volume=1.0,adelay={delay}|{delay}[vo{i}]")
            mixes.append(f"[vo{i}]")
            ai += 1
    a_fc.append("".join(mixes) + f"amix=inputs={len(mixes)}:normalize=0,"
                "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    audio_fc = ";".join(a_fc)

    audio = TMP / "audio.m4a"
    run(["ffmpeg", "-y", *a_inputs, "-filter_complex", audio_fc, "-map", "[aout]",
         "-c:a", "aac", "-ar", "44100", "-t", str(total), str(audio)])

    silent = TMP / "video.mp4"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", video_fc, "-map", f"[{prev}]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    final = OUT / "demo_reel.mp4"
    run(["ffmpeg", "-y", "-i", str(silent), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", str(final)])
    print(f"film: {final}  ({total:.1f}s, {len(segs)} segments)")


if __name__ == "__main__":
    main()
