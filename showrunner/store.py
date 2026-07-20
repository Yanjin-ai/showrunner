"""Run + artifact persistence. Every artifact is JSON on disk so runs are replayable and
any shot can be re-generated in isolation. This is also what the dashboard reads."""
import json
import time
from pathlib import Path

RUNS = Path("runs")


def new_run_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def run_dir(run_id: str) -> Path:
    d = RUNS / run_id
    (d / "shots").mkdir(parents=True, exist_ok=True)
    return d


def save_json(run_id: str, name: str, obj) -> Path:
    p = run_dir(run_id) / f"{name}.json"
    data = obj.model_dump() if hasattr(obj, "model_dump") else obj
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load_json(run_id: str, name: str):
    p = run_dir(run_id) / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def append_event(run_id: str, event: dict):
    """Append-only log powering the observability/replay view."""
    p = run_dir(run_id) / "events.jsonl"
    event = {"t": time.time(), **event}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
