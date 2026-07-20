"""The showrunner state machine: brief -> finished multi-language short drama.

Design goals the judges care about:
  - structured, replayable artifacts (everything via store.*)
  - parallel per-shot generation (video gen is 1-5 min each; never sequence it)
  - a bounded critic/retry loop (the self-correcting differentiator)
  - human-in-the-loop gates (approve callback) at outline / storyboard / final
  - an append-only event log powering the observability dashboard
"""
import json
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from showrunner import store, ffmpeg_utils, localize, config, subtitle_render, cost, lifecycle
from showrunner.clients import video
from showrunner.agents import planner, storyboard, prompt_writer, critic
from showrunner.consistency import ConsistencyManager
from showrunner.schemas import StoryBible, ShotSpec, EditDecisionList, SubtitleTrack

MAX_ATTEMPTS = 2       # 1 shot + up to 1 targeted retry
MAX_PARALLEL = 3       # keep upload contention low so i2v reference uploads don't time out


def _auto_approve(gate: str, payload) -> bool:
    return True


class Showrunner:
    def __init__(self, brief: str, *, langs=("zh", "en"), master_lang="zh",
                 n_scenes=4, n_chars=2, seconds=35, shots_per_scene=2,
                 consistency="text", budget_usd: float | None = None, genre: str = "悬疑反转",
                 frame_gate: bool = False, approve=_auto_approve, run_id: str | None = None):
        self.brief = brief
        self.langs = list(langs)
        self.master_lang = master_lang
        self.opts = dict(n_scenes=n_scenes, n_chars=n_chars, seconds=seconds,
                         shots_per_scene=shots_per_scene)
        self.consistency = consistency  # "text" (default) | "i2v" (reference-frame showcase)
        self.budget_usd = budget_usd
        self.genre = genre
        self.frame_gate = frame_gate
        self.approve = approve
        self.run_id = run_id or store.new_run_id()
        self.bible: StoryBible | None = None
        self.cm: ConsistencyManager | None = None
        self.cost = cost.CostTracker(ceiling_usd=budget_usd)

    def log(self, **e):
        store.append_event(self.run_id, e)
        print(f"[{self.run_id}] " + " ".join(f"{k}={v}" for k, v in e.items()))

    def _gate(self, gate: str, payload) -> tuple[bool, dict | None]:
        """Normalize approve callbacks: plain bool (CLI/auto) or (bool, edits) (web gates)."""
        res = self.approve(gate, payload)
        return res if isinstance(res, tuple) else (bool(res), None)

    # ---- pipeline ----------------------------------------------------------
    def run(self) -> dict:
        d = store.run_dir(self.run_id)
        cost.use(self.cost)  # meter every model call in this run against the budget
        self.log(stage="start", brief=self.brief[:80], budget=self.budget_usd)
        # persist the run's recipe so it can be resumed / partially regenerated later
        store.save_json(self.run_id, "run_config", {
            "brief": self.brief, "langs": self.langs, "master_lang": self.master_lang,
            **self.opts, "consistency": self.consistency,
            "budget_usd": self.budget_usd, "genre": self.genre})

        master_language = localize.LANG_NAMES.get(self.master_lang, self.master_lang)

        # 1. Plan (— @ids in the brief pull locked characters from the asset library)
        from showrunner import assetlib
        mentioned = re.findall(r"@([A-Za-z0-9_\-]+)", self.brief)
        existing = [c.model_dump() for cid in mentioned
                    if (c := assetlib.get_character(cid))]
        if existing:
            self.log(stage="cast_reused", ids=",".join(c["id"] for c in existing))
        self.bible, scenes = planner.plan(
            self.brief, n_scenes=self.opts["n_scenes"], n_chars=self.opts["n_chars"],
            seconds=self.opts["seconds"], master_language=master_language, genre=self.genre,
            existing_cast=existing or None)
        store.save_json(self.run_id, "story_bible", self.bible)
        store.save_json(self.run_id, "scenes", {"scenes": scenes})
        self.log(stage="planned", title=self.bible.title, characters=len(self.bible.characters))
        ok, edits = self._gate("outline", {"bible": self.bible.model_dump(), "scenes": scenes})
        if not ok:
            self.log(stage="halted", gate="outline"); return {"run_id": self.run_id, "halted": "outline"}
        if edits:  # reviewer edited the outline in the gate — apply before storyboarding
            merged = {**self.bible.model_dump(), **{k: v for k, v in edits.items()
                      if k in ("title", "logline", "synopsis", "style") and v}}
            self.bible = StoryBible.model_validate(merged)
            store.save_json(self.run_id, "story_bible", self.bible)
            self.log(stage="outline_edited", fields=",".join(edits.keys()))

        # 2. Storyboard
        shots = storyboard.storyboard(self.bible, scenes,
                                      shots_per_scene=self.opts["shots_per_scene"],
                                      master_language=master_language)
        store.save_json(self.run_id, "shots", {"shots": [s.model_dump() for s in shots]})
        self.log(stage="storyboarded", shots=len(shots))
        ok, edits = self._gate("storyboard", {"shots": [s.model_dump() for s in shots]})
        if not ok:
            self.log(stage="halted", gate="storyboard"); return {"run_id": self.run_id, "halted": "storyboard"}
        if edits:  # per-shot field edits: {shot_id: {action/dialogue/camera/...}}
            by_id = {s.id: s for s in shots}
            for sid, fields in edits.items():
                if sid in by_id and isinstance(fields, dict):
                    merged = {**by_id[sid].model_dump(),
                              **{k: v for k, v in fields.items()
                                 if k in ("action", "dialogue", "camera", "shot_size",
                                          "emotion", "continuity", "duration") and v not in (None, "")}}
                    shots[shots.index(by_id[sid])] = ShotSpec.model_validate(merged)
            store.save_json(self.run_id, "shots", {"shots": [s.model_dump() for s in shots]})
            self.log(stage="storyboard_edited", shots=",".join(edits.keys()))
        self._shots = shots

        # 2b. Consistency: mint one reference frame per character, reused as i2v first_frame.
        if self.consistency == "i2v":
            self.cm = ConsistencyManager(self.bible, d, self.bible.style,
                                         log=self.log, run_id=self.run_id)
            self.cm.mint_all(shots)

        # 2c. Frame Gate: cheap first-frame stills reviewed BEFORE any video spend.
        # The approved frame becomes that shot's literal i2v first_frame.
        if self.frame_gate:
            made = self._make_frames(shots, d)
            if made:
                for s in shots:
                    if s.id in made:
                        lifecycle.set_state(self.run_id, s.id, "frame_ready", force=True)
                if not self.approve("frames", {"frames": made}):
                    self.log(stage="halted", gate="frames")
                    return {"run_id": self.run_id, "halted": "frames"}

        # 3. Generate shots in parallel, each self-critiqued
        results: dict[str, Path] = {}
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
            futs = {pool.submit(self._make_shot, sh, d): sh for sh in shots}
            for f in as_completed(futs):
                sh = futs[f]
                try:
                    clip = f.result()
                    if clip:
                        results[sh.id] = clip
                except Exception as e:
                    self.log(stage="shot_error", shot=sh.id, error=str(e)[:160])

        ordered = [results[s.id] for s in shots if s.id in results]
        if not ordered:
            self.log(stage="failed", reason="no shots generated")
            return {"run_id": self.run_id, "error": "no shots generated"}

        # 4. Edit: normalize -> concat -> subtitles (multi-lang) -> cover
        final = self._edit(shots, results, d)

        # 5. Final gate
        self.approve("final", {"video": str(final)})
        store.save_json(self.run_id, "cost", self.cost.breakdown())
        self.log(stage="done", final=str(final), cost_usd=self.cost.total())
        return {"run_id": self.run_id, "final": str(final), "title": self.bible.title,
                "shots": len(ordered), "cost": self.cost.breakdown()}

    # ---- per-shot generation + critic loop ---------------------------------
    def _make_shot(self, shot: ShotSpec, d: Path, attempt_base: int = 0, *,
                   kind: str = "gen", ref_override: str | None = None,
                   prompt_extra: str = "") -> Path | None:
        advice = ""
        best: Path | None = None
        ref = ref_override if ref_override is not None else (
            self._frame_ref(shot, d) or (self.cm.ref_for_shot(shot) if self.cm else None))
        lifecycle.set_state(self.run_id, shot.id, "rendering", force=True)
        for a in range(1, MAX_ATTEMPTS + 1):
            attempt = attempt_base + a
            if not self.cost.admit("video"):  # budget admission: refuse new spend, keep in-flight
                self.log(stage="budget_refused", shot=shot.id, attempt=attempt)
                break
            req = prompt_writer.write(shot, self.bible, ref_image_url=ref, revision_advice=advice)
            prompt = req.prompt + (f" {prompt_extra}" if prompt_extra else "")
            dest = d / "shots" / f"{shot.id}_try{attempt}.mp4"
            self.log(stage="gen", shot=shot.id, attempt=attempt)
            try:
                clip = video.generate(prompt, dest, image_url=req.ref_image_path,
                                      negative_prompt=req.negative_prompt, duration=req.duration)
            except Exception as e:
                self.log(stage="gen_fail", shot=shot.id, attempt=attempt, error=str(e)[:160])
                continue
            best = clip
            rel = str(clip.relative_to(d)) if clip.is_relative_to(d) else str(clip)
            lifecycle.add_version(self.run_id, shot.id, attempt, rel, kind=kind)
            # Tier-0 gate: free deterministic checks before spending VL tokens
            pre = critic.precheck(clip, expected_duration=shot.duration)
            if not pre["ok"]:
                self.log(stage="precheck_fail", shot=shot.id, attempt=attempt, reason=pre["reason"])
                advice = f"previous take failed a technical check: {pre['reason']}"
                continue
            lifecycle.set_state(self.run_id, shot.id, "review", force=True)
            try:
                qa = critic.review(clip, shot, self.bible)
            except Exception as e:  # fail-open: never let a critic error drop a usable clip
                self.log(stage="critic_error", shot=shot.id, error=str(e)[:120])
                return clip
            store.save_json(self.run_id, f"shots/{shot.id}_qa{attempt}", qa)
            lifecycle.set_qa(self.run_id, shot.id, attempt, qa.model_dump())
            self.log(stage="qa", shot=shot.id, attempt=attempt, passed=qa.passed,
                     na=qa.narrative_alignment, cc=qa.character_consistency, tq=qa.technical_quality)
            if qa.passed:
                lifecycle.set_current(self.run_id, shot.id, attempt)
                lifecycle.set_state(self.run_id, shot.id, "approved", force=True)
                return clip
            lifecycle.set_state(self.run_id, shot.id, "rendering", force=True)
            advice = qa.revision_advice
        if best is None:
            lifecycle.set_state(self.run_id, shot.id, "error", force=True)
        else:  # fail-open: float the pointer to the last take so the final can still assemble
            try:
                n = int(re.search(r"_try(\d+)$", best.stem).group(1))
                lifecycle.set_current(self.run_id, shot.id, n)
            except (AttributeError, ValueError):
                pass
            lifecycle.set_state(self.run_id, shot.id, "review", force=True)
        return best  # keep the last attempt even if it never passed

    # ---- editing -----------------------------------------------------------
    def _edit(self, shots: list[ShotSpec], results: dict[str, Path], d: Path) -> Path:
        used = [s for s in shots if s.id in results]
        self.log(stage="edit", shots=len(used))
        norm = [ffmpeg_utils.normalize(results[s.id], d / "shots" / f"{s.id}_norm.mp4") for s in used]
        master = ffmpeg_utils.concat(norm, d / "master.mp4")

        # Subtitle cache: dialogue doesn't change on re-edit/regen, so reuse saved tracks
        # (skips the translation calls) as long as the used-shot list is identical.
        ids = [s.id for s in used]
        cached = store.load_json(self.run_id, "subtitles")
        if cached and cached.get("shot_ids") == ids:
            tracks = [SubtitleTrack.model_validate(t) for t in cached["tracks"]]
            self.log(stage="subs_cached", langs=len(tracks))
        else:
            tracks = localize.build_tracks(used, self.langs, self.master_lang)
        store.save_json(self.run_id, "subtitles",
                        {"shot_ids": ids, "tracks": [t.model_dump() for t in tracks]})
        srt_by_lang = {t.lang: ffmpeg_utils.write_srt(t.cues, d / f"subs_{t.lang}.srt")
                       for t in tracks}

        # Burn bilingual subtitles (master lang + first secondary) via Pillow overlay,
        # plus the mandatory explicit AIGC badge (CN labeling regulation).
        sec_lang = next((l for l in self.langs if l != self.master_lang), None)
        burned = master
        try:
            slots = subtitle_render.build_slots(tracks, self.master_lang, sec_lang, d / "subpng")
            badge = subtitle_render.render_aigc_badge(d / "subpng" / "aigc.png")
            slots.append({"png": str(badge), "start": 0, "end": 0, "pos": "tr", "always": True})
            burned = ffmpeg_utils.burn_overlay(master, slots, d / "burned.mp4")
            self.log(stage="burned", cues=max(len(slots) - 1, 0), aigc_label=True)
        except Exception as e:
            self.log(stage="burn_skip", error=str(e)[:120])
        # Embed every language as a selectable soft track on top of the burned cut.
        try:
            final = ffmpeg_utils.mux_soft_subs(burned, srt_by_lang, d / "final.mp4")
        except RuntimeError as e:
            self.log(stage="mux_skip", error=str(e)[:120])
            final = d / "final.mp4"; shutil.copy(burned, final)
        # Titled cover — from the pre-subtitle master so only the title shows.
        try:
            frame = ffmpeg_utils.extract_frame(master, d / "cover_raw.png", from_end=1.0)
            subtitle_render.render_cover(frame, self.bible.title, d / "cover.png")
        except Exception as e:
            self.log(stage="cover_skip", error=str(e)[:120])

        edl = EditDecisionList(ordered_shot_ids=[s.id for s in used],
                               subtitle_tracks=tracks, cover_shot_id=used[0].id if used else None)
        store.save_json(self.run_id, "edl", edl)
        return final

    # ---- resume & single-shot regeneration ---------------------------------
    @classmethod
    def from_run(cls, run_id: str, approve=_auto_approve) -> "Showrunner":
        """Rehydrate a Showrunner from a run's persisted artifacts (config, bible, shots)."""
        cfg = store.load_json(run_id, "run_config") or {}
        sr = cls(cfg.get("brief", "(resumed)"),
                 langs=cfg.get("langs", ["zh", "en"]), master_lang=cfg.get("master_lang", "zh"),
                 n_scenes=cfg.get("n_scenes", 4), n_chars=cfg.get("n_chars", 2),
                 seconds=cfg.get("seconds", 35), shots_per_scene=cfg.get("shots_per_scene", 2),
                 consistency=cfg.get("consistency", "text"), budget_usd=cfg.get("budget_usd"),
                 genre=cfg.get("genre", "悬疑反转"), approve=approve, run_id=run_id)
        bible = store.load_json(run_id, "story_bible")
        shots = (store.load_json(run_id, "shots") or {}).get("shots")
        if not bible or not shots:
            raise RuntimeError(f"run {run_id} has no bible/shots on disk — nothing to resume")
        sr.bible = StoryBible.model_validate(bible)
        sr._shots = [ShotSpec.model_validate(s) for s in shots]
        return sr

    @classmethod
    def resume(cls, run_id: str, approve=_auto_approve) -> dict:
        """Checkpoint restart: reuse every QA-passed clip, regenerate only what's missing."""
        return cls.from_run(run_id, approve)._resume_run()

    @classmethod
    def regen_shot(cls, run_id: str, shot_id: str, *, camera: str | None = None,
                   note: str | None = None) -> dict:
        """Targeted redo of one shot, then re-assemble the final cut.
        camera: preset key or free text (overrides the ShotSpec); note: director's note
        appended to the generation prompt (Retake-style targeted fix)."""
        return cls.from_run(run_id)._regen_single(shot_id, camera=camera, note=note)

    def _resume_run(self) -> dict:
        d = store.run_dir(self.run_id)
        cost.use(self.cost)
        shots = self._shots
        if self.consistency == "i2v":
            self.cm = ConsistencyManager(self.bible, d, self.bible.style,
                                         log=self.log, run_id=self.run_id)
            self.cm.mint_all(shots)  # run-dir/library hits → normally zero new generations
        results = self._collect_results(shots, d)
        todo = [s for s in shots if s.id not in results]
        self.log(stage="resume", reuse=len(results), regen=len(todo))
        if todo:
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
                futs = {pool.submit(self._make_shot, sh, d, self._attempt_base(sh, d)): sh
                        for sh in todo}
                for f in as_completed(futs):
                    sh = futs[f]
                    try:
                        clip = f.result()
                        if clip:
                            results[sh.id] = clip
                    except Exception as e:
                        self.log(stage="shot_error", shot=sh.id, error=str(e)[:160])
                    if sh.id not in results:  # regen failed (e.g. quota) → salvage best old try
                        fb = self._best_clip(sh, d)
                        if fb:
                            results[sh.id] = fb
                            self.log(stage="resume_fallback", shot=sh.id)
        ordered = [results[s.id] for s in shots if s.id in results]
        if not ordered:
            self.log(stage="failed", reason="no shots available")
            return {"run_id": self.run_id, "error": "no shots available"}
        final = self._edit(shots, results, d)
        self.approve("final", {"video": str(final)})
        self._save_cost_merged()
        self.log(stage="done", final=str(final), cost_usd=self.cost.total())
        return {"run_id": self.run_id, "final": str(final), "title": self.bible.title,
                "shots": len(ordered), "reused": len(shots) - len(todo)}

    def _regen_single(self, shot_id: str, camera: str | None = None,
                      note: str | None = None) -> dict:
        d = store.run_dir(self.run_id)
        cost.use(self.cost)
        shots = self._shots
        target = next((s for s in shots if s.id == shot_id), None)
        if not target:
            return {"run_id": self.run_id, "error": f"unknown shot {shot_id}"}
        if camera:  # structured camera override persists onto the ShotSpec
            target.camera = camera
            store.save_json(self.run_id, "shots", {"shots": [s.model_dump() for s in shots]})
        self.log(stage="regen", shot=shot_id, camera=camera or "", note=(note or "")[:60])
        if self.consistency == "i2v":
            self.cm = ConsistencyManager(self.bible, d, self.bible.style,
                                         log=self.log, run_id=self.run_id)
            self.cm.mint_all([target])
        clip = None
        try:
            clip = self._make_shot(target, d, attempt_base=self._attempt_base(target, d),
                                   kind="regen",
                                   prompt_extra=f"Director's note: {note}." if note else "")
        except Exception as e:
            self.log(stage="shot_error", shot=shot_id, error=str(e)[:160])
        results = self._collect_results(shots, d)
        if clip:
            results[shot_id] = clip
        elif shot_id not in results:
            fb = self._best_clip(target, d)
            if fb:
                results[shot_id] = fb
                self.log(stage="regen_fallback", shot=shot_id)
        if not results:
            return {"run_id": self.run_id, "error": "no clips available"}
        final = self._edit(shots, results, d)
        self._save_cost_merged()
        self.log(stage="done", final=str(final), cost_usd=self.cost.total())
        return {"run_id": self.run_id, "final": str(final), "shot": shot_id}

    # ---- Extend / Jump-To (the two continuity primitives, per Google Flow) ---
    @classmethod
    def continue_shot(cls, run_id: str, shot_id: str, mode: str, prompt: str) -> dict:
        """mode='extend': continue the action, seeded by the source take's LAST frame.
        mode='jump': cut to a new setting carrying the cast (portrait as first_frame)."""
        return cls.from_run(run_id)._continue(shot_id, mode, prompt)

    def _continue(self, shot_id: str, mode: str, prompt: str) -> dict:
        d = store.run_dir(self.run_id)
        cost.use(self.cost)
        shots = self._shots
        src = next((s for s in shots if s.id == shot_id), None)
        if not src:
            return {"run_id": self.run_id, "error": f"unknown shot {shot_id}"}

        # a unique id sequenced after the source shot
        suffix = "x" if mode == "extend" else "j"
        n = 1
        while any(s.id == f"{shot_id}_{suffix}{n}" for s in shots):
            n += 1
        new = ShotSpec(
            id=f"{shot_id}_{suffix}{n}", scene_index=src.scene_index,
            shot_index=src.shot_index + 1, beat=src.beat,
            shot_size=src.shot_size if mode == "extend" else "medium",
            camera="continuation of previous shot" if mode == "extend" else "establishing the new space",
            characters_present=list(src.characters_present),
            action=prompt, emotion=src.emotion, dialogue="", continuity=src.continuity,
            duration=src.duration)
        shots.insert(shots.index(src) + 1, new)
        store.save_json(self.run_id, "shots", {"shots": [s.model_dump() for s in shots]})
        self.log(stage=mode, shot=new.id, source=shot_id)

        ref = None
        if mode == "extend":  # seed with the source's current take's final frame
            src_clip = lifecycle.current_clip(self.run_id, shot_id)
            if src_clip:
                from showrunner import images
                p = d / src_clip if not Path(src_clip).is_absolute() else Path(src_clip)
                if p.exists():
                    frame = ffmpeg_utils.extract_frame(p, d / "frames" / f"{new.id}_seed.png",
                                                       from_end=0.15)
                    ref = images.to_datauri(frame, max_w=1080, quality=88)
        elif self.consistency == "i2v":  # jump: carry the cast via locked portraits
            self.cm = ConsistencyManager(self.bible, d, self.bible.style,
                                         log=self.log, run_id=self.run_id)
            self.cm.mint_all([new])
            ref = self.cm.ref_for_shot(new)

        clip = None
        try:
            clip = self._make_shot(new, d, attempt_base=0, kind=mode,
                                   ref_override=ref if ref else None)
        except Exception as e:
            self.log(stage="shot_error", shot=new.id, error=str(e)[:160])
        results = self._collect_results(shots, d)
        if clip:
            results[new.id] = clip
        if not results:
            return {"run_id": self.run_id, "error": "no clips available"}
        final = self._edit(shots, results, d)
        self._save_cost_merged()
        self.log(stage="done", final=str(final), cost_usd=self.cost.total())
        return {"run_id": self.run_id, "final": str(final), "new_shot": new.id}

    # ---- Frame Gate ---------------------------------------------------------
    def _make_frames(self, shots: list[ShotSpec], d: Path) -> dict:
        """Generate a first-frame still per shot (~15x cheaper than a video take).
        Uses Qwen-Image I2I from the character portrait when possible; falls back to the
        portrait itself; skips the gate entirely if nothing can be produced (fail-open)."""
        from showrunner import images
        from showrunner.clients import image as image_client
        made: dict[str, str] = {}
        fdir = d / "frames"
        fdir.mkdir(exist_ok=True)
        for shot in shots:
            dest = fdir / f"{shot.id}.png"
            if dest.exists():
                made[shot.id] = str(dest)
                continue
            ref = self.cm.ref_for_shot(shot) if self.cm else None
            prompt = (f"Vertical 9:16 cinematic still. {self.bible.style}. {shot.shot_size} shot. "
                      f"{shot.action}. Mood: {shot.emotion}.")
            try:
                if not self.cost.admit("image"):
                    break
                if ref:
                    image_client.first_frame(ref, prompt, dest)
                else:
                    image_client.portrait(prompt, dest)
                made[shot.id] = str(dest)
                self.log(stage="frame", shot=shot.id)
            except Exception as e:
                self.log(stage="frame_fail", shot=shot.id, error=str(e)[:120])
                # fallback: reuse the character portrait as a stand-in preview
                if ref and ref.startswith("data:"):
                    src = d / "refs"
                    for cid in shot.characters_present:
                        p = src / f"{cid}.png"
                        if p.exists():
                            shutil.copy(p, dest)
                            made[shot.id] = str(dest)
                            self.log(stage="frame_fallback", shot=shot.id)
                            break
        if made:
            store.save_json(self.run_id, "frames", {"frames": made})
        else:
            self.log(stage="frames_skipped", reason="no frames could be produced")
        return made

    def _frame_ref(self, shot: ShotSpec, d: Path) -> str | None:
        """An approved Frame-Gate still takes precedence as the shot's i2v first_frame."""
        from showrunner import images
        p = d / "frames" / f"{shot.id}.png"
        if self.frame_gate and p.exists():
            return images.to_datauri(p, max_w=1080, quality=88)
        return None

    def regen_frame(self, shot_id: str) -> dict:
        """Redo a single Frame-Gate still (called from the frame wall UI)."""
        d = store.run_dir(self.run_id)
        shots = getattr(self, "_shots", None) or []
        target = next((s for s in shots if s.id == shot_id), None)
        if not target:
            return {"error": f"unknown shot {shot_id}"}
        (d / "frames" / f"{shot_id}.png").unlink(missing_ok=True)
        made = self._make_frames([target], d)
        return {"ok": shot_id in made}

    # -- helpers over persisted per-shot artifacts --
    def _collect_results(self, shots: list[ShotSpec], d: Path) -> dict[str, Path]:
        """shot_id -> the take the final should use.

        Precedence: the lifecycle version stack's floating CURRENT pointer (user-controllable)
        → newest QA-passed clip (legacy runs without lifecycle.json)."""
        out: dict[str, Path] = {}
        lc = lifecycle.load(self.run_id)["shots"]
        for sh in shots:
            cur = lc.get(sh.id, {}).get("current")
            if cur is not None:
                rel = lifecycle.current_clip(self.run_id, sh.id)
                if rel:
                    clip = d / rel if not Path(rel).is_absolute() else Path(rel)
                    if clip.exists():
                        out[sh.id] = clip
                        continue
            for qaf in sorted((d / "shots").glob(f"{sh.id}_qa*.json")):
                if qaf.name.startswith("._"):
                    continue
                try:
                    qa = json.loads(qaf.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if qa.get("passed"):
                    n = qaf.stem.rsplit("_qa", 1)[1]
                    clip = d / "shots" / f"{sh.id}_try{n}.mp4"
                    if clip.exists():
                        out[sh.id] = clip
        return out

    def _best_clip(self, shot: ShotSpec, d: Path):
        clips = [c for c in sorted((d / "shots").glob(f"{shot.id}_try*.mp4"))
                 if not c.name.startswith("._")]
        return clips[-1] if clips else None

    def _attempt_base(self, shot: ShotSpec, d: Path) -> int:
        ns = [int(m.group(1)) for c in (d / "shots").glob(f"{shot.id}_try*.mp4")
              if not c.name.startswith("._")
              and (m := re.match(rf"{re.escape(shot.id)}_try(\d+)$", c.stem))]
        return max(ns, default=0)

    def _save_cost_merged(self):
        """Resume/regen add spend on top of the original run's bill — merge, don't clobber."""
        prior = store.load_json(self.run_id, "cost") or {"total": 0, "by_kind": {}, "calls": 0}
        now = self.cost.breakdown()
        kinds = set(prior.get("by_kind", {})) | set(now["by_kind"])
        store.save_json(self.run_id, "cost", {
            "total": round(prior.get("total", 0) + now["total"], 4),
            "by_kind": {k: round(prior.get("by_kind", {}).get(k, 0) + now["by_kind"].get(k, 0), 4)
                        for k in kinds},
            "calls": prior.get("calls", 0) + now["calls"], "ceiling": now.get("ceiling")})
