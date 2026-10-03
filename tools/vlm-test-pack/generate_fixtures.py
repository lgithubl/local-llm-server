#!/usr/bin/env python3
"""Generate small manga-like image fixtures for VLM smoke tests."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int) -> ImageFont.ImageFont:
    for name in (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def speech(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str) -> None:
    draw.rounded_rectangle(xy, radius=28, fill="white", outline="black", width=4)
    x0, y0, x1, y1 = xy
    draw.polygon([(x0 + 40, y1 - 4), (x0 + 10, y1 + 45), (x0 + 88, y1 - 4)], fill="white", outline="black")
    draw.text((x0 + 28, y0 + 28), text, fill="black", font=font(34), spacing=8)


def face(draw: ImageDraw.ImageDraw, cx: int, cy: int, mood: str, hair: str) -> None:
    draw.ellipse((cx - 84, cy - 100, cx + 84, cy + 92), fill="#f4c7a1", outline="black", width=4)
    draw.pieslice((cx - 100, cy - 120, cx + 100, cy + 35), 180, 360, fill=hair, outline="black", width=4)
    draw.ellipse((cx - 42, cy - 20, cx - 20, cy + 4), fill="black")
    draw.ellipse((cx + 20, cy - 20, cx + 42, cy + 4), fill="black")
    if mood == "happy":
        draw.arc((cx - 34, cy + 18, cx + 34, cy + 66), 0, 180, fill="black", width=4)
    elif mood == "angry":
        draw.line((cx - 55, cy - 42, cx - 16, cy - 28), fill="black", width=5)
        draw.line((cx + 16, cy - 28, cx + 55, cy - 42), fill="black", width=5)
        draw.line((cx - 30, cy + 52, cx + 30, cy + 52), fill="black", width=4)
    else:
        draw.ellipse((cx - 18, cy + 30, cx + 18, cy + 64), outline="black", width=4)


def make_single_reaction(path: Path) -> None:
    img = Image.new("RGB", (768, 1024), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((30, 30, 738, 994), outline="black", width=8)
    d.rectangle((40, 40, 728, 984), fill="#f7f7f2")
    face(d, 380, 560, "surprised", "#2f2f38")
    d.text((225, 800), "surprised close-up", fill="#222", font=font(42))
    speech(d, (78, 80, 430, 235), "What?!")
    img.save(path)


def make_bath_scene(path: Path) -> None:
    img = Image.new("RGB", (1024, 768), "#dce8ef")
    d = ImageDraw.Draw(img)
    d.rectangle((30, 30, 994, 738), outline="black", width=8)
    d.rectangle((40, 40, 984, 360), fill="#edf6f8")
    d.rectangle((100, 390, 924, 650), fill="#f2f2f2", outline="black", width=5)
    d.ellipse((115, 330, 909, 520), fill="#c5e9f3", outline="black", width=5)
    for x in (210, 360, 520, 690):
        d.arc((x, 150, x + 80, 300), 90, 250, fill="#9ca8ad", width=4)
    face(d, 520, 330, "happy", "#6b4b35")
    speech(d, (640, 80, 935, 235), "So warm")
    img.save(path)


def make_two_people_dialogue(path: Path) -> None:
    img = Image.new("RGB", (1024, 768), "#faf7ec")
    d = ImageDraw.Draw(img)
    d.rectangle((30, 30, 994, 738), outline="black", width=8)
    d.rectangle((40, 40, 984, 738), fill="#f8f0dd")
    d.rectangle((40, 510, 984, 738), fill="#c9d7b8")
    face(d, 325, 405, "happy", "#202637")
    face(d, 705, 405, "angry", "#9b403a")
    speech(d, (68, 70, 385, 220), "Let's go!")
    speech(d, (600, 80, 950, 245), "Wait for me!")
    img.save(path)


def make_multi_panel_page(path: Path) -> None:
    img = Image.new("RGB", (900, 1200), "white")
    d = ImageDraw.Draw(img)
    panels = [(30, 30, 870, 370), (30, 410, 430, 1160), (470, 410, 870, 1160)]
    for box in panels:
        d.rectangle(box, outline="black", width=8)
    d.rectangle((40, 40, 860, 360), fill="#cfddea")
    d.text((225, 150), "wide outdoor panel", fill="black", font=font(44))
    face(d, 230, 780, "surprised", "#4a3a2a")
    face(d, 670, 800, "happy", "#25304a")
    speech(d, (90, 470, 380, 620), "Look!")
    speech(d, (535, 480, 820, 630), "Nice!")
    img.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="images", help="Output image directory")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    make_single_reaction(out / "01_single_reaction.png")
    make_bath_scene(out / "02_bath_scene.png")
    make_two_people_dialogue(out / "03_two_people_dialogue.png")
    make_multi_panel_page(out / "04_multi_panel_page.png")
    print(f"Generated fixtures in {out}")


if __name__ == "__main__":
    main()
