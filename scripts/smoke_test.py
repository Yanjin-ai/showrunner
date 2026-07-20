"""Day-1 risk killer. Verifies the three unknowns before we build the pipeline:
  1. Qwen text model returns valid JSON
  2. Qwen-VL vision model reads an image
  3. Video model generates + downloads a clip end-to-end (async task/poll)

Run: python -m scripts.smoke_test
It also auto-detects which model IDs actually work if the defaults are rejected.
"""
import sys
from pathlib import Path
from showrunner import config
from showrunner.clients import qwen, video

OUT = Path("runs/smoke")
CANDIDATE_TEXT = ["qwen3.7-max", "qwen3.7-plus", "qwen-max", "qwen-plus"]
CANDIDATE_VL = ["qwen3.6-plus", "qwen-vl-max", "qwen-vl-plus"]
CANDIDATE_VIDEO = ["wan2.7-t2v", "happyhorse-1.1-t2v", "wan2.6-t2v", "wan2.2-t2v-plus"]
TEST_IMG = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"


def _try(label, fn):
    try:
        fn()
        print(f"  ✅ {label}")
        return True
    except Exception as e:
        print(f"  ❌ {label}: {type(e).__name__}: {str(e)[:200]}")
        return False


def test_text():
    print("[1/3] Qwen text -> JSON")
    for m in [config.PLANNER_MODEL, *CANDIDATE_TEXT]:
        try:
            out = qwen.chat_json('Return {"ok": true, "n": 3}', model=m)
            assert out.get("ok") is True
            print(f"  ✅ text model works: {m}  ->  {out}")
            return m
        except Exception as e:
            print(f"  ·  {m} failed: {str(e)[:120]}")
    print("  ❌ no text model worked"); return None


def test_vision():
    print("[2/3] Qwen-VL vision")
    for m in [config.VL_MODEL, *CANDIDATE_VL]:
        try:
            config.VL_MODEL = m
            cap = qwen.vision_caption(TEST_IMG, "Describe this image in one short sentence.")
            assert cap.strip()
            print(f"  ✅ VL model works: {m}  ->  {cap[:100]}")
            return m
        except Exception as e:
            print(f"  ·  {m} failed: {str(e)[:120]}")
    print("  ❌ no VL model worked"); return None


def test_video():
    print("[3/3] Video gen (async, ~1-5 min)")
    prompt = ("Vertical 9:16 cinematic noir. A woman in a trench coat turns sharply "
              "under a flickering streetlight, rain, cool teal-orange grade, subtle dolly-in.")
    for m in [config.T2V_MODEL, *CANDIDATE_VIDEO]:
        try:
            print(f"  ·  trying {m} ...")
            path = video.generate(prompt, OUT / f"smoke_{m}.mp4", model=m)
            print(f"  ✅ video model works: {m}  ->  {path} ({path.stat().st_size} bytes)")
            return m
        except Exception as e:
            print(f"  ·  {m} failed: {str(e)[:160]}")
    print("  ❌ no video model worked"); return None


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== Showrunner smoke test ===")
    t = test_text()
    v = test_vision()
    g = test_video()
    print("\n=== RESULT ===")
    print(f"  text : {t or 'FAILED'}")
    print(f"  vl   : {v or 'FAILED'}")
    print(f"  video: {g or 'FAILED'}")
    if all([t, v, g]):
        print("\n🎉 All green. Put these confirmed IDs in .env, then we build the pipeline.")
        sys.exit(0)
    print("\n⚠️  Fix the failing leg before building further (usually a model-ID or region issue).")
    sys.exit(1)
