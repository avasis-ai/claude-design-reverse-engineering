#!/usr/bin/env python3
"""
Animated explainer: observable assistant-output habits → structured framework.
Writes docs/media/framework-promo.gif, framework-promo.mp4, framework-promo-poster.png.

  python3 -m venv .venv && .venv/bin/pip install pillow
  .venv/bin/python scripts/render-framework-promo.py
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("pip install pillow", file=sys.stderr)
    raise SystemExit(1)

W, H = 720, 406  # even height for H.264 yuv420p
FRAMES = 42
FPS = 10

BG = (8, 8, 8)
CREAM = (237, 232, 223)
ACC = (127, 176, 105)
DIM = (95, 92, 88)
SURF = (22, 22, 24)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _font(n: int) -> ImageFont.ImageFont:
    for p in (
        "/System/Library/Fonts/Supplemental/SFMono-Regular.otf",
        "/Library/Fonts/Arial.ttf",
    ):
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, n)
            except OSError:
                pass
    return ImageFont.load_default()


def draw_frame(i: int, f: ImageFont.ImageFont, fs: ImageFont.ImageFont) -> Image.Image:
    u = (i % FRAMES) / FRAMES
    ph = u * math.pi * 2
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((24, 18), "Reverse engineering: assistant output → design system", fill=CREAM, font=fs)

    # Pipeline
    steps = ("Observe", "Abstract", "Ship tokens + checklists")
    for k, lab in enumerate(steps):
        x0 = 24 + k * 232
        pulse = 0.5 + 0.5 * math.sin(ph * 2 - k * 0.9)
        fill = tuple(int(lerp(a, b, pulse)) for a, b in zip(SURF, (32, 48, 38)))
        d.rounded_rectangle((x0, 46, x0 + 216, 74), radius=8, fill=fill)
        d.text((x0 + 14, 54), lab, fill=CREAM, font=fs)

    # Left: wall → chunks
    d.rounded_rectangle((24, 92, 330, 288), radius=12, outline=DIM)
    d.text((40, 104), "User-visible text", fill=DIM, font=fs)
    split = ease(max(0.0, (u - 0.15) / 0.5))
    if split < 0.95:
        for row in range(11):
            yy = 128 + row * 13
            jx = int(3 * math.sin(ph + row * 0.4))
            d.rectangle((40 + jx, yy, 310, yy + 7), fill=(20, 20, 22))
    else:
        for row, name in enumerate(["Hook", "Sections", "Lists", "Recap"]):
            yy = 128 + row * 36
            d.rounded_rectangle((42, yy, 312, yy + 28), radius=6, fill=(28, 30, 32))
            d.text((52, yy + 8), name, fill=CREAM, font=fs)

    # Center arrow / lens
    cx, cy = W // 2, 200
    r = int(28 + 6 * math.sin(ph * 3))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ACC, width=2)
    d.line([(cx - 52, cy), (cx - r - 4, cy)], fill=ACC, width=2)
    d.line([(cx + r + 4, cy), (cx + 52, cy)], fill=ACC, width=2)
    d.text((cx - 18, cy + 38), "infer", fill=DIM, font=fs)

    # Right: pyramid + table sketch
    d.rounded_rectangle((390, 92, W - 24, 288), radius=12, outline=DIM)
    d.text((406, 104), "Framework artifacts", fill=DIM, font=fs)
    # pyramid levels
    for lv in range(3):
        prog = ease(max(0.0, (u * 1.2 - lv * 0.12)))
        w = int(lerp(40, 260 - lv * 40, prog))
        x1 = (W - 24 + 390) // 2 - w // 2
        y1 = 132 + lv * 44
        d.rounded_rectangle((x1, y1, x1 + w, y1 + 28), radius=6, fill=(26, 32, 28))
        d.text((x1 + 12, y1 + 7), ["H1 thesis", "H2 pillars", "H3 evidence"][lv], fill=CREAM, font=fs)

    # Bottom table animates in
    ty = ease(max(0.0, (u - 0.55) / 0.45))
    if ty > 0.05:
        bx0, by0, bx1, by1 = 24, 302, W - 24, 388
        d.rounded_rectangle((bx0, by0, bx1, by1), radius=10, fill=(14, 14, 16))
        cols = ["Aspect", "Principle", "Do this"]
        cw = (bx1 - bx0) / 3
        for c, h in enumerate(cols):
            x = bx0 + c * cw + 8
            d.text((x, by0 + 10), h[: int(len(h) * ty) + 1], fill=ACC, font=fs)
        rowy = by0 + 36
        cells = [("Chunking", "One idea/block", "Use lists"), ("Disclosure", "Answer first", "Put detail last")]
        for ri, row in enumerate(cells):
            for ci, cell in enumerate(row):
                if ty > 0.35 + ri * 0.12:
                    d.text((bx0 + ci * cw + 10, rowy + ri * 22), cell, fill=CREAM, font=fs)

    return img


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "docs", "media")
    os.makedirs(out_dir, exist_ok=True)
    out_gif = os.path.join(out_dir, "framework-promo.gif")
    out_mp4 = os.path.join(out_dir, "framework-promo.mp4")
    out_poster = os.path.join(out_dir, "framework-promo-poster.png")

    f = _font(14)
    fs = _font(11)
    tmp = tempfile.mkdtemp(prefix="fw-promo-")
    try:
        for i in range(FRAMES):
            draw_frame(i, f, fs).save(os.path.join(tmp, f"f{i:03d}.png"), compress_level=3)
        pat = os.path.join(tmp, "f%03d.png")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(FPS),
                "-i",
                pat,
                "-filter_complex",
                "[0:v]scale=640:-1:flags=lanczos,split[s0][s1];"
                "[s0]palettegen=max_colors=128:stats_mode=diff[p];"
                "[s1][p]paletteuse=dither=bayer:bayer_scale=2",
                "-loop",
                "0",
                out_gif,
            ],
            check=True,
            cwd=tmp,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(FPS),
                "-i",
                pat,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "26",
                "-movflags",
                "+faststart",
                out_mp4,
            ],
            check=True,
            cwd=tmp,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                os.path.join(tmp, "f000.png"),
                "-frames:v",
                "1",
                out_poster,
            ],
            check=True,
        )
    finally:
        for n in os.listdir(tmp):
            os.unlink(os.path.join(tmp, n))
        os.rmdir(tmp)
    print(out_gif, out_mp4, sep="\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
