"""Persistent, reusable asset library — the product's spine.

Characters (with locked portraits + per-language voices), style DNA, and world elements are
stored at PROJECT level (`library/`), NOT per-run, so a cast/style built once is reused across
every future generation. This is what makes output consistent AND continuable: next week's
shots draw the same face, wardrobe, and voice by id."""
import json
import shutil
from pathlib import Path

from showrunner.schemas import CharacterAsset, StyleDNA, WorldElement, AssetLibrary

ROOT = Path("library")


def _dir(kind: str) -> Path:
    d = ROOT / kind
    d.mkdir(parents=True, exist_ok=True)
    return d


def _jsons(d: Path) -> list[Path]:
    # skip macOS AppleDouble junk (._*) that appears on exFAT drives
    return [p for p in sorted(d.glob("*.json")) if not p.name.startswith("._")]


# ---- characters ----
def save_character(c: CharacterAsset, portrait_src=None) -> CharacterAsset:
    """Persist a character. If a portrait file is given, copy it into the library and lock it."""
    if portrait_src:
        dest = _dir("characters") / f"{c.id}.png"
        shutil.copy(portrait_src, dest)
        c.portrait_path = str(dest)
    (_dir("characters") / f"{c.id}.json").write_text(
        json.dumps(c.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return c


def get_character(cid: str) -> CharacterAsset | None:
    p = _dir("characters") / f"{cid}.json"
    return CharacterAsset.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def list_characters() -> list[CharacterAsset]:
    return [CharacterAsset.model_validate_json(p.read_text(encoding="utf-8"))
            for p in _jsons(_dir("characters"))]


# ---- style ----
def save_style(s: StyleDNA) -> StyleDNA:
    (_dir("styles") / f"{s.id}.json").write_text(
        json.dumps(s.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return s


def get_style(sid: str) -> StyleDNA | None:
    p = _dir("styles") / f"{sid}.json"
    return StyleDNA.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


# ---- world ----
def save_world(w: WorldElement) -> WorldElement:
    (_dir("world") / f"{w.id}.json").write_text(
        json.dumps(w.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return w


def load() -> AssetLibrary:
    return AssetLibrary(
        characters=list_characters(),
        styles=[StyleDNA.model_validate_json(p.read_text(encoding="utf-8"))
                for p in _jsons(_dir("styles"))],
        world=[WorldElement.model_validate_json(p.read_text(encoding="utf-8"))
               for p in _jsons(_dir("world"))],
    )
