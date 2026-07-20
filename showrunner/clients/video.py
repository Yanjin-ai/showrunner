"""HappyHorse / Wan async video generation: submit task -> poll -> download.

DashScope video synthesis is asynchronous: POST creates a task (requires the
X-DashScope-Async header), then you GET /tasks/{id} until SUCCEEDED. Output URLs
expire in 24h, so we download to disk immediately."""
import time
import httpx
from pathlib import Path
from showrunner import config, cost

_SUBMIT = f"{config.VIDEO_BASE_URL}/services/aigc/video-generation/video-synthesis"
_TASK = f"{config.VIDEO_BASE_URL}/tasks/{{task_id}}"
_HEADERS = {"Authorization": f"Bearer {config.API_KEY}", "Content-Type": "application/json"}


def submit(prompt: str, *, model: str | None = None, image_url: str | None = None,
           negative_prompt: str = "", duration: int = config.SHOT_DURATION,
           resolution: str = config.RESOLUTION, ratio: str = config.ASPECT_RATIO) -> str:
    """Create a generation task, return task_id.

    i2v when image_url is given: wan2.7 takes the reference under
    input.media=[{type:first_frame,url:...}] (url may be an http(s) URL or a data: URI).
    The first_frame sets the aspect ratio, so `ratio` is only sent for t2v."""
    model = model or (config.I2V_MODEL if image_url else config.T2V_MODEL)
    inp: dict = {"prompt": prompt}
    if negative_prompt:
        inp["negative_prompt"] = negative_prompt
    params: dict = {"resolution": resolution, "duration": duration}
    if image_url:
        inp["media"] = [{"type": "first_frame", "url": image_url}]
    else:
        params["ratio"] = ratio
    body = {"model": model, "input": inp, "parameters": params}
    headers = {**_HEADERS, "X-DashScope-Async": "enable"}
    # The i2v body carries a base64 reference image; give it a generous write timeout and
    # retry transient network errors so parallel submits don't drop shots.
    last = None
    for attempt in range(3):
        try:
            r = httpx.post(_SUBMIT, headers=headers, json=body, timeout=180)
            r.raise_for_status()
            task_id = r.json().get("output", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"No task_id in response: {r.text[:200]}")
            cost.current.video(1)  # meter each generation (video is the budget sink)
            return task_id
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"submit failed after retries: {last}")


def poll(task_id: str, *, interval: int = 8, timeout: int = 900) -> str:
    """Poll until SUCCEEDED; return the video URL. Transient GET errors don't abort polling."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(_TASK.format(task_id=task_id), headers=_HEADERS, timeout=60)
            r.raise_for_status()
        except (httpx.TimeoutException, httpx.TransportError):
            time.sleep(interval)
            continue
        out = r.json().get("output", {})
        status = out.get("task_status")
        if status == "SUCCEEDED":
            url = out.get("video_url") or out.get("results", [{}])[0].get("url")
            if not url:
                raise RuntimeError(f"SUCCEEDED but no video_url: {out}")
            return url
        if status == "FAILED":
            raise RuntimeError(f"Task {task_id} FAILED: {out.get('message')}")
        time.sleep(interval)
    raise TimeoutError(f"Task {task_id} did not finish within {timeout}s")


def download(url: str, dest: str | Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(3):
        try:
            with httpx.stream("GET", url, timeout=300) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            return dest
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"download failed after retries: {last}")


def generate(prompt: str, dest: str | Path, **kw) -> Path:
    """Convenience: submit -> poll -> download to dest."""
    task_id = submit(prompt, **kw)
    url = poll(task_id)
    return download(url, dest)
