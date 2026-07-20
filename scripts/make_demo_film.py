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

from scripts.make_devpost_assets import (IVORY, INK, ACCENT, HAIR, MUTE,
                                         serif, sans, fit, frame_shadowed)

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
    f_h = serif(110)
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


def lower_third(text):
    """Translucent ivory chip with eyebrow text, for film overlays (CJK-capable)."""
    from showrunner.subtitle_render import _font as cjk_font
    f = cjk_font(26)
    tmp = Image.new("RGBA", (10, 10))
    dl = ImageDraw.Draw(tmp)
    trk = 6
    wdt = int(sum(dl.textlength(c, font=f) + trk for c in text.upper()) - trk)
    pad = 34
    chip = Image.new("RGBA", (wdt + pad * 2, 92), (245, 242, 235, 216))
    d = ImageDraw.Draw(chip)
    d.line([0, 0, chip.width, 0], fill=(*INK, 255), width=2)
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
          "[s1][s2][s3][s4][s5][nz]amix=inputs=6:weights='0.9 1.0 0.62 0.55 0.3 0.5',"
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

    def content_len(base, *keys, card=2.6):
        """Content segment stretches so the chapter's VO fits (card + content)."""
        need = sum(vd.get(k, 0) for k in keys)
        return max(base, need - card + 1.4)

    segs = []   # (path, dur, vo_key_starting_here)
    segs.append((*card_seg("open", 3.6, "One line in — a finished vertical drama out",
                           "AI Showrunner", "a virtual production studio on QwenCloud"), "open"))
    segs.append((*card_seg("c1", 2.6, "Chapter 01", "The brief",
                           "price shown before a single frame is rendered"), "brief"))
    segs.append((*ui_seg("ui_create", SRC / "fresh_create.png",
                         content_len(4.5, "brief"), crop=(0, 0, 1800, 800)), None))
    segs.append((*card_seg("c2", 2.6, "Chapter 02", "The script",
                           "four beats · story bible · human approval gates"), "script"))
    segs.append((*ui_seg("ui_bible", SRC / "fresh_bible_110141.png",
                         content_len(4.5, "script"), crop=(0, 0, 1800, 924)), None))
    segs.append((*card_seg("c3", 2.6, "Chapter 03", "The cast",
                           "one locked portrait drives every shot"), "cast"))
    segs.append((*ui_seg("ui_cast", GAL / "05_the_cast.png",
                         content_len(4.2, "cast"), crop=(0, 130, 1920, 1210)), None))
    segs.append((*card_seg("c4", 2.6, "Chapter 04", "The shoot",
                           "Wan2.7 renders — Qwen-VL judges every take"), "shoot"))
    segs.append((*ui_seg("ui_shots", SRC / "fresh_shots_023130.png",
                         content_len(4.5, "shoot"), crop=(0, 0, 1800, 984)), None))
    segs.append((*film_seg("film_night", RUNS / "20260706-110141/final.mp4",
                           max(11, vd.get("film1", 0) + 4),
                           "夜班替身 · generated / judged / cut by the system"), "film1"))
    segs.append((*card_seg("c5", 2.6, "Chapter 05", "The final cut",
                           "bilingual burn-in · zh/en/es tracks · AIGC label"), "final"))
    segs.append((*ui_seg("ui_final", SRC / "fresh_final_110141.png",
                         content_len(4.0, "final"), crop=(0, 0, 1800, 700)), None))
    segs.append((*film_seg("film_alibi", RUNS / "20260706-023130/final.mp4", 9,
                           "完美不在场 · bilingual burned subtitles"), None))
    segs.append((*film_seg("film_loop", RUNS / "20260706-103834/final.mp4", 6,
                           "the sandbox loop · consistency 9/10 via locked cast"), None))
    segs.append((*card_seg("close", max(4.2, vd.get("close", 0) + 1.8),
                           "github.com/Yanjin-ai/showrunner", "Built on QwenCloud",
                           "narrated by qwen3-tts · Qwen3.7-Max · Qwen-VL · Wan2.7",
                           closing=True), "close"))

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
    for i, (_p, _d, k) in enumerate(segs):
        if k and k in vo:
            a_inputs += ["-i", str(vo[k])]
            delay = int((starts[i] + 0.55) * 1000)
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
