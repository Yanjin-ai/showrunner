# Kling / Hailuo / Vidu — Interaction Design Research (July 2026)

[F] = fetched directly · [S] = verified via search snippets (kling.ai blocks server fetches)

## 1. Kling AI (kling.ai)
Sources: [S] kling.ai/quickstart/ai-video-character-consistency · /ai-camera-control-guide ·
/ai-lip-sync-guide · /app/membership/membership-plan; [F] atlascloud.ai kling-3.0 review;
[F] heyiastudio.com multi-elements hands-on; [S] pollo.ai elements guide, aitoolanalysis pricing.

- **Layout**: left-nav (AI Videos / AI Images / AI Human / Assets); T2V/I2V tabs; model dropdown
  (1.6/2.x/3.0 Omni); **Standard vs Professional mode toggle**; 5s/10s; ratios; creativity/relevance
  slider; negative prompt; right-side queue/history; paid = priority queue.
- **Camera**: "Camera Movement" panel — six numeric sliders (horizontal/vertical/zoom/pan/tilt/roll,
  ± values, 1–3 recommended), combinable; four one-click **"Master Shots" presets**. Kling 3.0 adds
  Motion Brush paths + **3.0 Omni storyboard tool** (per-shot duration/size/angle/pacing/camera).
- **Multi-Elements Editor** (1.6): select subject in a video → Swap/Add/Delete via text/image;
  50 credits, 3–5 min.
- **Elements consistency**: 1–4 tagged images (person/animal/object/scene); 3.0 Omni: text + 1–2 refs,
  "Omni Elements" reusable library.
- **Lip Sync as post-hoc card action**: on any clip with a face → Lip Sync → TTS (language/voice/speed)
  or upload dub → Generate. **Kling 3.0 generates native audio + lip-synced dialogue in 5 languages.**
- **Credits**: 5s Standard ≈10, Professional ≈35; plans Free 66 / ~$7–10 (660) / ~$26–37 (3000) / Ultra.

**Steal**: two-level camera control (presets + signed sliders); post-hoc Lip Sync as card action.

## 2. Hailuo / MiniMax (hailuoai.video)
Sources: [F] hailuoai.video blog 2.3 · escapism.ai director-mode · aivideobootcamp 2026 guide ·
create/subject-reference page; [S] minimax.io s2v-01 · video-agent · payment policy.

- **Layout**: Create → Video/Image/Assets/Agent; model picker (2.3, 2.3 Fast, 02, 02 Fast, I2V-01-Live,
  T2V-01-Director); 6s/10s; 768p/1080p. Queue policy: free 3 queued/1 parallel; paid 5/2 + accelerated.
- **Director Mode (headline)**: camera as **inline square-bracket DSL** — `[Push in]`, `[Pan left]`;
  12 movements in 6 antonym pairs + [Shake]/[Tracking shot]/[Static shot]; **≤3 moves in one bracket =
  simultaneous; separate brackets = sequential timed to sentence position**. UI: camera icon opens a
  palette — hover-preview, click inserts the tag at cursor (UI writes the DSL, DSL stays editable).
- **Subject Reference (S2V-01)**: one frontal portrait → identity holds across angles/motion;
  "<1% of LoRA cost".
- **Media Agent**: one-click templates → roadmap to semi-customizable (edit script/visuals/VO) → full
  agents; multi-shot storyboards + speech + music assembly.
- **Credits**: 768p 6s = 25, 10s = 50, 1080p 6s = 50; plans $14.99–$199.99; **Max = unlimited Relax
  Mode after credits run out**.

**Steal**: bracket-tag camera DSL + palette insertion; Relax Mode off-peak lane for binge iteration.

## 3. Vidu (vidu.com)
Sources: [F] vidu.com/ai-reference-to-video · gaga.art vidu guide · testingcatalog Q1 update ·
deevid.ai Q2 overview; [S] PRNewswire Q1 7-image / Q2 launch · pricing · tools/lip-sync · aibase Q2.

- **Layout**: four tabs — **Text / Image / Reference / Start-End to Video**; Q2-turbo/pro/pro-fast;
  540p/720p/1080p; **motion amplitude Low/Med/High**; Cinematic vs Lightning toggle;
  **generate button shows live credit cost per current settings** ("12 credits ($0.06)").
- **Reference-to-Video (flagship)**: upload **1–7 reference images** (characters/props/scenes) →
  prompt → Create; semantic engine infers missing elements; stable multi-character interaction.
- **My References** saved library + **RefHub** (pre-made assets) + proven-effect **Templates**.
- **Start-End chaining** = official multi-shot method; Q2: native wide↔close transitions in one
  generation, sequenced beats, ~3x faster, "AI story creation up to 5 minutes".
- **Audio**: model-level dialogue/BGM/SFX at 48kHz alongside visuals; Lip Sync tool (EN/中文/日本語);
  "only charged if applied".
- **Credits**: Free (starter + **unlimited off-peak**) / $10 (800) / $35 (4000) / $99 (8000);
  three credit classes (subscription 30d, purchased 2y, bonus 2y).

**Steal**: My References as cast/prop/set library + 7-subject composition; live credit price in the
Generate button + off-peak free lane.

## Cross-product takeaways
- **Three camera paradigms**: Kling sliders/presets (inspectable) · Hailuo inline DSL (text-native,
  API-friendly) · Vidu model-learned + reference-clip transfer (zero-UI). Best hybrid: palette-inserts-
  visible-tokens + preset tier.
- **Consistency stacks by input count**: Hailuo 1 face < Kling 1–4 tagged < Vidu 7 refs + library.
  Library model scales best to episodic drama.
- **Multi-shot converging on storyboard UIs** + last-frame→first-frame chaining everywhere.
