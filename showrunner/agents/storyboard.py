"""Storyboard: scene beats -> concrete ShotSpecs with real cinematic language."""
from showrunner.clients import qwen
from showrunner.schemas import StoryBible, ShotSpec

SYSTEM = """You are a director translating scenes into shots. You speak film grammar:
景别 (shot size), 机位 (camera position/movement), blocking, continuity. Each shot is a single
generatable clip (2-8s). You keep continuity of wardrobe, props, and lighting across neighbors."""

TEMPLATE = """Story bible:
title: {title}
style: {style}
characters: {chars}

Break these scenes into a shot list ({shots_per_scene} shots per scene). Vary shot sizes and
camera work for rhythm; put the strongest hook shot first. Give MOST shots a short spoken line
(a hook, a clue, or the twist reveal) written in {master_language}; leave dialogue empty only for
purely visual beats. Keep action suggestive, not graphic (avoid blood/gore) to pass content filters.

SCENES:
{scenes}

Carry each scene's beat_role onto its shots. The very last shot must serve the "button" beat and
cut on the question. Bias toward close-ups of faces ("short drama lives in faces, not locations").

Return JSON: {{"shots": [
  {{"id": "s0_sh0", "scene_index": 0, "shot_index": 0, "beat": "hook/friction/spike/button",
    "shot_size": "wide/medium/close-up/extreme close-up/over-the-shoulder",
    "camera": "static/slow dolly-in/handheld/pan/crane — pick purposefully",
    "characters_present": ["char_id", ...],
    "action": "the single beat this shot delivers",
    "emotion": "dominant emotion",
    "dialogue": "master-language line or empty",
    "continuity": "props/lighting/wardrobe that must match neighbor shots",
    "duration": 5 }}
]}}"""


def storyboard(bible: StoryBible, scenes: list[dict], *, shots_per_scene: int = 2,
               master_language: str = "Chinese") -> list[ShotSpec]:
    chars = "; ".join(f"{c.id}={c.name} ({c.appearance})" for c in bible.characters)
    scenes_txt = "\n".join(
        f"- scene {s.get('index', i)} [{s.get('beat_role','')} {s.get('t','')}] @ "
        f"{s.get('location','?')} ({s.get('time_of_day','?')}): "
        f"{s.get('beat','')} | tension: {s.get('tension','')}"
        for i, s in enumerate(scenes)
    )
    out = qwen.chat_json(
        TEMPLATE.format(title=bible.title, style=bible.style, chars=chars,
                        shots_per_scene=shots_per_scene, scenes=scenes_txt,
                        master_language=master_language),
        system=SYSTEM,
    )
    return [ShotSpec.model_validate(s) for s in out["shots"]]
