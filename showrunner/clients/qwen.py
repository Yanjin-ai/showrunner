"""Qwen text + vision-language via the OpenAI-compatible endpoint."""
import json
import re
from openai import OpenAI
from showrunner import config, cost

_client = OpenAI(api_key=config.API_KEY, base_url=config.QWEN_BASE_URL)


def _meter(resp, vl: bool = False):
    u = getattr(resp, "usage", None)
    if u and getattr(u, "total_tokens", None):
        cost.current.text(u.total_tokens, vl=vl)


def chat(prompt: str, *, system: str = "", model: str | None = None,
         temperature: float = 0.7, response_format: dict | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kw = {"response_format": response_format} if response_format else {}
    resp = _client.chat.completions.create(
        model=model or config.PLANNER_MODEL, messages=messages, temperature=temperature, **kw)
    _meter(resp)
    return resp.choices[0].message.content or ""


def chat_json(prompt: str, *, system: str = "", model: str | None = None) -> dict:
    """Ask for JSON and parse robustly. Uses the API's json_object mode first (forces valid
    JSON), then falls back to plain + repair. Never lets one flaky generation kill a run."""
    system = (system + "\nRespond with ONLY a single valid JSON object, no prose, no markdown fences.").strip()
    try:
        raw = chat(prompt, system=system, model=model, temperature=0.5,
                   response_format={"type": "json_object"})
        return _extract_json(raw)
    except Exception:
        pass  # json_object unsupported for this model, or a rare parse miss — retry plainly
    raw = chat(prompt, system=system, model=model, temperature=0.2)
    return _extract_json(raw)


def vision_caption(image_url_or_datauri: str, question: str) -> str:
    """Qwen-VL: caption/score a frame. Accepts an http(s) URL or a data: URI."""
    resp = _client.chat.completions.create(
        model=config.VL_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": image_url_or_datauri}},
        ]}],
        temperature=0.2,
    )
    _meter(resp, vl=True)
    return resp.choices[0].message.content or ""


def vision_json(image_url_or_datauri: str, question: str) -> dict:
    """Qwen-VL returning a parsed JSON object (used by the critic)."""
    question += "\nRespond with ONLY a single valid JSON object, no prose, no fences."
    return _extract_json(vision_caption(image_url_or_datauri, question))


def vision_json_multi(image_urls: list[str], question: str) -> dict:
    """Qwen-VL over several frames at once — lets the critic judge motion/action."""
    question += "\nRespond with ONLY a single valid JSON object, no prose, no fences."
    content = [{"type": "text", "text": question}]
    for u in image_urls:
        content.append({"type": "image_url", "image_url": {"url": u}})
    resp = _client.chat.completions.create(
        model=config.VL_MODEL, messages=[{"role": "user", "content": content}], temperature=0.2)
    _meter(resp, vl=True)
    return _extract_json(resp.choices[0].message.content or "")


def frame_to_datauri(png_path) -> str:
    import base64
    from pathlib import Path
    b = Path(png_path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(b).decode()


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].removeprefix("json").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    for candidate in (raw, _repair(raw)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Could not parse JSON from model output: {raw[:300]}")


def _repair(s: str) -> str:
    """Fix the JSON errors LLMs actually make: // comments and trailing commas."""
    s = re.sub(r'//[^\n]*', '', s)
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return s
