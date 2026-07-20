"""Human-in-the-loop gate controller for the web pipeline.

The orchestrator's approve callback blocks on a per-(run,gate) Event; the dashboard
resolves it via an HTTP endpoint. Times out to auto-approve so a live demo never stalls."""
import threading

AUTO_APPROVE_TIMEOUT = 240  # seconds


class Gates:
    def __init__(self):
        self._events: dict[tuple[str, str], threading.Event] = {}
        self._decisions: dict[tuple[str, str], bool] = {}
        self._edits: dict[tuple[str, str], dict | None] = {}
        self._pending: dict[str, str | None] = {}

    def pending_gate(self, run_id: str) -> str | None:
        return self._pending.get(run_id)

    def wait(self, run_id: str, gate: str, payload=None) -> tuple[bool, dict | None]:
        """Block until the gate is resolved. Returns (approved, edits) — the reviewer may
        approve WITH edits (structure-first editing, per LTX's breakdown review)."""
        key = (run_id, gate)
        ev = self._events.setdefault(key, threading.Event())
        self._pending[run_id] = gate
        resolved = ev.wait(timeout=AUTO_APPROVE_TIMEOUT)
        self._pending[run_id] = None
        if not resolved:  # timeout -> auto-approve, no edits (a live demo never stalls)
            return True, None
        return self._decisions.get(key, True), self._edits.get(key)

    def resolve(self, run_id: str, gate: str, approved: bool, edits: dict | None = None):
        key = (run_id, gate)
        self._decisions[key] = approved
        self._edits[key] = edits
        self._events.setdefault(key, threading.Event()).set()


gates = Gates()
