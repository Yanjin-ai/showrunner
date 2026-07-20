"""FastAPI backend + live dashboard for the showrunner pipeline.

  uvicorn showrunner.server:app --host 0.0.0.0 --port 8000

Serves the dashboard at /, starts runs, streams live state (scene->shot tree, QA scores,
retries, pending HITL gate), and serves generated media from runs/."""
import json
import logging
import os
import threading
from collections import deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from showrunner import store, cost, lifecycle
from showrunner.agents.prompt_writer import CAMERA_PRESETS
from showrunner.gates import gates
from showrunner.orchestrator import Showrunner

# ---- production hardening ---------------------------------------------------
# Auth: set SHOWRUNNER_TOKEN to require `Authorization: Bearer <token>` (or ?token=)
# on every mutating endpoint. Unset = open dev mode.
TOKEN = os.getenv("SHOWRUNNER_TOKEN", "")


def require_token(request: Request):
    if not TOKEN:
        return
    supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip() \
        or request.query_params.get("token", "")
    if supplied != TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing token")


# Job queue: ONE worker executes generation jobs sequentially (fal/Replicate queue model).
# This is deliberate: gates and the cost tracker are per-process/per-run state, and a single
# API key means concurrent runs would just contend for the same quota. NOTE: run the server
# as a SINGLE process (uvicorn default; do not use --workers>1 — gates are in-memory).
_queue: deque = deque()
_queue_cv = threading.Condition()
_current_job: dict | None = None

_log_dir = Path("logs"); _log_dir.mkdir(exist_ok=True)
_reqlog = logging.getLogger("showrunner.requests")
if not _reqlog.handlers:
    h = logging.FileHandler(_log_dir / "server.log", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _reqlog.addHandler(h)
    _reqlog.setLevel(logging.INFO)


def enqueue(run_id: str, label: str, fn) -> int:
    with _queue_cv:
        _queue.append({"run_id": run_id, "label": label, "fn": fn})
        pos = len(_queue)
        _queue_cv.notify()
    store.append_event(run_id, {"stage": "queued", "label": label, "position": pos})
    return pos


def _job_worker():
    global _current_job
    while True:
        with _queue_cv:
            while not _queue:
                _queue_cv.wait()
            _current_job = _queue.popleft()
        job = _current_job
        try:
            job["fn"]()
        except Exception as e:
            store.append_event(job["run_id"], {"stage": f"{job['label']}_error",
                                               "error": str(e)[:200]})
        finally:
            _current_job = None


threading.Thread(target=_job_worker, daemon=True).start()

app = FastAPI(title="AI Showrunner")
RUNS = Path("runs"); RUNS.mkdir(exist_ok=True)
Path("library/characters").mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory="runs"), name="media")
app.mount("/lib", StaticFiles(directory="library"), name="lib")
_INDEX = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")


class RunReq(BaseModel):
    brief: str
    langs: list[str] = ["zh", "en"]
    master_lang: str = "zh"
    n_scenes: int = 4
    n_chars: int = 2
    seconds: int = 35
    shots_per_scene: int = 2
    consistency: str = "text"
    budget_usd: float | None = None
    genre: str = "悬疑反转"
    frame_gate: bool = False
    hitl: bool = True


class ApproveReq(BaseModel):
    decision: bool = True
    edits: dict | None = None


class RegenReq(BaseModel):
    camera: str | None = None
    note: str | None = None


class ContinueReq(BaseModel):
    mode: str  # "extend" | "jump"
    prompt: str


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    resp = await call_next(request)
    p = request.url.path
    if p != "/healthz" and not p.startswith(("/media", "/lib")):
        client = request.client.host if request.client else "-"
        _reqlog.info(f"{client} {request.method} {p} {resp.status_code}")
    return resp


@app.get("/healthz")
def healthz():
    return {"ok": True, "active_job": (_current_job or {}).get("run_id"),
            "queue_len": len(_queue), "auth": bool(TOKEN)}


@app.get("/queue")
def queue_state():
    return {"active": (_current_job or {}).get("run_id"),
            "pending": [{"run_id": j["run_id"], "label": j["label"]} for j in _queue]}


@app.get("/", response_class=HTMLResponse)
def index():
    return _INDEX


@app.post("/runs", dependencies=[Depends(require_token)])
def create_run(req: RunReq):
    run_id = store.new_run_id()
    approve = (lambda gate, payload: gates.wait(run_id, gate, payload)) if req.hitl else None
    sr = Showrunner(req.brief, langs=req.langs, master_lang=req.master_lang,
                    n_scenes=req.n_scenes, n_chars=req.n_chars, seconds=req.seconds,
                    shots_per_scene=req.shots_per_scene, consistency=req.consistency,
                    budget_usd=req.budget_usd, genre=req.genre, frame_gate=req.frame_gate,
                    run_id=run_id, approve=approve or (lambda g, p: True))
    pos = enqueue(run_id, "run", sr.run)
    return {"run_id": run_id, "queue_position": pos}


@app.post("/estimate")
def estimate(req: RunReq):
    """Price the run BEFORE generating (per-action cost transparency)."""
    return cost.estimate(req.n_scenes, req.shots_per_scene, req.n_chars,
                         consistency=req.consistency, langs=len(req.langs),
                         frame_gate=req.frame_gate)


@app.get("/camera-presets")
def camera_presets():
    return {"presets": CAMERA_PRESETS}


@app.post("/runs/{run_id}/approve", dependencies=[Depends(require_token)])
def approve(run_id: str, gate: str, decision: bool = True, body: ApproveReq | None = None):
    edits = body.edits if body else None
    gates.resolve(run_id, gate, body.decision if body else decision, edits)
    return {"ok": True}


@app.post("/runs/{run_id}/shots/{shot_id}/version/{n}", dependencies=[Depends(require_token)])
def select_version(run_id: str, shot_id: str, n: int):
    """Float the current-take pointer; re-assemble via /resume (subs cached → ~free)."""
    try:
        sh = lifecycle.set_current(run_id, shot_id, n)
        return {"ok": True, "shot": sh}
    except ValueError as e:
        return {"error": str(e)}


@app.post("/runs/{run_id}/shots/{shot_id}/lock", dependencies=[Depends(require_token)])
def lock_shot(run_id: str, shot_id: str, unlock: bool = False):
    sh = lifecycle.set_state(run_id, shot_id, "approved" if unlock else "locked", force=True)
    return {"ok": True, "shot": sh}


@app.post("/runs/{run_id}/shots/{shot_id}/continue", dependencies=[Depends(require_token)])
def continue_shot(run_id: str, shot_id: str, body: ContinueReq):
    """Extend (continue the action from the last frame) or Jump-To (new scene, same cast)."""
    if not (RUNS / run_id).exists():
        return {"error": "unknown run"}
    _bg(run_id, body.mode, lambda: Showrunner.continue_shot(run_id, shot_id, body.mode, body.prompt))
    return {"ok": True, "mode": body.mode}


@app.post("/runs/{run_id}/frames/{shot_id}/redo", dependencies=[Depends(require_token)])
def redo_frame(run_id: str, shot_id: str):
    if not (RUNS / run_id).exists():
        return {"error": "unknown run"}
    _bg(run_id, "frame", lambda: Showrunner.from_run(run_id).regen_frame(shot_id))
    return {"ok": True}


def _bg(run_id: str, label: str, fn):
    """All generation work funnels through the single job queue (see _job_worker)."""
    enqueue(run_id, label, fn)


@app.post("/runs/{run_id}/resume", dependencies=[Depends(require_token)])
def resume_run(run_id: str):
    """Checkpoint restart: reuse QA-passed clips, regenerate only missing/failed shots."""
    if not (RUNS / run_id).exists():
        return {"error": "unknown run"}
    _bg(run_id, "resume", lambda: Showrunner.resume(run_id))
    return {"ok": True, "run_id": run_id}


@app.post("/runs/{run_id}/shots/{shot_id}/regenerate", dependencies=[Depends(require_token)])
def regenerate_shot(run_id: str, shot_id: str, body: RegenReq | None = None):
    """Targeted redo of one shot (optional camera override + director's note);
    the final cut re-assembles automatically."""
    if not (RUNS / run_id).exists():
        return {"error": "unknown run"}
    cam = body.camera if body else None
    note = body.note if body else None
    _bg(run_id, "regen", lambda: Showrunner.regen_shot(run_id, shot_id, camera=cam, note=note))
    return {"ok": True, "run_id": run_id, "shot": shot_id}


@app.get("/runs/{run_id}/state")
def state(run_id: str):
    d = RUNS / run_id
    if not d.exists():
        return {"error": "unknown run"}
    events = _read_events(d)
    bible = store.load_json(run_id, "story_bible")
    shots = (store.load_json(run_id, "shots") or {}).get("shots", [])
    shot_state = _derive_shot_state(run_id, shots, events)
    final = f"/media/{run_id}/final.mp4" if (d / "final.mp4").exists() else None
    cover = f"/media/{run_id}/cover.png" if (d / "cover.png").exists() else None
    last = events[-1]["stage"] if events else "start"
    frames = (store.load_json(run_id, "frames") or {}).get("frames", {})
    return {
        "run_id": run_id, "status": last, "title": bible["title"] if bible else None,
        "bible": bible, "shots": shot_state, "pending_gate": gates.pending_gate(run_id),
        "final": final, "cover": cover, "events": events[-40:],
        "cost": store.load_json(run_id, "cost"),
        "scenes": (store.load_json(run_id, "scenes") or {}).get("scenes", []),
        "subtitles": (store.load_json(run_id, "subtitles") or {}).get("tracks", []),
        "edl": store.load_json(run_id, "edl"),
        "lifecycle": lifecycle.load(run_id)["shots"],
        "frames": {sid: f"/media/{run_id}/frames/{Path(p).name}" for sid, p in frames.items()},
    }


@app.get("/runs")
def list_runs():
    """Recent runs so the dashboard opens populated and past cuts are browsable."""
    out = []
    for d in sorted((p for p in RUNS.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True):
        bible = store.load_json(d.name, "story_bible")
        out.append({"id": d.name, "title": (bible or {}).get("title"),
                    "final": f"/media/{d.name}/final.mp4" if (d / "final.mp4").exists() else None,
                    "cover": f"/media/{d.name}/cover.png" if (d / "cover.png").exists() else None})
    return {"runs": out[:30]}


@app.get("/library")
def library():
    """The persistent, reusable cast — locked portraits + voices, shared across runs."""
    from showrunner import assetlib
    return {"characters": [
        {**c.model_dump(),
         "portrait": f"/lib/characters/{c.id}.png" if c.portrait_path else None}
        for c in assetlib.list_characters()]}


def _read_events(d: Path) -> list[dict]:
    p = d / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _derive_shot_state(run_id: str, shots: list[dict], events: list[dict]) -> list[dict]:
    """Fold the event log into a per-shot status + latest QA for the tree view."""
    by_id = {s["id"]: {**s, "status": "queued", "qa": None,
                       "clip": None, "attempts": 0} for s in shots}
    for e in events:
        sid = e.get("shot")
        if sid not in by_id:
            continue
        st = by_id[sid]
        if e["stage"] == "gen":
            st["status"] = "generating"; st["attempts"] = e.get("attempt", st["attempts"])
        elif e["stage"] == "qa":
            st["status"] = "passed" if e.get("passed") else "retrying"
            st["qa"] = {"na": e.get("na"), "cc": e.get("cc"), "tq": e.get("tq"),
                        "passed": e.get("passed")}
        elif e["stage"] in ("gen_fail", "shot_error"):
            st["status"] = "error"
    d = RUNS / run_id / "shots"
    for sid, st in by_id.items():
        clips = [c for c in (sorted(d.glob(f"{sid}_norm.mp4")) or sorted(d.glob(f"{sid}_try*.mp4")))
                 if not c.name.startswith("._")]
        if clips:
            st["clip"] = f"/media/{run_id}/shots/{clips[-1].name}"
            # poster from the QA-sampled frames so shot walls render instantly
            fdirs = [f for f in sorted(d.glob(f"{sid}_try*.frames"))
                     if f.is_dir() and not f.name.startswith("._")]
            if fdirs:
                fs = [p for p in sorted(fdirs[-1].glob("f*.png")) if not p.name.startswith("._")]
                if fs:
                    pick = fs[min(1, len(fs) - 1)]
                    st["poster"] = f"/media/{run_id}/shots/{fdirs[-1].name}/{pick.name}"
            else:  # legacy single-frame QA artifact
                stills = [p for p in sorted(d.glob(f"{sid}_try*.frame.png"))
                          if not p.name.startswith("._")]
                if stills:
                    st["poster"] = f"/media/{run_id}/shots/{stills[-1].name}"
            if st["status"] in ("generating", "queued"):
                st["status"] = "done"
            # A failed retry/regen must not mask a clip that already passed QA — the final
            # cut falls back to the passed take, so report the delivered state.
            if st["status"] == "error" and _has_passed_qa(d, sid):
                st["status"] = "passed"
    return list(by_id.values())


def _has_passed_qa(shots_dir: Path, shot_id: str) -> bool:
    for qaf in shots_dir.glob(f"{shot_id}_qa*.json"):
        if qaf.name.startswith("._"):
            continue
        try:
            if json.loads(qaf.read_text(encoding="utf-8")).get("passed"):
                return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return False
