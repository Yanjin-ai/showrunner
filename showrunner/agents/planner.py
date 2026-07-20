"""Planner: brief -> StoryBible + scene beats. Uses the strongest Qwen model."""
from showrunner.clients import qwen
from showrunner.schemas import StoryBible

SYSTEM = """You are a veteran showrunner for VERTICAL (9:16) short-form dramas — the punchy,
hook-in-first-3-seconds format that dominates mobile.
You write to the proven four-beat engine and end on a cliffhanger button. Structure the conflict
into the premise itself. Two central characters (or one lead + one animal lead); supporting cast
strictly functional. Output production-ready structured data."""

# Genre playbooks: craft guidance + content-safety guidance per template.
GENRES = {
    "悬疑反转": "Urban suspense with a twist. Conflict types: power imbalance / forbidden proximity / "
              "enemies / forced circumstance. Keep imagery suggestive, never graphic (no blood/gore).",
    "霸总情感": "CEO romance. Power-imbalance conflict, charged proximity, one status-flip per unit. "
              "Lush interiors, wardrobe contrast between leads.",
    "复仇逆袭": "Revenge / rise. Humiliation beat early, receipts and reversal later; the button teases "
              "the next counterblow.",
    "甜宠": "Sweet romance. Micro-conflicts resolved with warmth; the spike is an accidental intimacy "
          "or confession; button is an interrupted moment.",
    "萌宠": "Pet drama. An animal lead (fixed breed, coat pattern, collar — describe precisely for "
          "consistency) with a human companion. The pet does NOT talk on screen: its thoughts are a "
          "VOICE-OVER inner monologue (write it in the dialogue field, mark speaker as the pet). "
          "Emotion via animal body language: ears, tail, head tilts. Wholesome, zero dark imagery.",
    "灵异": "Supernatural suspense. Fear by SUGGESTION only: reflections that lag, doors ajar, wrong "
          "shadows, a second reflection — never gore, never monsters on screen (also keeps content "
          "filters happy). Cold light vs one warm source. The button reveals the rule was wrong.",
}

TEMPLATE = """Expand this brief into a short-drama bible.

BRIEF: {brief}
GENRE PLAYBOOK: {genre_guide}
CONSTRAINTS: {n_scenes} scenes, {n_chars} main characters, target ~{seconds}s total, style="{style}".
ALL character dialogue must be written in {master_language}. Character appearance/style stays in English.

Return JSON with EXACTLY this shape:
{{
  "story_bible": {{
    "title": "...",
    "logline": "one-sentence hook",
    "genre": "urban suspense / twist",
    "style": "visual style sheet: grade, lighting, lens feel, vertical framing",
    "characters": [
      {{"id": "slug", "name": "...", "appearance": "DENSE visual descriptors — hair, wardrobe, build, distinctive features (these get reused verbatim in every shot prompt for consistency)", "personality": "...", "role": "protagonist/antagonist/supporting"}}
    ],
    "synopsis": "3-5 sentences, must contain a clear twist"
  }},
  "scenes": [
    {{"index": 0, "beat_role": "hook", "t": "0:00-0:15", "location": "...", "time_of_day": "...", "beat": "the single most cinematic image; detonate, no easing in", "tension": "why they don't scroll"}},
    {{"index": 1, "beat_role": "friction", "t": "0:15-0:60", "location": "...", "time_of_day": "...", "beat": "visible conflict between the two leads in one space", "tension": "..."}},
    {{"index": 2, "beat_role": "spike", "t": "0:60-0:90", "location": "...", "time_of_day": "...", "beat": "one jolt that re-contextualizes everything (the twist)", "tension": "..."}},
    {{"index": 3, "beat_role": "button", "t": "0:90-1:00", "location": "...", "time_of_day": "...", "beat": "cut on the question, NOT the answer — an unresolved cliffhanger", "tension": "makes the next tap automatic"}}
  ]
}}
Rules: exactly the four beats hook→friction→spike→button in order. Front-load the strongest image in the hook.
The button must end unresolved. Keep the two leads visually distinct and describe them densely."""


GENRE_STYLES = {
    "萌宠": "warm golden-hour glow, soft daylight, cozy interiors, gentle handheld, vertical 9:16",
    "灵异": "desaturated cold blue-green, single warm practical light, deep shadows, slow creeping camera, vertical 9:16",
    "霸总情感": "glossy high-key interiors, warm rim light, shallow depth of field, vertical 9:16",
    "甜宠": "pastel warm palette, soft bloom, bright daylight, vertical 9:16",
}
DEFAULT_STYLE = "cinematic noir, cool teal-orange grade, shallow depth of field, vertical 9:16"


def plan(brief: str, *, n_scenes: int = 4, n_chars: int = 2, seconds: int = 35,
         master_language: str = "Chinese", genre: str = "悬疑反转",
         existing_cast: list[dict] | None = None,
         style: str | None = None) -> tuple[StoryBible, list[dict]]:
    genre_guide = GENRES.get(genre, genre or GENRES["悬疑反转"])
    style = style or GENRE_STYLES.get(genre, DEFAULT_STYLE)
    prompt = TEMPLATE.format(brief=brief, n_scenes=n_scenes, n_chars=n_chars, seconds=seconds,
                             style=style, master_language=master_language, genre_guide=genre_guide)
    if existing_cast:  # @-referenced library characters: reuse identity EXACTLY (locked portraits)
        cast_txt = "\n".join(f'- id="{c["id"]}" name="{c["name"]}" appearance="{c["appearance"]}"'
                             for c in existing_cast)
        prompt += ("\n\nREUSE THESE EXISTING CHARACTERS — keep their id, name and appearance "
                   "EXACTLY as given (their look is locked to saved portraits):\n" + cast_txt)
    out = qwen.chat_json(prompt, system=SYSTEM)
    bible = StoryBible.model_validate(out["story_bible"])
    scenes = out["scenes"]
    return bible, scenes
