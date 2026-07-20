# LTX Studio — Interaction Design Research (closest comp)

Compiled July 2026. Site migrated ltx.studio → ltx.io; help center is behind the app.

## Sources (fetched)
- https://ltx.io/blog/ltx-studio-tutorial (2026-03-24) — Projects, Gen Space, Storyboard, Retake, Elements
- https://ltx.io/blog/ltx-storyboard-generator-update (2026-01-06) — rebuilt storyboard flow
- https://ltx.io/blog/top-ltx-studio-features (2026-01-22)
- https://ltx.io/blog/how-to-create-a-consistent-character (2025-07-28) — exact button names
- https://ltx.io/blog/how-to-storyboard (2026-05-01) — panel anatomy, breakdown review step
- https://ltx.io/blog/mastering-camera-motion-gen-space (2025-10-20) — camera presets
- https://ltx.io/studio · /studio/platform/shot-video-editor · /studio/platform/ai-storyboard-generator · /pricing
- Third-party: uraiguide.com/ltx-studio-guide/ · vijaytalksai.com/ltx-studio-review/ · gaga.art/blog/ltx-studio-complete-guide/

## 1. Project structure
- **Project** = top container with four connected workspaces: **Gen Space** (generation), **Storyboard**,
  **Timeline** (editing), **Pitch Deck**. Generations group into nameable **Sessions**.
- Four starting points: From Script / With a Concept / From an Image / From a Video.
- **Script → structure with a review gate**: parses screenplay into scenes→shots and SHOWS the editable
  structure (scene count, shots per scene, script text per shot) BEFORE rendering anything; merge scenes /
  split shots / add beats at this stage — "this is where the budget is protected" (official).
- Script stays attached to panels; regenerating one panel never touches neighbors; storyboard editing is
  **non-destructive** (panels reference generations, don't own them).
- Init settings: idea → image model picker (FLUX / Nano Banana / Z-Image) → aspect (16:9/9:16/1:1/4:5,
  locked project-wide) → review auto-extracted Elements → Generate.
- Scene Settings panel per scene: Location, Lighting dropdown, Weather, Voiceover text, Scene Sound.

## 2. Elements (Cast evolved) — consistency machinery
Types: **Character, Location, Object, Other**; characters carry an assigned **voice**.
- Create path A: Elements → Create New Element → Character → generate/upload image → description →
  name (`@Detective_Martinez`) → assign voice → Save.
- Create path B: any generation → Tools menu → **"Save as Element"** (available across all projects).
- **@-tagging** in any prompt/shot field with autocomplete; storyboard generator **auto-extracts and
  auto-binds** recurring script mentions to the same Element.
- **Wardrobe variants**: character → Duplicate → edit 'Clothing style'/'Main outfit' → rename
  (`@Sarah_casual` / `@Sarah_formal`); identity persists.
- **Replace Image** propagates to every tagged shot ("update once, propagate everywhere"); **Face Switch**
  swaps face keeping body/clothing/composition.
- Reference guidance: 5–12 images, close-up + full-body mix, frontal, neutral background, even light.
- Reality check (reviews): faces can still drift slightly even with Elements.

## 3. Storyboard
- Panel = frame image + one-sentence shot description + camera direction + dialogue/VO + cast ref + location ref.
- Tap any panel to regenerate / swap model / rewrite description without touching the rest.
- Drag-to-sequence, per-clip duration + transition. Free tier = blank storyboards; **AI storyboards are
  the paid unlock** (Standard+). Real-time collaboration + comment-only stakeholders.

## 4. Per-shot regeneration & edit controls
- **Retake (flagship)**: select any **2–16s segment** in a generated video → new prompt for just that
  span → regenerate; model attends to surrounding frames. "Reach for Retake before returning to the
  prompt" — marketed as the credit-saver.
- **Camera Motion Presets** under the prompt field: Static, Handheld, Dolly In/Out, Crane Up/Down, Pan,
  Tilt, Dolly Zoom, Whip Out; zero-prompt, combinable with a motion prompt.
- **Keyframes**: start/end conditioning + multi-keyframe control points; Prompt Strength slider.
- Region edits (older shot editor): Generative Fill / Remove Object; FPS 8/16/24; duration 3/6/9/12s;
  Frame-vs-Character motion-target toggle; **separate Generate (preview) vs Apply (commit) buttons**.
- History: full prompt history per Session; revision rollback. No user-facing seeds.

## 5. Style consistency
- Style module presets (Cinematic/Sketch/Branded/Documentary/Experimental); customizable at
  **project, board, and frame levels**; reference-image steering; **Brand Kit** = global style lock.
- Image-model choice per board is itself a style decision; panels can swap model individually.

## 6. Timeline, audio, export
- Lightweight timeline: duration/transition per clip, **audio layered directly** (VO, music, SFX);
  narrator vs per-character voices; **Audio-to-Video** — uploaded audio stays LOCKED across
  regenerations while visuals change (audio as source of truth).
- **Animatics** from storyboard frames before spending video credits.
- Export: **MP4, XML (NLE handoff), pitch-deck PDF**.

## 7. Pricing/credits (ltx.io/pricing, 2026-07)
Free $0 (800 one-time credits, watermark, blank boards) · Lite $15/mo (8k) · Standard $35/mo (28k,
premium models incl. Veo 2 / Kling 3.0 Pro / Seedance 2.0, **Elements + AI storyboards + pitch decks
unlock here**, commercial license) · Pro $125/mo (110k, Veo 3.1, 3 collaborators) · Enterprise (custom
model training, org credit allocation). Real-time credit balance; Retake marketed as credit-saver.
Gating insight: generation is free-tier; **consistency (Elements) and pre-production automation are
the paid unlock**.

## Patterns worth stealing
1. **Structure-first, render-later ("shot breakdown review gate")** — full editable scene/shot structure
   shown before a single frame is generated; restructure at zero cost; non-destructive panels.
2. **@-taggable asset entities** with auto-extraction from script, **Duplicate-for-wardrobe variants**,
   and update-once-propagate-everywhere (Replace Image / Face Switch).
3. **Segment-scoped regeneration (Retake) as the default fix** + Generate-vs-Apply preview/commit split —
   "direct retakes", don't reroll scenes; directly reduces credit burn.
4. Bonus: aspect locked at project init (hard-default 9:16 + safe-area overlays for vertical);
   Audio-to-Video's locked-audio inversion for dialogue-heavy drama.
