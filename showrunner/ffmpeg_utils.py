"""Thin ffmpeg wrappers for the editor and critic. Requires ffmpeg on PATH."""
import subprocess
from pathlib import Path

W, H = 1080, 1920  # vertical 9:16


def _run(cmd: list[str], cwd: str | None = None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr[-800:]}")


def has_cues(srt) -> bool:
    p = Path(srt)
    return p.exists() and p.stat().st_size > 0


def extract_frame(video, out_png=None, from_end: float = 0.4) -> Path:
    """Grab a frame near the end of the clip (good for continuity checks)."""
    video = Path(video)
    out_png = Path(out_png) if out_png else video.with_suffix(".frame.png")
    _run(["ffmpeg", "-y", "-sseof", f"-{from_end}", "-i", str(video),
          "-update", "1", "-frames:v", "1", str(out_png)])
    return out_png


def _duration(video) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except (ValueError, AttributeError):
        return 5.0


def extract_frames(video, out_dir, n: int = 3) -> list[Path]:
    """Sample n frames evenly across the clip (start / middle / end)."""
    dur = _duration(video)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        t = max(0.0, dur * (i + 0.5) / n)
        p = out_dir / f"f{i}.png"
        _run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(p)])
        paths.append(p)
    return paths


def normalize(video, out) -> Path:
    """Force clips to identical 1080x1920 h264+aac so concat is seamless."""
    out = Path(out)
    _run(["ffmpeg", "-y", "-i", str(video),
          "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
          "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-shortest", str(out)])
    return out


def concat(videos: list, out) -> Path:
    out = Path(out)
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{Path(v).resolve()}'\n" for v in videos))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
          "-c", "copy", str(out)])
    return out


def _ts(sec: float) -> str:
    h, rem = divmod(sec, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s%1)*1000):03d}"


def write_srt(cues: list[dict], path) -> Path:
    """cues: [{start, end, text}] in seconds."""
    path = Path(path)
    lines = []
    for i, c in enumerate(cues, 1):
        if not c.get("text"):
            continue
        lines.append(f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{c['text']}\n")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def burn_overlay(video, slots: list[dict], out) -> Path:
    """Composite pre-rendered subtitle PNGs onto the video, each shown during its cue
    window. Uses the overlay filter (present) instead of subtitles (needs libass)."""
    video, out = Path(video).resolve(), Path(out).resolve()
    if not slots:
        _run(["ffmpeg", "-y", "-i", str(video), "-c", "copy", str(out)])
        return out
    cmd = ["ffmpeg", "-y", "-i", str(video)]
    for s in slots:
        cmd += ["-i", str(Path(s["png"]).resolve())]
    chain, last = [], "0:v"
    for i, s in enumerate(slots, start=1):
        lbl = f"v{i}"
        pos = {"tr": "W-w-24:24", "tl": "24:24"}.get(s.get("pos"), "(W-w)/2:H-h-70")
        enable = ("" if s.get("always")
                  else f":enable='between(t,{s['start']},{s['end']})'")
        chain.append(f"[{last}][{i}:v]overlay={pos}{enable}[{lbl}]")
        last = lbl
    cmd += ["-filter_complex", ";".join(chain), "-map", f"[{last}]", "-map", "0:a?",
            "-c:a", "copy", str(out)]
    _run(cmd)
    return out


# Implicit AIGC label (CN regulation): provenance embedded in container metadata.
AIGC_METADATA = ["-metadata", "comment=AIGC: AI-generated video (Qwen + Wan/HappyHorse via AI Showrunner)",
                 "-metadata", "encoded_by=AI Showrunner (AIGC)"]


def mux_soft_subs(video, srt_by_lang: dict, out) -> Path:
    """Embed selectable subtitle tracks (mov_text) + implicit AIGC provenance metadata.
    Empty tracks are dropped; if none remain the video is just copied so the pipeline
    never dies on missing dialogue."""
    out = Path(out)
    tracks = {l: s for l, s in srt_by_lang.items() if has_cues(s)}
    if not tracks:
        _run(["ffmpeg", "-y", "-i", str(video), "-c", "copy", *AIGC_METADATA, str(out)])
        return out
    cmd = ["ffmpeg", "-y", "-i", str(video)]
    for srt in tracks.values():
        cmd += ["-i", str(srt)]
    cmd += ["-map", "0:v", "-map", "0:a?"]
    for i, _ in enumerate(tracks, start=1):
        cmd += ["-map", str(i)]
    cmd += ["-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text"]
    for i, lang in enumerate(tracks):
        cmd += [f"-metadata:s:s:{i}", f"language={lang}"]
    cmd += [*AIGC_METADATA, str(out)]
    _run(cmd)
    return out


def mux_audio(video, audio, out) -> Path:
    """Replace/attach a voice track (from TTS). Video length wins."""
    out = Path(out)
    _run(["ffmpeg", "-y", "-i", str(video), "-i", str(audio),
          "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)])
    return out


def add_music(video, music, out, music_vol: float = 0.22) -> Path:
    """Duck a royalty-free music bed under whatever audio the video already has."""
    out = Path(out)
    has_audio = bool(_probe_streams(video, "a"))
    if has_audio:
        fc = f"[1:a]volume={music_vol}[m];[0:a][m]amix=inputs=2:duration=first[a]"
        maps = ["-map", "0:v", "-map", "[a]"]
    else:
        fc = f"[1:a]volume={music_vol}[a]"
        maps = ["-map", "0:v", "-map", "[a]"]
    _run(["ffmpeg", "-y", "-i", str(video), "-i", str(music),
          "-filter_complex", fc, *maps, "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)])
    return out


def _probe_streams(video, kind: str) -> list:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", kind,
                        "-show_entries", "stream=index", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def make_cover(video, out_png, title: str = "") -> Path:
    out_png = Path(out_png)
    frame = extract_frame(video, out_png.with_suffix(".raw.png"), from_end=1.0)
    if not title:
        return Path(frame).replace(out_png)
    safe = title.replace("'", "").replace(":", " ").replace("\\", " ")
    try:  # drawtext needs a usable font; fall back to the bare frame if it can't find one
        _run(["ffmpeg", "-y", "-i", str(frame),
              "-vf", f"drawtext=text='{safe}':fontcolor=white:fontsize=64:borderw=3:"
                     f"bordercolor=black:x=(w-tw)/2:y=h-220",
              str(out_png)])
    except RuntimeError:
        Path(frame).replace(out_png)
    return out_png
