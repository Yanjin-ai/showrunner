"""Alibaba Cloud service map — every cloud call in AI Showrunner goes through here.

════════════════════════════════════════════════════════════════════════════════
 PROOF OF ALIBABA CLOUD USAGE  (submission evidence file)
════════════════════════════════════════════════════════════════════════════════

All generative work runs on Alibaba Cloud Model Studio (DashScope, intl region),
and the backend itself is hosted on Alibaba Cloud ECS (ap-southeast-1, Singapore).

┌────────────────────────┬──────────────────────────────┬──────────────────────┐
│ Alibaba Cloud service  │ What we use it for           │ Client module        │
├────────────────────────┼──────────────────────────────┼──────────────────────┤
│ Qwen3.7-Max            │ planner · storyboard ·       │ clients/qwen.py      │
│  (Model Studio, LLM)   │ multi-language localization  │  chat()              │
│ Qwen-VL (qwen3.6-plus) │ the critic: scores 3 frames  │ clients/qwen.py      │
│  (vision-language)     │ per take (na / cc / tq)      │  chat_vl()           │
│ Wan2.7 t2v / i2v       │ every shot's video; i2v      │ clients/video.py     │
│  (video synthesis)     │ first_frame = locked cast    │  generate()          │
│ Qwen3-TTS (flash)      │ narration & dubbing voices   │ clients/tts.py       │
│ Qwen-Image (wired)     │ Frame Gate stills, portraits │ clients/image.py     │
│ ECS ap-southeast-1     │ hosts this FastAPI backend   │ deploy/deploy.sh     │
│                        │ (systemd + nginx)            │ deploy/*.service     │
└────────────────────────┴──────────────────────────────┴──────────────────────┘

Endpoints (see showrunner/config.py):
  text/VL   https://dashscope-intl.aliyuncs.com/compatible-mode/v1   (OpenAI-style)
  video/TTS https://dashscope-intl.aliyuncs.com/api/v1               (native async:
            POST + X-DashScope-Async → poll /tasks/{id} → download within 24h)

Runtime proof: GET /healthz on the deployed backend returns the ECS instance-id
and region read from Alibaba Cloud's on-instance metadata service
(http://100.100.100.200/latest/meta-data/) — the server attests to where it runs.

Every call is metered through showrunner/cost.py (budget admission control), and
every artifact the cloud returns is persisted as replayable JSON under runs/.
"""
from . import qwen, video, tts, image  # noqa: F401  (re-export the service clients)
