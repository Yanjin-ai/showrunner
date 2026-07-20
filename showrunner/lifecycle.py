"""Shot lifecycle state machine + version stacks.

Modeled on the industry consensus (see docs/research/film-pipeline.md):
- ShotGrid: two-axis state — production state vs artifact approval; approving an artifact
  promotes the shot; role-gated transitions.
- Frame.io: version stacks with a floating "current" pointer; feedback lives on the version.
- ftrack: creating a version IS the review request; numbering climbs until approved.

Persisted per run in runs/<id>/lifecycle.json:
{
  "shots": {
    "<shot_id>": {
      "state": "draft|frame_ready|rendering|review|approved|locked|error",
      "current": 2,                       # attempt number of the current take (floating pointer)
      "versions": [ {"n":1, "clip":"...", "qa":{...}|null, "kind":"gen|regen|extend"} ]
    }
  }
}
"""
import json
import threading
from pathlib import Path

from showrunner import store

STATES = ["draft", "frame_ready", "rendering", "review", "approved", "locked", "error"]

# Allowed transitions (from -> set of to). "locked" only unlocks explicitly.
_ALLOWED = {
    "draft": {"frame_ready", "rendering", "error"},
    "frame_ready": {"rendering", "draft", "error"},
    "rendering": {"review", "error", "rendering"},
    "review": {"approved", "rendering", "error"},
    "approved": {"locked", "rendering", "review"},   # re-open by starting a new take
    "locked": {"approved"},                          # explicit unlock only
    "error": {"rendering", "draft"},
}

_lock = threading.Lock()


def _path(run_id: str) -> Path:
    return store.run_dir(run_id) / "lifecycle.json"


def load(run_id: str) -> dict:
    p = _path(run_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"shots": {}}


def _save(run_id: str, data: dict):
    _path(run_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _shot(data: dict, shot_id: str) -> dict:
    return data["shots"].setdefault(shot_id, {"state": "draft", "current": None, "versions": []})


def set_state(run_id: str, shot_id: str, state: str, *, force: bool = False) -> dict:
    """Transition a shot's state (validated against _ALLOWED unless force)."""
    with _lock:
        data = load(run_id)
        sh = _shot(data, shot_id)
        cur = sh["state"]
        if not force and state != cur and state not in _ALLOWED.get(cur, set()):
            raise ValueError(f"illegal transition {cur} -> {state} for {shot_id}")
        sh["state"] = state
        _save(run_id, data)
        return sh


def add_version(run_id: str, shot_id: str, n: int, clip: str, *, kind: str = "gen",
                qa: dict | None = None, make_current: bool = False) -> dict:
    """Append an immutable take to the stack; the current pointer moves only when asked
    (the orchestrator floats it to the passing take, or to the last take on fail-open)."""
    with _lock:
        data = load(run_id)
        sh = _shot(data, shot_id)
        sh["versions"] = [v for v in sh["versions"] if v["n"] != n] + \
                         [{"n": n, "clip": clip, "qa": qa, "kind": kind}]
        sh["versions"].sort(key=lambda v: v["n"])
        if make_current:
            sh["current"] = n
        _save(run_id, data)
        return sh


def set_qa(run_id: str, shot_id: str, n: int, qa: dict) -> dict:
    with _lock:
        data = load(run_id)
        sh = _shot(data, shot_id)
        for v in sh["versions"]:
            if v["n"] == n:
                v["qa"] = qa
        _save(run_id, data)
        return sh


def set_current(run_id: str, shot_id: str, n: int) -> dict:
    """Float the current pointer to an existing take (never destroys other takes)."""
    with _lock:
        data = load(run_id)
        sh = _shot(data, shot_id)
        if not any(v["n"] == n for v in sh["versions"]):
            raise ValueError(f"{shot_id} has no version {n}")
        if sh["state"] == "locked":
            raise ValueError(f"{shot_id} is locked; unlock before changing takes")
        sh["current"] = n
        _save(run_id, data)
        return sh


def current_clip(run_id: str, shot_id: str) -> str | None:
    sh = load(run_id)["shots"].get(shot_id)
    if not sh or sh["current"] is None:
        return None
    for v in sh["versions"]:
        if v["n"] == sh["current"]:
            return v["clip"]
    return None
