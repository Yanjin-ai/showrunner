"""Qwen-TTS: character dialogue + narration + multilingual dubbing.

⚠️ NEEDS-VALIDATION: exact DashScope qwen-tts request/response shape to be probed with quota.
Interface is stable (the pipeline calls `synthesize(text, voice, lang) -> wav path`); only the
raw HTTP body/return field may need a small fix after probing.

Voices power both per-character dialogue and one-click English dubbing (bidirectional market)."""
import time
import httpx
from pathlib import Path
from showrunner import config, cost

_BASE = config.VIDEO_BASE_URL
_SUBMIT = f"{_BASE}/services/aigc/multimodal-generation/generation"   # TODO(validate) may be a tts-specific path
_HEADERS = {"Authorization": f"Bearer {config.API_KEY}", "Content-Type": "application/json"}

# a few default Qwen-TTS voices per language (placeholders; confirm names on QwenCloud)
DEFAULT_VOICE = {"zh": "qwen-tts-zhichu", "en": "qwen-tts-eric", "es": "qwen-tts-sofia"}


def synthesize(text: str, dest, *, voice: str | None = None, lang: str = "zh",
               model: str | None = None) -> Path:
    """Text → wav/mp3 file for a character line or narration."""
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    cost.current.tts(len(text))
    voice = voice or DEFAULT_VOICE.get(lang, DEFAULT_VOICE["en"])
    body = {"model": model or config.TTS_MODEL,
            "input": {"text": text, "voice": voice},   # TODO(validate) field names
            "parameters": {"format": "wav"}}
    r = httpx.post(_SUBMIT, headers=_HEADERS, json=body, timeout=120)
    r.raise_for_status()
    out = r.json().get("output", {})
    url = out.get("audio", {}).get("url") or out.get("audio_url")   # TODO(validate) return path
    if not url:
        raise RuntimeError(f"TTS: no audio url in response: {r.text[:200]}")
    with httpx.stream("GET", url, timeout=120) as resp:
        resp.raise_for_status()
        dest.write_bytes(b"".join(resp.iter_bytes()))
    return dest
