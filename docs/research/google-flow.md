# Google Flow (labs.google/flow) — Interaction Design Research

Launched 2025-05-20 (I/O); Veo 3.1 in Flow 2025-10-15; by 2026 a unified "AI Creative Studio"
(Whisk/ImageFX absorbed, Agent mode, Gemini Omni Flash, Nano Banana image models). 275M+ videos.

## 1. Project → clip → SceneBuilder

- **Projects** (persistent, full generation history) contain **clips** (4/6/8/10s per generation),
  assembled into scenes on the **SceneBuilder** timeline ("the in-Flow storyboard").
- Loop: prompt → **2–4 output variants** (each a "stack") → hover → More → **Add to Scene** →
  drag-reorder + **trim handles** per clip → download the scene.
- **Extend**: select clip → Extend → describe how the action continues; generated **from the final
  second of the previous clip** → 60s+ chains. Extended clips can't take other edit modes.
- **Jump To (Add Scene)**: cut to a new setting **while preserving the character/object's appearance**
  (Gemini handles continuity). Launch-era lesson: Extend/Jump To silently downgraded to Veo 2 with a
  "Switching you to a compatible model" toast — users revolted; make capability/cost explicit.
- **History panel** + "Save to Project"; pause any frame → **Save frame** (reusable as ingredient
  or start/end frame — the manual continuity bridge).

## 2. Ingredients & Frames

- **Ingredients to Video**: up to **3 ingredients per prompt** (characters/objects/styles), uploaded
  or generated in-app (Nano Banana), referenced **by plain-language name in the prompt**; saved to
  the project and reused across generations — Flow's cross-shot consistency machinery. Native audio
  since Veo 3.1. 2026 Omni adds **voice references** (Add → Voices) bound to ingredient generations.
- **Frames to Video**: "+ Add start frame" (+ optional end frame) → describe transition → Veo
  interpolates. End-frame-of-A = start-frame-of-B is the standard shot-chaining trick.

## 3. Camera controls (two tiers)

- **Preset UI**: camera icon in prompt box → Dolly In/Out, Pan L/R, Tilt Up/Down (+static/zoom/
  handheld), **with preview of the move before generating**.
- **Prompt vocabulary**: full cinematography language in text. Camera is a clip edit-mode
  (alongside Insert/Remove); not available on extended clips.

## 4. Asset management

- Ingredients drawer next to prompt box; edits auto-save to an **asset's version stack**;
  **Flow TV** public gallery shows the **exact prompts** used (inspiration-as-documentation).

## 5. Prompt box & Agent

- Mode picker: Text / Frames / Ingredients. Settings show model tier (Veo 3.1 Lite/Fast/Quality,
  Omni Flash, Nano Banana 2), aspect (16:9/9:16/1:1), output count, length — **and the current
  credit cost of that exact configuration, before generating**.
- Gemini rewrites everyday language into Veo prompts (recommended structure: subject/action +
  composition/camera + location/lighting + style + audio).
- **Agent mode (2026)**: toggle in prompt box; drag media in; ≤3 conversational refine turns;
  upload external video ≤60s/1GB, select 10s segment; natural-language custom tools.

## 6. Credits UX (official numbers)

- Free 50/day (no rollover); AI Plus $4.99 = 200/mo; Pro $19.99 = 1,000/mo; Ultra $100 = 10k,
  $200 = 25k/mo.
- Per generation (Veo 3.1): **Lite 10 · Fast 20 · Quality 100** (Ultra subs pay 5/10/100);
  same for Extend hops; charged per generation (multi-output multiplies).
- Balance under profile chip; out-of-credits → notification → wait or top up.

## 7. Timeline

2025-05-20 launch → 2025-10-15 Veo 3.1 (audio in Ingredients/Frames/Extend; **Insert** = describe
object + drag a box, Flow handles shadows/lighting; **Remove** coming) → 2026 unified studio,
Omni Flash conversational editing, voice references, 2K/4K upscale by tier, mobile.

## Verified URLs (fetched)

- https://blog.google/innovation-and-ai/products/google-flow-veo-ai-filmmaking-tool/
- https://blog.google/innovation-and-ai/products/veo-updates-flow/
- https://blog.google/innovation-and-ai/products/flow-video-tips/
- https://labs.google/fx/tools/flow
- https://support.google.com/labs/answer/16353333 · /16353334 · /16352836
- https://support.google.com/flow/answer/16935718 · /16526234
- https://huggingface.co/blog/MonsterMMORPG/veo-3-flow-full-tutorial-how-to-use-veo3-in-flow
- https://digiwebinsight.com/google-flow-beginners-guide-veo-videos/ · /flow-camera-controls-explained/
- https://9to5google.com/2025/10/15/veo-3-1/
(2026 third-party guide whiskailabs.net treated as unverified where it contradicts official.)

## Patterns worth stealing

1. **"Extend vs Jump To" as the two primitives of continuity** — the only two buttons a clip needs:
   continue-the-beat (seeded by last second) vs next-scene-same-cast (last frame + character
   ingredients into a fresh generation). Plus the failure lesson: never silently downgrade models.
2. **Ingredients as first-class reusable cast (max ~3/shot)** — "Cast & Props" drawer pinned by the
   prompt box; voice references bound to characters; **Save frame** bridges continuity manually.
3. **Per-action cost inside the generation control** (model×length×count priced before Generate) +
   episode-level estimate; **variant stacks** make retakes feel like coverage, not waste.
