# AI Showrunner — Product Spec (locked)

## One line
A **reusable virtual-production kit for vertical short drama**: build a cast + style + world
once, and every future generation reuses them — so output is consistent *and continuable*.

## The unit is the ASSET, not the episode
We do **not** fixate on season/episode counts. The durable thing is a persistent **Asset Library**:
- **Character** — locked reference portrait (reused as i2v `first_frame`) + per-language voice + wardrobe/props.
- **Style DNA** — grade / lighting / lens / negative, baked into every prompt.
- **World element** — recurring locations/props.

Any generation (a shot, a scene, next week's chapter) references assets by id, and newly minted
characters are written back to the library for reuse. This is the moat: **guaranteed continuity + continuable production.**

## Full-modality pipeline (all on QwenCloud)
```
brief ─► Planner(Qwen3.7-Max, 四拍 Hook/Friction/Spike/Button)
      ─► Asset Library: reuse or mint  { portrait (Qwen-Image) · voice (Qwen-TTS) }
      ─► per shot: PromptWriter ─► Video i2v(Wan/HappyHorse, first_frame=locked portrait)
                                 ─► Voice(Qwen-TTS) ─► Lip-sync(i2v driving_audio)
                                 ─► Critic(Qwen-VL, 3-frame) ─► retry ≤2
      ─► Editor(ffmpeg: concat · voice track · music bed · bilingual subs · cover)
      ─► Localize/Dub(zh↔en) ─► final.mp4
```

## Narrative engine (short-drama craft, encoded)
Four-beat per unit: **Hook (0–15s, detonate)** → **Friction (15–60s)** → **Spike (60–90s, reversal)**
→ **Button (last 5–10s, cut on the question)**. Two central characters. "Lives in faces, not locations."

## Modality → model placement
| Modality | Model | Role |
|---|---|---|
| Text reasoning | Qwen3.7-Max | bible / beats / storyboard / translation |
| Vision-language | Qwen3.6-Plus | 3-frame QA |
| Image gen + edit | Qwen-Image-2.0-Pro | locked portraits + I2I first-frames |
| Video I2V | HappyHorse-1.1-I2V / Wan2.7 | shots from locked portrait |
| TTS voice | Qwen-TTS / Qwen3-TTS-Flash | dialogue + narration + **dubbing** |
| Lip-sync | i2v `driving_audio` | talking faces |
| Music/SFX | (not on QwenCloud) | royalty-free bed |

## Target market
**Bidirectional**: Chinese master production → one-click English dub + multi-language subs (出海).

## Control: what the user gives vs what the system configures
- **User (progressive, min one line)**: premise + genre template + market/language + **budget cap**; optional: reuse existing library characters, style refs, a written script.
- **System**: model roster per modality, budget guardrails, four-beat genre template, style sheet, output specs (9:16), localization languages.

## Human-in-the-loop (maps to the real 10-person AI-drama team)
Producer (greenlight + budget) · Writer (approve bible + beats) · AI asset curator (pick/lock portraits & voices)
· AI director (spot-fix shots). Everything between gates is autonomous.

## Cost
Video is ~95% of spend. Every call is metered ([cost.py](../showrunner/cost.py)); a budget ceiling hard-stops a run.
