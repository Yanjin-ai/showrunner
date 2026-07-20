"""PromptWriter: ShotSpec + bible -> VideoGenRequest.

Consistency strategy (default, always works): bake each present character's dense
appearance descriptors into every prompt, plus the global style sheet. This gives strong
text-level continuity without needing a public reference-image URL. If an image uploader is
available, the orchestrator upgrades this to image-to-video with a shared reference frame."""
from showrunner.schemas import StoryBible, ShotSpec, VideoGenRequest

NEG = ("blurry, low quality, flickering, distorted face, deformed hands, extra limbs, "
       "warped anatomy, watermark, text artifacts, subtitles, jitter, morphing")

# Two-tier camera control (industry pattern: presets for speed, prose for precision).
# Keys are stable identifiers the UI/API can send; values are the cinematic phrases the
# video model actually understands.
CAMERA_PRESETS = {
    "static": "locked-off static camera",
    "push_in": "slow dolly push-in toward the subject",
    "pull_out": "slow dolly pull-back revealing the space",
    "handheld": "subtle handheld camera, documentary energy",
    "pan_left": "smooth pan left",
    "pan_right": "smooth pan right",
    "tilt_up": "slow tilt up",
    "tilt_down": "slow tilt down",
    "crane_up": "crane rising above the subject",
    "orbit": "slow orbit around the subject",
    "dolly_zoom": "dolly zoom (vertigo effect) on the subject",
    "whip": "fast whip pan transition",
}


def camera_text(value: str) -> str:
    """Resolve a preset key to its phrase; free text passes through unchanged."""
    return CAMERA_PRESETS.get(value, value)


def write(shot: ShotSpec, bible: StoryBible, *, ref_image_url: str | None = None,
          revision_advice: str = "") -> VideoGenRequest:
    char_map = {c.id: c for c in bible.characters}
    who = [char_map[cid] for cid in shot.characters_present if cid in char_map]
    char_desc = " | ".join(f"{c.name}: {c.appearance}" for c in who) or "no characters, empty scene"

    parts = [
        f"Vertical 9:16 cinematic short-drama shot. Style: {bible.style}.",
        f"Shot size: {shot.shot_size}. Camera: {camera_text(shot.camera)}.",
        f"Characters — {char_desc}.",
        f"Action: {shot.action}. Emotion: {shot.emotion}.",
    ]
    if shot.continuity:
        parts.append(f"Continuity to preserve: {shot.continuity}.")
    if revision_advice:
        parts.append(f"IMPORTANT FIX: {revision_advice}.")
    prompt = " ".join(parts)

    return VideoGenRequest(
        shot_id=shot.id,
        mode="i2v" if ref_image_url else "t2v",
        prompt=prompt,
        negative_prompt=NEG,
        ref_image_path=ref_image_url,
        duration=shot.duration,
    )
