"""Critic: score a generated clip against its ShotSpec using Qwen-VL on a sampled frame.

This is the headline loop — it turns 'prompt -> video' into a self-correcting system.
Bounded to keep cost sane; the orchestrator decides retries from `passed` + `revision_advice`."""
import subprocess
from pathlib import Path
from showrunner.clients import qwen
from showrunner import ffmpeg_utils, images
from showrunner.schemas import ShotSpec, StoryBible, QAReport


def precheck(video_path, expected_duration: int | None = None) -> dict:
    """Tier-0 quality gate: free deterministic checks BEFORE spending VL tokens
    (Netflix VVS pattern — never pay for perceptual scoring on a clip that fails spec).
    Checks: file exists/non-trivial, decodable video stream, sane duration, not near-black."""
    p = Path(video_path)
    if not p.exists() or p.stat().st_size < 50_000:
        return {"ok": False, "reason": "file missing or implausibly small"}
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True)
    lines = [l for l in probe.stdout.splitlines() if l.strip()]
    if probe.returncode != 0 or not lines:
        return {"ok": False, "reason": "no decodable video stream"}
    try:
        dur = float(lines[-1].split(",")[0])
    except (ValueError, IndexError):
        dur = 0.0
    if expected_duration and dur < expected_duration * 0.5:
        return {"ok": False, "reason": f"duration {dur:.1f}s < half of requested {expected_duration}s"}
    # near-black detection: mean luma of a mid-clip frame
    luma = subprocess.run(
        ["ffmpeg", "-ss", str(max(dur / 2, 0.1)), "-i", str(p), "-frames:v", "1",
         "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"],
        capture_output=True, text=True)
    for line in luma.stderr.splitlines():
        if "YAVG" in line:
            try:
                if float(line.rsplit("=", 1)[1]) < 8.0:
                    return {"ok": False, "reason": "frame is near-black"}
            except ValueError:
                pass
            break
    return {"ok": True, "reason": ""}

# Per-axis thresholds. The critic now sees 3 frames (start/mid/end), so narrative can be
# judged on the actual motion — held to a fair bar alongside consistency/technical quality.
NA_MIN, CC_MIN, TQ_MIN = 5, 6, 6
PASS_THRESHOLD = CC_MIN  # shown to the model as the "below this needs advice" bar
N_FRAMES = 3

RUBRIC = """You are a strict QA reviewer for AI-generated short-drama clips. You are given
{n} frames sampled across the clip in order (start, middle, end). Judge the CLIP as a motion
sequence against the intended shot. Score 0-10 on each axis and be honest — low scores are useful.

INTENDED SHOT:
- action (should be visible as change across the frames): {action}
- emotion: {emotion}
- shot size: {shot_size} | camera: {camera}
- characters that must appear: {chars}

Return JSON:
{{"narrative_alignment": 0-10, "character_consistency": 0-10, "technical_quality": 0-10,
  "reason": "one sentence on the biggest problem or strength",
  "revision_advice": "a concrete, targeted prompt change if anything scored below {thr}, else empty"}}"""


def review(video_path, shot: ShotSpec, bible: StoryBible) -> QAReport:
    char_map = {c.id: c for c in bible.characters}
    chars = ", ".join(f"{char_map[c].name} ({char_map[c].appearance[:60]}...)"
                      for c in shot.characters_present if c in char_map) or "none"
    frames = ffmpeg_utils.extract_frames(video_path, Path(video_path).with_suffix(".frames"), n=N_FRAMES)
    data = [images.to_datauri(f, max_w=640, quality=82) for f in frames]
    scored = qwen.vision_json_multi(data, RUBRIC.format(
        n=N_FRAMES, action=shot.action, emotion=shot.emotion, shot_size=shot.shot_size,
        camera=shot.camera, chars=chars, thr=PASS_THRESHOLD))

    na = int(scored.get("narrative_alignment", 0))
    cc = int(scored.get("character_consistency", 0))
    tq = int(scored.get("technical_quality", 0))
    passed = na >= NA_MIN and cc >= CC_MIN and tq >= TQ_MIN
    return QAReport(
        shot_id=shot.id, narrative_alignment=na, character_consistency=cc, technical_quality=tq,
        passed=passed, reason=scored.get("reason", ""),
        revision_advice="" if passed else scored.get("revision_advice", ""),
    )
