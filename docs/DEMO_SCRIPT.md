# 3-minute demo video — beat sheet

Judges weight Presentation 15% but the video is how they *see* the other 85%. Show the system
working, not slides. Record the dashboard live.

| Time | Beat | On screen | Say |
|---|---|---|---|
| 0:00–0:20 | Hook | The finished 35s vertical drama playing, with subtitles toggling ZH→EN→ES | "One line of input became this — script, shots, video, and three subtitle languages, fully autonomous." |
| 0:20–0:45 | Problem | — | Short-drama studios burn days on scripting→storyboard→shoot→localize. We compress it into one agent. |
| 0:45–1:10 | Plan + HITL | Type brief → dashboard shows StoryBible + characters → the outline gate → approve | "The planner builds a story bible; a human can approve or halt at each gate." |
| 1:10–1:50 | The differentiator | Shot tree filling in parallel; zoom a shot that **failed QA and retried** — show na/cc/tq scores changing | "Each clip is critiqued by Qwen-VL against its shot spec. Weak shots get a *targeted* prompt fix and regenerate. This is the closed loop." |
| 1:50–2:20 | Consistency + edit | Point out the same character across shots; final concat + burned subs appear | "Appearance descriptors carry across every shot for continuity; ffmpeg concatenates and burns subtitles." |
| 2:20–2:45 | Localization value | Switch embedded subtitle tracks on the final video | "One master script, N markets — the real distribution bottleneck, solved." |
| 2:45–3:00 | Architecture + deploy | Architecture diagram, then the dashboard URL on the Alibaba Cloud ECS IP | "Planner–orchestrator–executor–critic, deployed on Alibaba Cloud, every run replayable." |

Tips: pre-generate one flagship run so you can cut to a finished result (generation is 1–5 min/shot).
Keep a second run going live to show the tree animating.
