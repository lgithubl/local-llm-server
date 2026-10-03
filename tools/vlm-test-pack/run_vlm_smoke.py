#!/usr/bin/env python3
"""Run local-llm-server VLM suitability checks against manga-like images."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError


PROMPT = """You are analyzing one manga panel or manga page for conversion into an image-generation storyboard.

Return JSON only with exactly these keys:
{
  "scene": "short scene label",
  "visible_characters": ["generic visual descriptions, not copyrighted names"],
  "character_count": 0,
  "action": "what the characters are doing",
  "emotion": "dominant emotion or mood",
  "composition": "camera angle and framing",
  "environment": "place and important background objects",
  "lighting": "lighting description",
  "fx": "visual effects such as steam, speed lines, reflections, or none",
  "dialogue_hint": "visible text only; do not invent dialogue",
  "prompt_tags": ["anime image generation tags"],
  "negative_tags": ["only tags needed to avoid likely mistakes"],
  "confidence": 0.0
}

Rules:
- Do not identify copyrighted character names.
- Do not invent dialogue that is not visible in the image.
- If uncertain, use generic descriptions.
- Keep prompt_tags useful for anime/SDXL image generation.
- Output parseable JSON only, no markdown.
"""


def post_json(url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def get(url: str, timeout: int) -> tuple[int, str]:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as res:
        return res.status, res.read().decode("utf-8", errors="replace")


def content_text(response: dict) -> str:
    message = response["choices"][0]["message"]
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content)


def extract_json(text: str) -> tuple[dict | None, str | None]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped), None
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", stripped, re.S)
        if match:
            try:
                return json.loads(match.group(0)), None
            except json.JSONDecodeError:
                pass
        return None, str(exc)


def image_payload(path: Path) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def chat_payload(model: str, content: list | str, max_tokens: int, temperature: float) -> dict:
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def score_result(data: dict | None, elapsed: float) -> dict:
    required = {
        "scene",
        "visible_characters",
        "character_count",
        "action",
        "emotion",
        "composition",
        "environment",
        "lighting",
        "fx",
        "dialogue_hint",
        "prompt_tags",
        "negative_tags",
        "confidence",
    }
    if data is None:
        return {"json_ok": False, "schema_ok": False, "usable": False, "elapsed": elapsed}
    missing = sorted(required - set(data))
    tags_ok = isinstance(data.get("prompt_tags"), list) and len(data.get("prompt_tags")) > 0
    scene_ok = bool(str(data.get("scene", "")).strip())
    action_ok = bool(str(data.get("action", "")).strip())
    schema_ok = not missing and isinstance(data.get("visible_characters"), list)
    usable = schema_ok and tags_ok and scene_ok and action_ok
    return {
        "json_ok": True,
        "schema_ok": schema_ok,
        "missing": missing,
        "tags_ok": tags_ok,
        "scene_ok": scene_ok,
        "action_ok": action_ok,
        "usable": usable,
        "elapsed": elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8082", help="local-llm-server base URL")
    parser.add_argument("--model", default="qwen-vl", help="model name sent to llama-server")
    parser.add_argument("--images", default="images", help="directory of images to test")
    parser.add_argument("--out", default="results", help="output directory")
    parser.add_argument("--timeout", type=int, default=300, help="per-request timeout seconds")
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--temperature", type=float, default=0.1)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    images_dir = Path(args.images)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    report: list[str] = ["# VLM Smoke Report", ""]

    try:
        status, health = get(f"{base}/health", timeout=30)
        report.append(f"- Health: HTTP {status} `{health[:120].strip()}`")
    except (HTTPError, URLError, TimeoutError) as exc:
        report.append(f"- Health: FAILED `{exc}`")
        (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("Health check failed; see results/report.md")
        return 2

    try:
        text_start = time.monotonic()
        text_res = post_json(
            f"{base}/v1/chat/completions",
            chat_payload(args.model, 'Return exactly this JSON: {"ok": true}', 80, 0.0),
            timeout=args.timeout,
        )
        text_elapsed = time.monotonic() - text_start
        raw_dir.joinpath("00_text.json").write_text(json.dumps(text_res, ensure_ascii=False, indent=2), encoding="utf-8")
        report.append(f"- Text chat: ok in {text_elapsed:.1f}s")
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
        report.append(f"- Text chat: FAILED `{exc}`")

    image_paths = sorted(
        p for p in images_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if not image_paths:
        report.append(f"- Images: none found in `{images_dir}`")
        (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        return 2

    report.extend(["", "## Image Results", ""])
    usable_count = 0
    json_count = 0
    elapsed_values = []
    for path in image_paths:
        content = [{"type": "text", "text": PROMPT}, image_payload(path)]
        started = time.monotonic()
        try:
            response = post_json(
                f"{base}/v1/chat/completions",
                chat_payload(args.model, content, args.max_tokens, args.temperature),
                timeout=args.timeout,
            )
            elapsed = time.monotonic() - started
            elapsed_values.append(elapsed)
            raw_dir.joinpath(f"{path.stem}.response.json").write_text(
                json.dumps(response, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            text = content_text(response)
            raw_dir.joinpath(f"{path.stem}.txt").write_text(text, encoding="utf-8")
            parsed, error = extract_json(text)
            if parsed is not None:
                raw_dir.joinpath(f"{path.stem}.parsed.json").write_text(
                    json.dumps(parsed, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            score = score_result(parsed, elapsed)
            json_count += int(score["json_ok"])
            usable_count += int(score["usable"])
            report.append(
                f"- `{path.name}`: json={score['json_ok']} usable={score['usable']} "
                f"time={elapsed:.1f}s scene={str((parsed or {}).get('scene', ''))[:60]!r} "
                f"action={str((parsed or {}).get('action', ''))[:60]!r}"
            )
            if error:
                report.append(f"  Parse error: `{error}`")
        except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
            elapsed = time.monotonic() - started
            report.append(f"- `{path.name}`: FAILED after {elapsed:.1f}s `{exc}`")

    total = len(image_paths)
    avg_elapsed = sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0
    report.extend(
        [
            "",
            "## Summary",
            "",
            f"- JSON parseable: {json_count}/{total}",
            f"- Usable schema/content: {usable_count}/{total}",
            f"- Average image latency: {avg_elapsed:.1f}s",
            "",
            "Recommended gate for Manga Studio Smart Import:",
            "- JSON parseable >= 80%",
            "- Usable schema/content >= 70%",
            "- Average image latency <= 90s for interactive-ish use",
        ]
    )

    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print((out / "report.md").read_text(encoding="utf-8"))
    return 0 if json_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
