# Runway (Gen-4 era, 2025–2026) — Interaction Design Research

> Method note: help.runwayml.com blocks direct fetches (403); articles were fetched via Zendesk's
> public API (`help.runwayml.com/api/v2/help_center/en-us/articles/<id>.json`) — full bodies verified.

## Sources (fetched & verified)

- https://help.runwayml.com/hc/en-us/articles/33545310653203-Generating-with-Sessions
- https://help.runwayml.com/hc/en-us/articles/24298206897043 (Navigating Runway / dashboard)
- https://help.runwayml.com/hc/en-us/articles/37053594806419-Creating-with-Gen-4-Image
- https://help.runwayml.com/hc/en-us/articles/40042718905875-Creating-with-Gen-4-Image-References
- https://help.runwayml.com/hc/en-us/articles/37327109429011-Creating-with-Gen-4-Video
- https://help.runwayml.com/hc/en-us/articles/34170748696595-Creating-with-Keyframes-on-Gen-3
- https://help.runwayml.com/hc/en-us/articles/34926468947347-Creating-with-Camera-Control-on-Gen-3-Alpha-Turbo
- https://help.runwayml.com/hc/en-us/articles/42311337895827-Creating-with-Act-Two
- https://help.runwayml.com/hc/en-us/articles/41748090660499-Creating-Multi-Character-Dialogues-with-Act-Two
- https://help.runwayml.com/hc/en-us/articles/51683104370451-Creating-with-Edit-Studio (Aleph 2.0)
- https://help.runwayml.com/hc/en-us/articles/15124877443219-How-do-credits-work
- https://help.runwayml.com/hc/en-us/articles/18053095835795-Unlimited-plan-details (Explore Mode)
- https://www.datacamp.com/tutorial/runway-gen-4
- https://www.datacamp.com/tutorial/runway-aleph

Search-verified only: Gen-2 deprecation (Motion Brush), runwayml.com/research/introducing-runway-gen-4, Aleph research page, Runway Academy.

## 1. Workspace structure

Three areas: **Sessions, Dashboard, Assets**.
- **Dashboard** = hub: Create shortcuts, Assets (Private/Shared/Favorited), community showcase, billing.
- **Sessions** are both the generative workspace and org unit; auto-created on first generation,
  **auto-named from the first prompt**, recency-ordered. **Deleting a session never deletes assets.**
- Left nav creation modes: **Custom / App / Agent / Workflow**.
- Canvas: prompt box + input canvas left; model selector bottom-left; outputs stack **chronologically
  in a right-hand pane** (chat-transcript metaphor). Gen-4 Image: 1000-char prompt, batch 1/4,
  Aesthetic Range slider 0–5, fixed-seed toggle; hover output → **Use** / **Vary**.
- **Projects** are Enterprise-only.

## 2. Gen-4 References (consistency machinery)

- Up to **3 active references**; drag-drop or pick from Assets; toggle in prompt bar.
- Ephemeral by default; hover → **"tag to save"** → named reference → **@-mention autocomplete in
  prompts** (`@bryan driving a car. @jess in the passenger seat. night.` — official example).
- Saved reference: rename, **Share with Workspace** (team character library), remove.
- **"Reference for image"** promotes any output back into a reference — outputs become inputs;
  this is how identity locks across a production.

## 3. Keyframes

- Gen-3 Alpha: first OR last frame. Gen-3 Alpha Turbo: **First/Middle/Last** slots (retiring 2026-07-30).
- **Gen-4 Video: first-frame input only, mandatory** (no T2V); prompt describes motion only;
  5s/10s durations; 6 aspect ratios; fixed-seed toggle.
- Interpolation advice: similar keyframes = smooth; wild jumps = experimental; use 10s for big transitions.
- Output hover **"Use" menu**: Act-Two input, Retime, Expand, **Use Current Frame** (official
  last-frame chaining for extending shots), Upscale 4K.

## 4. Camera control & Motion Brush

- **Advanced Camera Control** (Gen-3 Alpha Turbo, "Legacy" group): camera icon → six axes
  (Horizontal/Vertical/Pan/Tilt/Zoom/Roll), sliders **−10..+10** (sign=direction, magnitude=intensity),
  **Static Camera** checkbox; combinable axes. Intensity is scene-relative.
- **Motion Brush is dead** (Gen-2 only; deprecated 2025-05-11) — replaced by prompt adherence.

## 5. Act-One / Act-Two performance capture

- Apps → Video → Performance Capture. Inputs: **driving performance** (webcam or video; carries motion,
  expression, gestures, **and audio → lip sync**) + **character** (image or video; image → Gestures
  toggle; video → face-only transfer, loops with boomerang).
- **Facial Expressiveness slider** (default 3; higher = expressive but artifact-prone).
- **Duration modal shows credit cost before Generate** — 5 credits/sec, 3s minimum, up to 30s, 24fps.
- **Multi-character dialogue recipe**: one performance per actor → Gen-4 Image two-shot with @refs →
  10s ambient base clip → crop per character → Act-Two per character → composite in NLE.

## 6. Aleph / Edit Studio (in-context editing)

- Edit Studio flow: pick keyframe on timeline → prompt the frame edit (action-verb grammar: add/remove/
  change/replace/re-light/re-style; optional reference; model dropdown) → **Prompt versions tray**
  with before/after preview — **approve the still before paying for video** → optional Extra-motion
  prompt → optional **ranged edits** (billed only for touched span) → generate; versions feed stacks.
- Cost: keyframe edits 5–20 credits/image; Aleph 2.0 video 28 credits/sec.

## 7. Credits & cost UX

- Per-second per-model rates: Gen-4 12/s, Gen-4 Turbo 5/s, Gen-3 Alpha 10/s, Act-Two 5/s, Aleph 28/s;
  images 5–8 credits.
- Plans: Free 125 one-time; Standard 625/mo; Pro/Unlimited 2,250/mo; Max 9,500/mo (1-mo rollover).
- Cost shown **before** generation (duration modal); ranged edits scope the charge.
- **Explore Mode** (relaxed queue, no credits) vs **Credits Mode** (fast) — top-right switcher;
  at concurrency cap the Generate button greys out instead of erroring.

## Patterns worth stealing for a short-drama tool

1. **Named, @-mentionable character references as first-class objects** — cast sheet: tag once,
   autocomplete everywhere, share to workspace, promote outputs back into the library.
2. **Session-as-chat-transcript with per-output "Use" routing** — chains shot → last frame → next
   shot without leaving the flow (exactly the extend-and-continue loop a 60–90s episode needs).
3. **Cheap-preview-before-expensive-commit** — approve a 5–20-credit still before 28-credit/sec video;
   show exact price in a confirm modal; bill only the edited range.
4. Bonus: **direction + signed-intensity slider grid** for camera language without prompts.
