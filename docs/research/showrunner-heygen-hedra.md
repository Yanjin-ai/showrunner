# Fable Showrunner + HeyGen / Hedra — Interaction Design Research

## A. Fable Studio Showrunner (showrunner.xyz)

The closest product to "AI TV": alpha launched 2025-07-30 (~10k alpha users, ~100k waitlist,
Amazon Alexa Fund invested — "the Netflix of AI").

### Creation flow (Discord alpha, verified via two tutorials)
1. showrunner.xyz → Join → Discord server → pick a world (e.g. *Exit Valley*) → #create-N channel.
2. **`/scene` slash command opens a STRUCTURED FORM**: Character 1, Character 2, (optional 3),
   Setting, scene description/conflict, optional visual filter + action verbs.
3. Auto-generates a fully animated scene (visuals + dialogue + voices + pacing); MP4 from Discord.
- "10–15 word prompt → 2–16 min episode" is really the scene-description field of this form.
- **Character Lab**: upload photo + traits, select/upload voice, backstory → custom character.

### Scene-level editing (the key mechanism)
Line-by-line **script editor** after generation:
- rewrite dialogue lines directly;
- **per-line voice tone tags** (angry, anxious, neutral, sarcastic, confused);
- **per-line camera directives** (zoom, pan, shake, cut, Dutch angle; hide/reveal characters);
- timing (pauses, cuts); then **re-generate the scene** as the commit action.

### SHOW-1 paper (fablestudio.github.io/showrunner-agents)
Episode = **14 scenes**; each scene = exactly {location, cast, dialogue}. User steering = synopsis +
major events per scene. Multi-agent simulation supplies character state (relationships, emotions,
time) as prompt context; a separate **staging system + AI camera system** picks shots after dialogue
generation; voice clips per dialogue line via cloned voices.

### Business model
Canonical Season 1 of *Exit Valley* = 22 episodes, part Fable-made, part user-made selected by a
filmmaker jury; **creators earn revenue when others generate using their IP/world**. Planned
$10–20/mo credit subscription.

### Patterns worth stealing
1. **Line-as-atomic-edit-unit**: each dialogue line = {text, speaker, tone, camera, timing} row;
   QA/edits happen in script-space, scene re-renders. Cheap to diff, cheap to regenerate.
2. **Structured scene form** instead of a blank prompt box (characters/setting/conflict as fields).
3. **Canonical season + remixable world** with jury-curated UGC + IP revenue share (content flywheel).

## B. HeyGen

### AI Studio layout (help.heygen.com, verified)
**Left**: Script panel ("everything starts here"; edit text / Upload Audio / AI Scriptwriter).
**Center**: canvas (current scene frame). **Bottom**: scene cards timeline (PowerPoint metaphor,
not track-based NLE). **Right**: Avatar / Voice / AI Tools / Media / Captions / Layers.

- **Digital Twin**: 30s–5min footage ≥1080p30 + mandatory **consent video (≤35s)**, face-matched.
- **Avatar IV (photo→video)**: upload photo → script or audio → voice → Generate; supports cartoon/3D;
  custom motion prompt costs 2× credits.
- **Voice**: Library or "+ New Voice" → Instant Clone / designed voice; per-voice accent/tone/speed/engine;
  voice bound per avatar per scene.
- **Dubbing**: Speed vs Precision (2×) modes; **"Proofread" review-and-edit gate** — word-by-word
  edit of the translated script BEFORE final render (cannot edit after).
- **Video Agent** (2025, app.heygen.com/video-agent): topic/audience/tone → 2–5 min "thinking" →
  **editable PLAN (scene breakdown + script + music + captions)** → user edits → Create renders;
  everything stays editable in Studio afterwards without full regen.
- Credits: ≈1 credit = 3s avatar generation; **billed only on seconds of actual avatar generation,
  not silence**; plans Free/$29/$49/$149.

## C. Hedra

- **Character-3**: omnimodal (image+audio+text jointly) — lip-sync, micro-expressions from one still.
- Studio flow: portrait (upload or generate; **9:16 full-body supported**) → audio via **4 inputs**
  (built-in TTS / ElevenLabs / upload / mic; saved to reusable asset library) → duration auto from
  audio length → generate → preview → MP4/WEBM.
- Pivoted to **multi-model studio** (~14 image + ~14 video models incl. Sora 2 Pro) on **one credit
  balance**; per-second billing on generated length (Character-3: 3 cr/s @540p, 6 @720p; Sora 2 Pro
  up to 70 cr/s; audio 15 cr/1k chars). Live Avatars: sub-100ms streaming, $0.05/min, pluggable LLM+TTS.

### Patterns worth stealing
1. **HeyGen scene-cards + script-first editing** — editing a scene's script regenerates only that scene.
2. **HeyGen Agent plan-approval checkpoint + Proofread gate** — cheap-to-review before expensive render.
3. **Hedra character-as-asset** — face + bound voice reusable across scenes; transparent per-second cost.

### Verified URLs
showrunner.xyz · fablestudio.github.io/showrunner-agents · forbes.com (2025-07-30 Exit Valley launch)
· evolutionaihub.com/how-to-use-showrunner-create-free-ai-tv-shows · bizrescuepro.com/showrunner-ai-…
· help.heygen.com/en/articles/11269603 (Avatar IV) · help.heygen.com/en/articles/11049655 (AI Studio)
· magichour.ai/blog/guide-to-hedra-ai · hedra.com/pricing
Search-verified: variety.com (Amazon invest, $10–20/mo), heygen.com/blog/video-agent-prompt-guide,
help.heygen.com 12089286/12092609/11202248/10029081/15125761, heygen.com/pricing, hedra.com/plans
