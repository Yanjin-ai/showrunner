"""Central config. All env-driven so the smoke test can correct model IDs fast."""
import os
from dotenv import load_dotenv

load_dotenv()


def _req(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var {key}. Copy .env.example -> .env and fill it in.")
    return val


API_KEY = _req("DASHSCOPE_API_KEY")

QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
VIDEO_BASE_URL = os.getenv("VIDEO_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")

PLANNER_MODEL = os.getenv("QWEN_PLANNER_MODEL", "qwen3.7-max")
FAST_MODEL = os.getenv("QWEN_FAST_MODEL", "qwen3.7-plus")
VL_MODEL = os.getenv("QWEN_VL_MODEL", "qwen3.6-plus")

T2V_MODEL = os.getenv("VIDEO_T2V_MODEL", "wan2.7-t2v")
I2V_MODEL = os.getenv("VIDEO_I2V_MODEL", "wan2.7-i2v")

# New modalities (all confirmed available on QwenCloud; exact API shapes to be probed with quota)
IMAGE_MODEL = os.getenv("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")
TTS_MODEL = os.getenv("QWEN_TTS_MODEL", "qwen3-tts-flash")  # validated live 2026-07-20

# Vertical short-drama defaults
RESOLUTION = "1080P"
ASPECT_RATIO = "9:16"
SHOT_DURATION = 5  # seconds per clip (2-15 allowed)
