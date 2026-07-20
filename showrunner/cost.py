"""Cost / budget guardrail. The hackathon scores token budget, and video is the money sink,
so every model call is metered and an optional ceiling stops a run before it overspends.

Rates are rough, editable estimates (USD) — the point is relative accounting + a hard stop,
not accounting-grade precision. A run reports its breakdown; the dashboard can surface it."""
import threading

# rough unit costs (USD): text per 1K tokens, video/image per generation, tts per 1K chars
RATES = {
    "text_per_1k": 0.004,
    "vl_per_1k": 0.006,
    "video_per_gen": 0.30,
    "image_per_gen": 0.02,
    "tts_per_1k_chars": 0.015,
}


class BudgetExceeded(RuntimeError):
    pass


class CostTracker:
    def __init__(self, ceiling_usd: float | None = None):
        self.ceiling = ceiling_usd
        self._lock = threading.Lock()
        self.events: list[dict] = []

    def _add(self, kind: str, usd: float, **meta):
        with self._lock:
            self.events.append({"kind": kind, "usd": usd, **meta})
            total = sum(e["usd"] for e in self.events)
        if self.ceiling is not None and total > self.ceiling:
            raise BudgetExceeded(f"budget ${self.ceiling:.2f} exceeded (spent ${total:.2f})")

    def text(self, tokens: int, vl: bool = False):
        self._add("vl" if vl else "text",
                  tokens / 1000 * RATES["vl_per_1k" if vl else "text_per_1k"], tokens=tokens)

    def video(self, n: int = 1):
        self._add("video", n * RATES["video_per_gen"], n=n)

    def image(self, n: int = 1):
        self._add("image", n * RATES["image_per_gen"], n=n)

    def tts(self, chars: int):
        self._add("tts", chars / 1000 * RATES["tts_per_1k_chars"], chars=chars)

    def total(self) -> float:
        return round(sum(e["usd"] for e in self.events), 4)

    def admit(self, kind: str = "video") -> bool:
        """Admission control (Replicate aborted-vs-canceled semantics): refuse to START a new
        expensive call that would bust the ceiling; in-flight work is never killed."""
        if self.ceiling is None:
            return True
        unit = {"video": RATES["video_per_gen"], "image": RATES["image_per_gen"]}.get(kind, 0.01)
        return self.total() + unit <= self.ceiling

    def breakdown(self) -> dict:
        out: dict[str, float] = {}
        for e in self.events:
            out[e["kind"]] = round(out.get(e["kind"], 0) + e["usd"], 4)
        return {"total": self.total(), "by_kind": out, "calls": len(self.events),
                "ceiling": self.ceiling}


def estimate(n_scenes: int, shots_per_scene: int, n_chars: int = 2, *, consistency: str = "text",
             langs: int = 2, retry_rate: float = 0.35, frame_gate: bool = False) -> dict:
    """Pre-flight price of a run BEFORE generating (industry rule: price before generate).

    Assumes MAX_ATTEMPTS=2 with `retry_rate` of shots needing one retry (observed ~1/3)."""
    shots = n_scenes * shots_per_scene
    videos = shots * (1 + retry_rate) + (n_chars if consistency == "i2v" and not frame_gate else 0)
    imgs = (shots + n_chars) if frame_gate else 0
    # text: plan + storyboard + (translate per extra lang) ≈ 2.5k tokens each; VL: ~1.2 reviews/shot
    text_tokens = (2 + max(0, langs - 1)) * 2500
    vl_tokens = shots * (1 + retry_rate) * 1800
    breakdown = {
        "video": round(videos * RATES["video_per_gen"], 2),
        "image": round(imgs * RATES["image_per_gen"], 2),
        "text": round(text_tokens / 1000 * RATES["text_per_1k"], 4),
        "vl": round(vl_tokens / 1000 * RATES["vl_per_1k"], 4),
    }
    return {"total": round(sum(breakdown.values()), 2), "by_kind": breakdown,
            "video_gens": round(videos, 1), "image_gens": imgs, "shots": shots}


# a no-op default so callers can always record without wiring a tracker through everything
class _NullTracker(CostTracker):
    def _add(self, *a, **k):
        pass


NULL = _NullTracker()

# module-global current tracker: the orchestrator sets one per run; clients record into it.
current: CostTracker = NULL


def use(tracker: CostTracker):
    global current
    current = tracker
