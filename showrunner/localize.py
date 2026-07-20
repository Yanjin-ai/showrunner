"""Multi-language localization — the value differentiator.

One master script -> subtitle cue tracks in N languages. Timings come from shot order and
durations (each shot occupies a contiguous slot on the final timeline)."""
from showrunner.clients import qwen
from showrunner.schemas import ShotSpec, SubtitleTrack

LANG_NAMES = {"zh": "Chinese", "en": "English", "es": "Spanish", "ja": "Japanese",
              "ko": "Korean", "pt": "Portuguese", "id": "Indonesian", "ar": "Arabic"}


def _timeline(shots: list[ShotSpec]) -> list[dict]:
    """Contiguous [start,end] per shot on the concatenated master."""
    out, t = [], 0.0
    for sh in shots:
        out.append({"shot_id": sh.id, "start": t, "end": t + sh.duration, "text": sh.dialogue})
        t += sh.duration
    return out


def build_tracks(shots: list[ShotSpec], langs: list[str], master_lang: str = "zh") -> list[SubtitleTrack]:
    base = _timeline(shots)
    dialogues = [b["text"] for b in base]
    tracks: list[SubtitleTrack] = []
    for lang in langs:
        if lang == master_lang:
            texts = dialogues
        else:
            texts = _translate(dialogues, LANG_NAMES.get(lang, lang))
        cues = [{"start": b["start"], "end": b["end"], "text": t}
                for b, t in zip(base, texts)]
        tracks.append(SubtitleTrack(lang=lang, cues=cues))
    return tracks


def _translate(lines: list[str], target_lang: str) -> list[str]:
    numbered = "\n".join(f"{i}. {ln or '(no line)'}" for i, ln in enumerate(lines))
    out = qwen.chat_json(
        f"Translate each numbered short-drama subtitle line to {target_lang}. Keep it punchy and "
        f"natural for on-screen subtitles, preserve line count.\n{numbered}\n"
        f'Return JSON: {{"lines": ["...", ...]}} with exactly {len(lines)} entries.',
        system="You are a subtitle localizer for streaming short dramas.",
    )
    res = out.get("lines", [])
    # pad/truncate defensively so cue count always matches
    if len(res) < len(lines):
        res += [""] * (len(lines) - len(res))
    return [("" if ln in ("(no line)", None) else ln) for ln in res[:len(lines)]]
