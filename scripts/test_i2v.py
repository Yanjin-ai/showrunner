"""Confirm wan2.7-i2v schema: media=[{type:first_frame, url:...}]. Test URL vs data URI."""
import base64, time, httpx
from pathlib import Path
from showrunner import config

FRAME = "runs/20260706-023130/shots/s1_sh0_try2.frame.png"
PUBLIC = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"
SUBMIT = f"{config.VIDEO_BASE_URL}/services/aigc/video-generation/video-synthesis"
H = {"Authorization": f"Bearer {config.API_KEY}", "Content-Type": "application/json",
     "X-DashScope-Async": "enable"}


def submit(url, tag):
    body = {"model": config.I2V_MODEL,
            "input": {"prompt": "the subject slowly turns toward camera, subtle push-in, cinematic",
                      "media": [{"type": "first_frame", "url": url}]},
            "parameters": {"resolution": "1080P", "duration": 3}}
    r = httpx.post(SUBMIT, headers=H, json=body, timeout=60)
    print(f"[{tag}] HTTP {r.status_code}: {r.text[:160]}")
    return r.json().get("output", {}).get("task_id") if r.status_code == 200 else None


datauri = "data:image/png;base64," + base64.b64encode(Path(FRAME).read_bytes()).decode()
tasks = {"public-url": submit(PUBLIC, "public-url"), "data-uri": submit(datauri, "data-uri")}

for _ in range(8):
    time.sleep(15)
    for tag, tid in list(tasks.items()):
        if not tid:
            continue
        o = httpx.get(f"{config.VIDEO_BASE_URL}/tasks/{tid}",
                      headers={"Authorization": f"Bearer {config.API_KEY}"}, timeout=60).json().get("output", {})
        print(f"[{tag}] {o.get('task_status')} {o.get('code','')} {o.get('message','')[:70]}")
        if o.get("task_status") in ("SUCCEEDED", "FAILED"):
            if o.get("task_status") == "SUCCEEDED":
                print(f"  >>> {tag} WORKS  video={o.get('video_url')}")
            tasks[tag] = None
