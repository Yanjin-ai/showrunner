![AI Showrunner — one line in, a finished vertical drama out](https://raw.githubusercontent.com/Yanjin-ai/showrunner/main/docs/devpost/gallery/01_hero.png)

## Inspiration

China's vertical short-drama industry now ships roughly **470 AI-generated dramas every day** — and the studios describe their own workflow with a gambling word: _抽卡_, "pulling cards." Thirty takes per shot. Pray one lands.

The generators are already good. What's missing is everything **around** them: the thing that keeps an actress's face identical across eight shots, that rejects a bad take _before_ it burns money, that lets a human bless the story before a single frame exists.

Film solved this problem a century ago. The solution is called **a studio**.

So we built one. AI Showrunner plans like a screenwriter, shoots like a director, reviews like a script supervisor, and counts money like a line producer.

## What it does

**One line in. A finished 9:16 drama out.**

Hand it a logline — _"the night-shift clerk sees herself on the security feed, doing things she has never done"_ — and it will:

- Write a **four-beat script** (Hook → Friction → Spike → Button, the pacing grammar of vertical drama), a story bible and a storyboard — pausing at **human approval gates** before money moves
- Cast from a **reusable character library**: one locked portrait drives every shot through image-to-video — measured face consistency of **9–10 / 10**, with no fine-tuning and no LoRA
- Shoot every take, then **judge its own footage**: a Qwen-VL critic scores three sampled frames per take and writes the revision note for a targeted retry — fully autonomously
- Run a real **production office**: the exact price quoted _before_ the Start button, a hard budget ceiling, per-shot lifecycle states (`draft → review → approved → locked`), and version stacks where switching takes re-cuts the final for **$0.00**
- Deliver like a distributor: bilingual burned-in subtitles, zh / en / es tracks from one master script, auto cover art, and China-compliant **AIGC labeling**

![Every take judged, every retry targeted](https://raw.githubusercontent.com/Yanjin-ai/showrunner/main/docs/devpost/gallery/04_the_critic.png)

_The critic at work: narrative / consistency / quality scores on every take — Regen, Extend, Jump, Lock on every shot._

## How we built it

**Everything generative runs on QwenCloud.** Qwen3.7-Max plans, storyboards and localizes. Qwen-VL judges. Wan2.7 t2v/i2v renders. We reverse-engineered the undocumented i2v reference protocol — the locked portrait travels inline as a base64 `first_frame`, so the entire system needs **zero object storage**.

The spine is **FastAPI plus a plain-Python orchestrator**: three-way parallel shot generation, three human gates with timeout auto-approve, Pydantic contracts on every artifact, an append-only event log. Every intermediate is replayable JSON — any single shot re-runs without touching the rest of the production.

**Quality is a funnel, not a hope.** A free ffprobe precheck (decodes? right duration? not near-black?) runs before a single vision-model token is spent. Then the critic gates each take:

$$ \text{pass} = (\text{narrative} \ge 5) \land (\text{consistency} \ge 6) \land (\text{quality} \ge 6) $$

In one real run the critic noticed the wrong character in frame, wrote its own revision note, and drove the consistency score from **1 to 9** in a single retry.

**Cost is governed, not observed.** Every model call passes through one metered choke point, and a production is priced before it begins:

$$ E[\text{cost}] \approx S(1+r)\,c_{video} + (S+C)\,c_{image} + T\,c_{text} + V\,c_{VL} $$

with an observed retry rate of \\( r \approx 0.35 \\). The **Frame Gate** inverts the economics — rejecting a $0.02 still instead of a $0.30 clip makes saying "no" roughly **15× cheaper**. And version stacks turn retakes into _coverage_ instead of waste: flip the current-take pointer and the final re-assembles free.

Before writing a line of code we benchmarked twenty-plus mature systems — LTX Studio, Runway, Google Flow, a Sora post-mortem, ShotGrid, ComfyUI, 即梦, 可灵 — and folded their consensus into the design: asset-first casting, structure before render, price before generate, and a VFX-style shot lifecycle.

![One locked portrait drives every shot](https://raw.githubusercontent.com/Yanjin-ai/showrunner/main/docs/devpost/gallery/05_the_cast.png)

_Consistency you can measure: one portrait from the cast library, the same face in every shot, scored 9–10 by the critic._

## Challenges we ran into

**The undocumented API.** The docs promised `sk-` keys; ours began `sk-ws-` and returned 401 until we bisected two gateways. Wan2.7's image-to-video schema was documented nowhere — we learned `first_frame` by reading validator errors like tea leaves.

**Physics.** Four parallel 2 MB base64 portrait uploads saturated the uplink and timed out. The fix: downscale + JPEG (7–16× smaller), exponential backoff, parallelism capped at three.

**An ffmpeg with no subtitle filter at all** — no libass, no drawtext. So we built our own renderer: Pillow paints bilingual cue cards, ffmpeg `overlay` composites them onto the cut. It ended up _more_ controllable than libass ever was.

**The censor.** Crime-adjacent imagery tripped Wan's content filter mid-run. The storyboard prompt now directs _"suggestive, not graphic,"_ and every failure fails open to the best surviving take.

**We burned the entire free video quota mid-hackathon.** It was the best thing that ever happened to the architecture: resume-from-checkpoint, subtitle caching, $0.00 re-assembly and the whole no-quota control plane were designed, built and verified without spending another cent.

## Accomplishments that we're proud of

- A critic that actually corrects: **consistency 1 → 9** in one autonomous retry
- The same face in every shot of a drama, from a single locked portrait
- Four finished dramas produced end-to-end — one carrying **zh / en / es** subtitle tracks
- The **$0.00 re-edit**: switch takes, re-cut the final, spend nothing
- Hackathon code with production manners: bearer-token auth, a serialized job queue, budget admission control, health checks, Docker, and AIGC compliance labeling

## What we learned

- **Reliability engineering is the product.** The critic loop, the fail-open fallbacks and the budget gate will outlive any single model's raw quality.
- **One reference frame beats a paragraph of prose** when you need to keep a face.
- **Let the cheapest artifact absorb the rejection** — storyboard text first, then a $0.02 still, then a $0.30 clip. Never the reverse.
- **Film's forty-year-old patterns transfer perfectly.** We didn't invent our shot lifecycle; we borrowed ShotGrid's.

## What's next for AI Showrunner

Qwen-Image first frames and Qwen-TTS dialogue with `driving_audio` lip-sync — the interfaces are already wired and waiting on quota. Then one-click English dubbing for the ReelShort-style export market, and OTIO export into professional editing suites.

**Source:** [github.com/Yanjin-ai/showrunner](https://github.com/Yanjin-ai/showrunner) — including a complete replayable production in [samples/night-shift-double](https://github.com/Yanjin-ai/showrunner/tree/main/samples/night-shift-double): story bible → shots → EDL → final cut with three subtitle tracks.
