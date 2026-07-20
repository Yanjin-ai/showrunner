"""Qwen-Image: locked character portraits (T2I) + I2I first-frames.

⚠️ NEEDS-VALIDATION: the exact DashScope endpoint/body for qwen-image-2.0-pro must be probed
with quota (the way the i2v `media` protocol was). The INTERFACE below is stable and what the
pipeline wires to — only the raw request/response fields may need a small fix after probing.
Async task pattern (submit → poll → download) mirrors video."""
import time
import httpx
from pathlib import Path
from showrunner import config, cost

_BASE = config.VIDEO_BASE_URL
_SUBMIT = f"{_BASE}/services/aigc/text2image/image-synthesis"   # TODO(validate) may be multimodal-generation
_HEADERS = {"Authorization": f"Bearer {config.API_KEY}", "Content-Type": "application/json"}
SIZE = "1080*1920"


def _run_task(body: dict, dest) -> Path:
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.post(_SUBMIT, headers={**_HEADERS, "X-DashScope-Async": "enable"}, json=body, timeout=120)
    r.raise_for_status()
    task_id = r.json().get("output", {}).get("task_id")
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        o = httpx.get(f"{_BASE}/tasks/{task_id}", headers=_HEADERS, timeout=60).json().get("output", {})
        if o.get("task_status") == "SUCCEEDED":
            results = o.get("results") or [{}]
            url = results[0].get("url") or o.get("image_url")   # TODO(validate) result path
            with httpx.stream("GET", url, timeout=120) as resp:
                resp.raise_for_status()
                dest.write_bytes(b"".join(resp.iter_bytes()))
            return dest
        if o.get("task_status") == "FAILED":
            raise RuntimeError(f"image task FAILED: {o.get('message')}")
        time.sleep(4)
    raise TimeoutError("image task timed out")


def portrait(prompt: str, dest, *, model: str | None = None) -> Path:
    """T2I locked character portrait (vertical)."""
    cost.current.image(1)
    body = {"model": model or config.IMAGE_MODEL, "input": {"prompt": prompt},
            "parameters": {"size": SIZE, "n": 1}}
    return _run_task(body, dest)


def first_frame(ref_image_url: str, prompt: str, dest, *, model: str | None = None) -> Path:
    """I2I: keep the character from ref, restage per prompt → a shot's first frame.
    ref_image_url may be an http(s) URL or a data: URI (as i2v accepts)."""
    cost.current.image(1)
    body = {"model": model or config.IMAGE_MODEL,
            "input": {"prompt": prompt, "images": [ref_image_url]},   # TODO(validate) field name
            "parameters": {"size": SIZE, "n": 1}}
    return _run_task(body, dest)
