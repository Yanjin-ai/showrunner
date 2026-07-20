"""CLI: run the full showrunner pipeline.

  python -m scripts.run "A detective realizes the victim is her own alibi" \
      --langs zh,en,es --scenes 4 --interactive

--interactive turns on human-in-the-loop approval at outline / storyboard / final.
"""
import argparse
from showrunner.orchestrator import Showrunner, _auto_approve


def interactive_approve(gate: str, payload) -> bool:
    print(f"\n===== HITL gate: {gate} =====")
    if gate == "outline":
        b = payload["bible"]
        print("TITLE:", b["title"]); print("LOGLINE:", b["logline"])
        print("CHARACTERS:", ", ".join(c["name"] for c in b["characters"]))
    elif gate == "storyboard":
        for s in payload["shots"]:
            print(f"  {s['id']}: [{s['shot_size']}] {s['action']}")
    elif gate == "final":
        print("FINAL:", payload["video"])
        return True
    return input(f"approve {gate}? [Y/n] ").strip().lower() in ("", "y", "yes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief", nargs="?", default=None)
    ap.add_argument("--resume", metavar="RUN_ID", default=None,
                    help="resume a previous run: reuse QA-passed shots, regenerate the rest")
    ap.add_argument("--langs", default="zh,en")
    ap.add_argument("--master-lang", default="zh")
    ap.add_argument("--scenes", type=int, default=4)
    ap.add_argument("--chars", type=int, default=2)
    ap.add_argument("--seconds", type=int, default=35)
    ap.add_argument("--shots-per-scene", type=int, default=2)
    ap.add_argument("--consistency", choices=["text", "i2v"], default="text",
                    help="text = appearance baked into prompts (fast); i2v = per-character reference frame")
    ap.add_argument("--budget", type=float, default=None, help="hard USD ceiling; stops the run if exceeded")
    ap.add_argument("--genre", default="悬疑反转",
                    help="题材模板: 悬疑反转 / 霸总情感 / 复仇逆袭 / 甜宠 / 萌宠 / 灵异 (or free text)")
    ap.add_argument("--frame-gate", action="store_true",
                    help="approve cheap first-frame stills before any video spend")
    ap.add_argument("--interactive", action="store_true")
    a = ap.parse_args()

    if a.resume:
        out = Showrunner.resume(a.resume,
                                approve=interactive_approve if a.interactive else _auto_approve)
        print("\n=== RESULT ===")
        for k, v in out.items():
            print(f"  {k}: {v}")
        return
    if not a.brief:
        ap.error("brief is required unless --resume RUN_ID is given")

    sr = Showrunner(
        a.brief, langs=a.langs.split(","), master_lang=a.master_lang,
        n_scenes=a.scenes, n_chars=a.chars, seconds=a.seconds,
        shots_per_scene=a.shots_per_scene, consistency=a.consistency, budget_usd=a.budget,
        genre=a.genre, frame_gate=a.frame_gate,
        approve=interactive_approve if a.interactive else _auto_approve,
    )
    out = sr.run()
    print("\n=== RESULT ===")
    for k, v in out.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
