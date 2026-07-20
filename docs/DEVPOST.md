# Devpost Submission — AI Showrunner

Everything below is **paste-ready for Devpost**. Devpost supports Markdown + LaTeX
(inline `\( … \)`, display `$$ … $$`) — this file uses exactly that dialect.
Copy each block into the matching Devpost field.

---

## FIELD 1 · "About the project" — copy everything between the cut lines

<!-- ✂ CUT FROM HERE ------------------------------------------------------ -->

## Inspiration

China's vertical short-drama industry ships **~470 AI-generated dramas per day**, yet studios still
call the workflow **"抽卡"** — pulling a slot-machine lever 30+ times per shot and praying. The
generators are good; what's missing is the **production system** around them: the thing that keeps a
character's face consistent across eight shots, rejects a bad take *before* it costs money, and lets
a human approve the story before a single frame is rendered.

AI Showrunner is that missing layer, built for QwenCloud Track 2: not a prompt box, but a **virtual
studio** — it plans like a screenwriter, shoots like a director, reviews like a script supervisor,
and accounts like a line producer.

## What it does

**One line in → a finished 9:16 short drama out.**

- **Four-beat screenwriting** (Hook → Friction → Spike → Button — the pacing grammar of 短剧) into a
  structured story bible and storyboard, with human approval gates at outline, storyboard, and final cut
- **Locked cast**: character portraits generated once, stored in a reusable library, and injected
  into every shot via Wan2.7 image-to-video — measured character-consistency 9–10/10 across shots
- **Self-correcting shoot loop**: a Qwen-VL critic scores three sampled frames of every take on
  narrative alignment, character consistency and technical quality, then drives *targeted*
  regeneration with a revision note — fully autonomously
- **A real production control plane**: per-shot lifecycle states and version stacks (switch takes and
  the final re-assembles for $0.00), Frame Gate (approve a cheap still before any video spend),
  price shown *before* the Start button, hard budget ceiling, Extend / Jump-To continuity primitives
- **Delivery**: bilingual burned subtitles, soft subtitle tracks in N languages from one master
  script, auto cover art, and China-compliant AIGC labeling (visible badge + container metadata)

Everything is observable and steerable from a live web studio.

## How we built it

**All generation runs on QwenCloud.** Qwen3.7-Max plans, storyboards and localizes. Qwen-VL judges
every take. Wan2.7 t2v/i2v renders shots — we reverse-engineered the undocumented i2v reference
protocol (`input.media = [{"type": "first_frame", "url": <data-URI>}]`) so locked portraits drive
every shot with no object storage at all. Interface stubs for Qwen-Image and Qwen-TTS are wired and
waiting on quota.

**The spine** is FastAPI plus a plain-Python orchestrator: a state machine with 3-way parallel shot
generation, three human gates with timeout auto-approve, Pydantic contracts on every artifact, an
append-only event log, and a file store where **every intermediate is replayable JSON** — any single
shot regenerates without touching the rest of the run.

**Quality is a funnel, not a hope.** Each take first passes a free deterministic precheck (decode,
duration, near-black detection) before any VL tokens are spent; the critic then scores it and a take
passes only if

$$\text{pass} \iff \text{NA} \ge 5 \;\wedge\; \text{CC} \ge 6 \;\wedge\; \text{TQ} \ge 6$$

Failed takes get one targeted retry whose prompt embeds the critic's revision note. In a real run, a
shot's character-consistency score went **1 → 9** after the critic noticed the wrong subject and
rewrote the prompt on its own.

**Cost is governed, not observed.** Every model call is metered at one choke point, and a run's
price is estimated before generation:

$$\mathbb{E}[\text{cost}] \approx \underbrace{S(1+r)\,c_v}_{\text{video}} + \underbrace{(S+C)\,c_i}_{\text{stills}} + \underbrace{T\,c_t + V\,c_{vl}}_{\text{tokens}}$$

with an observed retry rate \(r \approx 0.35\). A hard ceiling refuses *new* spend while letting
in-flight work finish. The **Frame Gate** inverts the economics — rejecting a $0.02 still instead of
a $0.30 clip makes a rejection roughly 15× cheaper — and version stacks turn retakes into coverage
instead of waste: flip the current-take pointer and the final re-assembles for $0.00 (verified;
subtitle tracks are cached).

Before building, we benchmarked 20+ mature systems — LTX Studio, Runway, Google Flow, a Sora
post-mortem, ShotGrid/ftrack/Frame.io, ComfyUI, Temporal, 即梦/可灵/Vidu — and encoded their consensus
into the design: asset-first casting, structure-before-render gates, price-before-generate, and a
ShotGrid-style shot lifecycle (`draft → rendering → review → approved → locked`).

## Challenges we ran into

1. **Undocumented protocols.** The docs said keys look like `sk-…`; ours was `sk-ws-…` and returned
   401 until we bisected two gateways. Wan2.7's i2v `media` schema wasn't documented anywhere — we
   discovered `first_frame` / `last_frame` / `driving_audio` by reading validator errors like tea leaves.
2. **Parallel uploads timed out.** Base64 reference frames (~2 MB each) saturated the uplink at
   4-way parallelism. Fix: downscale + JPEG (7–16× smaller), retry with backoff, cap parallelism at 3.
3. **Our ffmpeg had no libass and no drawtext** — no subtitle filter at all. So we built our own
   renderer: Pillow draws bilingual cue PNGs (CN large / EN small, outlined), composited with the
   `overlay` filter. It ended up more controllable than `force_style` ever was.
4. **Content filters.** Crime-adjacent imagery tripped Wan's censor mid-run. The storyboard prompt now
   directs "suggestive, not graphic", and every failure fails open to the best prior take.
5. **We burned the entire free video quota mid-hackathon.** Instead of stalling us, it forced the best
   architecture decisions: resume-from-checkpoint, subtitle caching, version-stack re-assembly and the
   whole no-quota control plane were built and verified at $0.

## Accomplishments that we're proud of

- A critic that actually corrects: character-consistency **1 → 9** in one autonomous retry
- Same face across every shot of a drama, from a single locked portrait — no fine-tuning, no LoRA
- Four finished dramas produced end-to-end, including one with **zh/en/es** subtitle tracks
- A $0.00 re-edit path: switching takes re-assembles the final without regenerating anything
- Production hardening rarely seen in hackathon builds: bearer-token auth, a single job queue,
  budget admission control, health checks, Dockerfile, and AIGC compliance labeling

## What we learned

- **Reliability engineering is the product.** The critic loop, fail-open fallbacks and budget
  admission matter more than any single model's raw quality.
- **One reference frame beats a paragraph of description** for character consistency.
- **The cheapest artifact that can absorb a rejection should come first** — storyboard text, then a
  $0.02 still, then a $0.30 clip.
- **Film industry patterns transfer.** A 40-year-old VFX shot lifecycle maps perfectly onto AI generation.

## What's next

Light up Qwen-Image first-frames and Qwen-TTS dialogue with `driving_audio` lip-sync (interfaces
already wired), one-click English dubbing for the ReelShort-style overseas market, and OTIO export
into professional editing suites.

<!-- ✂ CUT TO HERE -------------------------------------------------------- -->

---

## FIELD 2 · "Built with" — enter these tags

```
python, fastapi, pydantic, asyncio, httpx, openai-sdk, javascript, html5, css3,
qwen3.7-max, qwen-vl, wan2.7, qwen-image, qwen-tts, dashscope, alibaba-cloud,
ecs, docker, ffmpeg, pillow, uvicorn, nginx, agentic-workflow, multimodal, sqlite
```

## FIELD 3 · "Try it out" links

| URL | Label |
|---|---|
| `https://github.com/Yanjin-ai/showrunner` | Source code (public) |
| `http://<ECS-IP>:8000` | Live studio on Alibaba Cloud ECS — fill in after deploy |

## FIELD 4 · Video demo

Upload `docs/devpost/demo_reel_draft.mp4` to YouTube (unlisted is fine) and paste the link — or
record the narrated 3-minute version per `docs/DEMO_SCRIPT.md` and use that instead.

## FIELD 5 · Image gallery

Upload `docs/devpost/gallery/01…08.png` in numeric order (all 3:2, under 5 MB).
