"""Character-consistency engine (optional 'i2v' mode).

Mints one canonical reference frame per character (a clean portrait via t2v, then a
still), and reuses it as the wan2.7 i2v first_frame so a character keeps the same face,
wardrobe and build across shots. Confirmed: the media url accepts a data: URI, so refs are
kept locally — no object storage needed."""
from pathlib import Path

from showrunner import config, ffmpeg_utils, images, assetlib
from showrunner.clients import video
from showrunner.schemas import CharacterCard, StoryBible, ShotSpec, CharacterAsset


def _datauri(png_path) -> str:
    # 1080-wide JPEG keeps the first_frame crisp while staying small enough to upload reliably.
    return images.to_datauri(png_path, max_w=1080, quality=88)


class ConsistencyManager:
    """Library-aware. Reuses a character's LOCKED portrait from the asset library if it exists
    (→ same face across runs, continuable production); otherwise mints one and saves it back."""

    def __init__(self, bible: StoryBible, run_dir, style: str, log=lambda **k: None, run_id: str = ""):
        self.bible = bible
        self.d = Path(run_dir)
        self.style = style
        self.log = log
        self.run_id = run_id
        self.refs: dict[str, str] = {}  # character id -> reference frame as data URI

    def mint_all(self, shots: list[ShotSpec]):
        """Ensure a reference for every character that appears (reuse from library, or mint once)."""
        present = {cid for s in shots for cid in s.characters_present}
        for c in self.bible.characters:
            if c.id in present:
                self._ensure(c)

    def _ensure(self, char: CharacterCard):
        if char.id in self.refs:
            return
        # 0) a ref this run already minted (resume/regen): reuse it so the face matches
        #    the run's existing shots exactly
        local = self.d / "refs" / f"{char.id}.png"
        if local.exists():
            self.refs[char.id] = _datauri(local)
            self.log(stage="ref_reused_run", character=char.id)
            return
        # 1) reuse a locked portrait from the persistent library if present
        saved = assetlib.get_character(char.id)
        if saved and saved.portrait_path and Path(saved.portrait_path).exists():
            self.refs[char.id] = _datauri(saved.portrait_path)
            self.log(stage="ref_reused", character=char.id)
            return
        # 2) otherwise mint a portrait, then lock it into the library for future reuse
        prompt = (f"Vertical 9:16 portrait. {self.style}. Clean medium close-up establishing shot of "
                  f"{char.name}: {char.appearance}. Neutral confident expression, facing camera, "
                  f"centered, sharp focus, even cinematic lighting, minimal motion.")
        try:
            clip = video.generate(prompt, self.d / "refs" / f"{char.id}.mp4",
                                  model=config.T2V_MODEL, duration=3)
            frame = ffmpeg_utils.extract_frame(clip, self.d / "refs" / f"{char.id}.png", from_end=1.0)
            self.refs[char.id] = _datauri(frame)
            assetlib.save_character(
                CharacterAsset(id=char.id, name=char.name, appearance=char.appearance,
                               origin_run=self.run_id), portrait_src=frame)
            self.log(stage="ref_minted", character=char.id)
        except Exception as e:
            self.log(stage="ref_fail", character=char.id, error=str(e)[:120])

    def ref_for_shot(self, shot: ShotSpec) -> str | None:
        """Reference of the shot's primary present character, if any."""
        for cid in shot.characters_present:
            if cid in self.refs:
                return self.refs[cid]
        return None
