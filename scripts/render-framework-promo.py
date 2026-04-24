#!/usr/bin/env python3
"""
Animated explainer: ASCII title → subtitle → assistant output → framework.
Writes docs/media/framework-promo.gif, framework-promo.mp4, framework-promo-poster.png.

Layout is authored for 720×406; we render at 2× (1920×1080 for 960×540 output) so
labels stay crisp, then Lanczos-downscale. GIF uses ffmpeg palettegen/paletteuse
(Floyd–Steinberg); MP4 uses libx264 CRF 18. See:
  https://ffmpeg.org/ffmpeg-filters.html#palettegen-1
Optional: https://www.lcdf.org/gifsicle/ to re-optimize GIF size after export.

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

# Logical layout (matches legacy 720p explainer). Output is OUT_W×OUT_H.
ORIG_W, ORIG_H = 720, 406
OUT_W, OUT_H = 960, 540
SS = 2
CANVAS_W = OUT_W * SS
CANVAS_H = OUT_H * SS

# figlet -f small "CLAUDE DESIGN" (MIT-style community asset; bundled for reproducibility)
CLAUDE_DESIGN_ASCII = r"""
  ___ _      _  _   _ ___  ___   ___  ___ ___ ___ ___ _  _
 / __| |    /_\| | | |   \| __| |   \| __/ __|_ _/ __| \| |
| (__| |__ / _ \ |_| | |) | _|  | |) | _|\__ \| | (_ | .` |
 \___|____/_/ \_\___/|___/|___| |___/|___|___/___\___|_|\_|
""".strip("\n")

INTRO_ASCII_FRAMES = 16
INTRO_SUB_FRAMES = 10
MAIN_FRAMES = 48
TOTAL_FRAMES = INTRO_ASCII_FRAMES + INTRO_SUB_FRAMES + MAIN_FRAMES
FPS = 10

BG = (8, 8, 8)
CREAM = (237, 232, 223)
ACC = (127, 176, 105)
DIM = (95, 92, 88)
SURF = (22, 22, 24)


def sx(x: float | int) -> int:
    return int(float(x) * CANVAS_W / ORIG_W)


def sy(y: float | int) -> int:
    return int(float(y) * CANVAS_H / ORIG_H)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _font(n: int) -> ImageFont.ImageFont:
    for p in (
        "/System/Library/Fonts/Supplemental/SFMono-Regular.otf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, n)
            except OSError:
                pass
    return ImageFont.load_default()


def _text_size(d: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = d.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _label(
    d: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, ...],
    font: ImageFont.ImageFont,
    stroke: int = 2,
) -> None:
    d.text(
        xy,
        text,
        fill=fill,
        font=font,
        stroke_width=stroke,
        stroke_fill=BG,
    )


def draw_intro_ascii(d: ImageDraw.ImageDraw, frame: int) -> None:
    t = frame / max(1, INTRO_ASCII_FRAMES - 1)
    pulse = 0.75 + 0.25 * math.sin(t * math.pi * 2)
    mono = _font(sx(13))
    lines = [ln for ln in CLAUDE_DESIGN_ASCII.splitlines() if ln.strip()]
    tw = max(_text_size(d, ln, mono)[0] for ln in lines)
    block_h = len(lines) * sy(20)
    y0 = (CANVAS_H - block_h) // 2 - sy(24)
    x0 = (CANVAS_W - tw) // 2
    for row, line in enumerate(lines):
        y = y0 + row * sy(20)
        col = tuple(int(lerp(a, b, pulse)) for a, b in zip((40, 40, 42), ACC))
        _label(d, (x0, y), line, fill=col, font=mono, stroke=3)


def draw_intro_subtitle(d: ImageDraw.ImageDraw, frame: int) -> None:
    # frame 0..INTRO_SUB_FRAMES-1
    t = ease(frame / max(1, INTRO_SUB_FRAMES - 1))
    mono = _font(sx(11))
    lines = [ln for ln in CLAUDE_DESIGN_ASCII.splitlines() if ln.strip()]
    block_h = len(lines) * sy(20)
    y_ascii = (CANVAS_H - block_h) // 2 - sy(50)
    tw = max(_text_size(d, ln, mono)[0] for ln in lines)
    x0 = (CANVAS_W - tw) // 2
    dim_c = tuple(int(lerp(a, b, 0.45)) for a, b in zip(BG, CREAM))
    for row, line in enumerate(lines):
        d.text((x0, y_ascii + row * sy(20)), line, fill=dim_c, font=mono)

    title = _font(sx(26))
    sub = _font(sx(15))
    title_s = "Reverse engineered"
    sub_s = "Observable assistant output → tokens, checklists, document IA"
    tw1, th1 = _text_size(d, title_s, title)
    tw2, _ = _text_size(d, sub_s, sub)
    y1 = y_ascii + block_h + sy(18)
    _label(
        d,
        ((CANVAS_W - tw1) // 2, y1),
        title_s,
        fill=CREAM,
        font=title,
        stroke=3,
    )
    _label(
        d,
        ((CANVAS_W - tw2) // 2, y1 + th1 + sy(10)),
        sub_s[: max(0, int(len(sub_s) * t))],
        fill=ACC,
        font=sub,
        stroke=2,
    )


def draw_main(j: int, d: ImageDraw.ImageDraw, fs: ImageFont.ImageFont) -> None:
    u = (j % MAIN_FRAMES) / MAIN_FRAMES
    ph = u * math.pi * 2

    _label(
        d,
        (sx(24), sy(18)),
        "Assistant output → design system (patterns + IA)",
        fill=CREAM,
        font=fs,
        stroke=2,
    )

    steps = ("Observe", "Abstract", "Ship tokens + checklists")
    for k, lab in enumerate(steps):
        x0 = sx(24 + k * 232)
        pulse = 0.5 + 0.5 * math.sin(ph * 2 - k * 0.9)
        fill = tuple(int(lerp(a, b, pulse)) for a, b in zip(SURF, (32, 48, 38)))
        d.rounded_rectangle((x0, sy(46), x0 + sx(216), sy(74)), radius=sx(8), fill=fill)
        _label(d, (x0 + sx(14), sy(54)), lab, fill=CREAM, font=fs, stroke=2)

    d.rounded_rectangle((sx(24), sy(92), sx(330), sy(288)), radius=sx(12), outline=DIM)
    _label(d, (sx(40), sy(104)), "User-visible text", fill=DIM, font=fs, stroke=1)
    split = ease(max(0.0, (u - 0.15) / 0.5))
    if split < 0.95:
        for row in range(11):
            yy = sy(128 + row * 13)
            jx = int(sx(3) * math.sin(ph + row * 0.4))
            d.rectangle((sx(40) + jx, yy, sx(310), yy + sy(7)), fill=(20, 20, 22))
    else:
        for row, name in enumerate(["Hook", "Sections", "Lists", "Recap"]):
            yy = sy(128 + row * 36)
            d.rounded_rectangle((sx(42), yy, sx(312), yy + sy(28)), radius=sx(6), fill=(28, 30, 32))
            _label(d, (sx(52), yy + sy(8)), name, fill=CREAM, font=fs, stroke=2)

    cx, cy = CANVAS_W // 2, sy(200)
    r = int(sy(28) + sy(6) * math.sin(ph * 3))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ACC, width=max(2, SS))
    d.line([(cx - sx(52), cy), (cx - r - sx(4), cy)], fill=ACC, width=max(2, SS))
    d.line([(cx + r + sx(4), cy), (cx + sx(52), cy)], fill=ACC, width=max(2, SS))
    _label(d, (cx - sx(22), cy + sy(38)), "infer", fill=DIM, font=fs, stroke=1)

    d.rounded_rectangle((sx(390), sy(92), CANVAS_W - sx(24), sy(288)), radius=sx(12), outline=DIM)
    _label(d, (sx(406), sy(104)), "Framework artifacts", fill=DIM, font=fs, stroke=1)
    for lv in range(3):
        prog = ease(max(0.0, (u * 1.2 - lv * 0.12)))
        w = int(lerp(sx(40), sx(260 - lv * 40), prog))
        x1 = (CANVAS_W - sx(24) + sx(390)) // 2 - w // 2
        y1 = sy(132 + lv * 44)
        d.rounded_rectangle((x1, y1, x1 + w, y1 + sy(28)), radius=sx(6), fill=(26, 32, 28))
        _label(
            d,
            (x1 + sx(12), y1 + sy(7)),
            ["H1 thesis", "H2 pillars", "H3 evidence"][lv],
            fill=CREAM,
            font=fs,
            stroke=2,
        )

    ty = ease(max(0.0, (u - 0.55) / 0.45))
    if ty > 0.05:
        bx0, by0, bx1, by1 = sx(24), sy(302), CANVAS_W - sx(24), sy(388)
        d.rounded_rectangle((bx0, by0, bx1, by1), radius=sx(10), fill=(14, 14, 16))
        cols = ["Aspect", "Principle", "Do this"]
        cw = (bx1 - bx0) / 3
        for c, h in enumerate(cols):
            x = bx0 + c * cw + sx(8)
            _label(
                d,
                (x, by0 + sy(10)),
                h[: int(len(h) * ty) + 1],
                fill=ACC,
                font=fs,
                stroke=2,
            )
        rowy = by0 + sy(36)
        cells = [
            ("Chunking", "One idea/block", "Use lists"),
            ("Disclosure", "Answer first", "Put detail last"),
        ]
        for ri, row in enumerate(cells):
            for ci, cell in enumerate(row):
                if ty > 0.35 + ri * 0.12:
                    _label(
                        d,
                        (bx0 + ci * cw + sx(10), rowy + ri * sy(22)),
                        cell,
                        fill=CREAM,
                        font=fs,
                        stroke=1,
                    )


def draw_frame(i: int, fs: ImageFont.ImageFont) -> Image.Image:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    d = ImageDraw.Draw(img)
    if i < INTRO_ASCII_FRAMES:
        draw_intro_ascii(d, i)
    elif i < INTRO_ASCII_FRAMES + INTRO_SUB_FRAMES:
        draw_intro_subtitle(d, i - INTRO_ASCII_FRAMES)
    else:
        draw_main(i - INTRO_ASCII_FRAMES - INTRO_SUB_FRAMES, d, fs)
    return img


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "docs", "media")
    os.makedirs(out_dir, exist_ok=True)
    out_gif = os.path.join(out_dir, "framework-promo.gif")
    out_mp4 = os.path.join(out_dir, "framework-promo.mp4")
    out_poster = os.path.join(out_dir, "framework-promo-poster.png")

    fs = _font(sx(11))
    tmp = tempfile.mkdtemp(prefix="fw-promo-")
    gif_fc = (
        "[0:v]split[s0][s1];"
        "[s0]palettegen=max_colors=256:reserve_transparent=0:stats_mode=full[p];"
        "[s1][p]paletteuse=dither=floyd_steinberg:diff_mode=rectangle:new=1"
    )
    try:
        for i in range(TOTAL_FRAMES):
            im = draw_frame(i, fs)
            im = im.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
            im.save(os.path.join(tmp, f"f{i:03d}.png"), compress_level=3)
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
                gif_fc,
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
                "18",
                "-preset",
                "slow",
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
