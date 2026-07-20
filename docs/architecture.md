# Architecture

![AI Showrunner architecture](../assets/architecture.svg)

AI Showrunner turns a one-line brief into a finished vertical short drama through a
planner → orchestrator → executor → critic loop, with every intermediate artifact stored as
replayable JSON so any single shot can be regenerated in isolation.

```mermaid
flowchart TD
    B[One-line brief] --> P[Planner · Qwen3.7-Max]
    P -->|StoryBible + scene beats| G1{HITL gate: outline}
    G1 -->|approve| S[Storyboard · Qwen3.7-Max]
    S -->|ShotSpec JSON per shot| G2{HITL gate: storyboard}
    G2 -->|approve| ORCH[Orchestrator · async state machine]

    subgraph LOOP[Per-shot · parallel · self-correcting]
      direction TB
      PW[PromptWriter<br/>appearance + style baked in] --> EX[Executor<br/>HappyHorse / Wan · async task+poll]
      EX --> CR[Critic · Qwen-VL<br/>score frame vs ShotSpec]
      CR -->|pass| KEEP[keep clip]
      CR -->|fail ≤2x| PW
    end

    ORCH --> LOOP
    KEEP --> ED[Editor · ffmpeg<br/>normalize → concat]
    ED --> LOC[Localizer · Qwen<br/>N-language subtitle tracks]
    LOC --> G3{HITL gate: final cut}
    G3 --> OUT[final.mp4 · burned + soft subs · cover.png]

    ORCH -.events.-> DASH[FastAPI + live dashboard]
    P -.artifacts.-> ST[(runs/ JSON store)]
    ST -.-> DASH
```

## Why each piece exists (mapped to judging criteria)

| Judging axis | Where we earn it |
|---|---|
| **Technical Depth (30%)** | Async task/poll video pipeline, parallel shot generation, bounded critic/retry loop, Pydantic-validated artifacts, event-sourced state, HITL gate controller with timeout fallback. |
| **Innovation & AI Creativity (30%)** | Closed-loop Qwen-VL critic that drives *targeted* regeneration (not one-shot); character-consistency via reused appearance descriptors / reference-to-video; one-script→N-language localization. |
| **Problem Value & Impact (25%)** | Vertical short drama is a booming global format; auto-localization unlocks cross-market distribution — the real bottleneck for studios. |
| **Presentation & Docs (15%)** | Live dashboard makes the orchestration *visible*; this diagram + deploy proof + replayable runs. |

## Data flow / artifacts (all under `runs/<id>/`)

`story_bible.json` · `scenes.json` · `shots.json` · `shots/<id>_qa<n>.json` ·
`subtitles.json` · `edl.json` · `events.jsonl` (append-only log) ·
media: `shots/*.mp4`, `master.mp4`, `final.mp4`, `cover.png`, `subs_<lang>.srt`.

## Models

| Role | Model | Access |
|---|---|---|
| Planner / storyboard / prompt / localize | `qwen3.7-max` (+`-plus`) | OpenAI-compatible endpoint |
| Critic (vision) | `qwen3.6-plus` (VL) | OpenAI-compatible endpoint |
| Video executor | `happyhorse-1.1-*` / `wan2.7-*` | DashScope async video-synthesis |

All model IDs are env-driven (`.env`) and verified by `scripts/smoke_test.py`.
