"""Structured intermediate artifacts. Every agent hop reads/writes these Pydantic
models so any single shot can be re-run without redoing the whole pipeline."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class CharacterCard(BaseModel):
    id: str = Field(description="stable slug, e.g. 'lin_ke'")
    name: str
    appearance: str = Field(description="dense visual descriptors reused in every shot prompt for consistency")
    personality: str
    role: str = Field(description="protagonist / antagonist / supporting")


class StoryBible(BaseModel):
    title: str
    logline: str
    genre: str = "urban suspense / twist"
    style: str = Field(description="visual style sheet, e.g. 'cinematic noir, cool teal-orange grade, vertical 9:16'")
    characters: list[CharacterCard]
    synopsis: str


class ShotSpec(BaseModel):
    id: str = Field(description="e.g. 's1_sh2'")
    scene_index: int
    shot_index: int
    beat: str = Field(default="", description="short-drama beat: hook / friction / spike / button")
    shot_size: str = Field(description="景别: wide / medium / close-up / extreme close-up")
    camera: str = Field(description="机位与运动: static / dolly-in / handheld / over-the-shoulder ...")
    characters_present: list[str] = Field(default_factory=list, description="character ids")
    action: str = Field(description="what happens, the beat this shot delivers")
    emotion: str
    dialogue: str = Field(default="", description="master-language line; empty if none")
    continuity: str = Field(default="", description="props/lighting/wardrobe that must match neighbors")
    duration: int = 5


class ScenePlan(BaseModel):
    scenes: list[dict] = Field(description="scene-level beats; each expands into ShotSpecs")
    shots: list[ShotSpec]


class VideoGenRequest(BaseModel):
    shot_id: str
    mode: Literal["t2v", "i2v"] = "i2v"
    prompt: str = Field(description="positive prompt pack: subject + style + camera + motion + consistency tags")
    negative_prompt: str = "blurry, flickering, distorted face, extra limbs, warped hands, subtitle artifacts"
    ref_image_path: str | None = Field(default=None, description="canonical reference frame for i2v consistency")
    duration: int = 5


class QAReport(BaseModel):
    shot_id: str
    narrative_alignment: int = Field(ge=0, le=10, description="does the clip deliver the ShotSpec beat")
    character_consistency: int = Field(ge=0, le=10, description="does the character match the CharacterCard")
    technical_quality: int = Field(ge=0, le=10, description="sharpness, motion coherence, no artifacts")
    passed: bool
    reason: str
    revision_advice: str = Field(default="", description="targeted prompt fix if failed")


class SubtitleTrack(BaseModel):
    lang: str
    cues: list[dict] = Field(description="[{start, end, text}] per shot dialogue")


class EditDecisionList(BaseModel):
    ordered_shot_ids: list[str]
    subtitle_tracks: list[SubtitleTrack] = Field(default_factory=list)
    music_bed: str | None = None
    cover_shot_id: str | None = None


# ---- Reusable Asset Library -------------------------------------------------
# The persistent spine: build a cast + style + world once, reuse across every
# future generation so characters and look stay consistent and continuable.

class VoiceProfile(BaseModel):
    id: str = Field(description="stable slug, e.g. 'lin_ye_zh'")
    provider_voice: str = Field(description="Qwen-TTS voice name")
    lang: str = "zh"
    notes: str = ""


class CharacterAsset(BaseModel):
    id: str = Field(description="stable slug reused across runs, e.g. 'lin_ye'")
    name: str
    appearance: str = Field(description="dense visual descriptors reused in every prompt")
    portrait_path: str | None = Field(default=None, description="locked reference portrait; reused as i2v first_frame")
    voices: list[VoiceProfile] = Field(default_factory=list, description="per-language voices for dubbing")
    wardrobe: list[str] = Field(default_factory=list, description="continuity: signature clothing/props")
    version: int = 1
    origin_run: str = ""


class StyleDNA(BaseModel):
    id: str = "default"
    name: str = ""
    look: str = Field(description="grade / lighting / lens feel, baked into every prompt")
    palette: str = ""
    negative: str = ""


class WorldElement(BaseModel):
    id: str
    name: str
    description: str = Field(description="recurring location or prop to keep consistent")


class AssetLibrary(BaseModel):
    characters: list[CharacterAsset] = Field(default_factory=list)
    styles: list[StyleDNA] = Field(default_factory=list)
    world: list[WorldElement] = Field(default_factory=list)
