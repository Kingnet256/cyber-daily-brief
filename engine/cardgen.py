"""Generate a branded 1200x675 headline card for each story."""
from __future__ import annotations

import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

from engine import config

W, H = 1200, 675
ASSET_SHIELD = os.path.join(os.path.dirname(__file__), "..", "assets", "shield.png")

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
]
FONT_REG = [p.replace("-Bold", "") for p in FONT_CANDIDATES]


def _font(size, bold=True):
    for path in (FONT_CANDIDATES if bold else FONT_REG):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _gradient(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / max(1, h - 1)
        draw.line([(0, y), (w, y)],
                  fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return base


def make_card(title: str, source: str, date_str: str, out_path: str):
    b = config.BRAND
    img = _gradient(W, H, b["teal"], b["teal_dark"])
    d = ImageDraw.Draw(img)

    # Header: shield badge + brand name
    x = 60
    try:
        shield = Image.open(ASSET_SHIELD).convert("RGBA").resize((88, 88))
        img.paste(shield, (x, 54), shield)
        x += 108
    except Exception:
        pass
    d.text((x, 74), b["name"].upper(), font=_font(30), fill=(255, 255, 255))

    # Orange accent rule under header
    d.rectangle([60, 168, 300, 174], fill=b["orange"])

    # Headline, wrapped and vertically balanced
    fsize = 62 if len(title) < 90 else 52 if len(title) < 140 else 44
    font = _font(fsize)
    avg_char = font.getlength("n") or (fsize * 0.5)
    wrap_at = max(18, int((W - 120) / avg_char))
    lines = textwrap.wrap(title, width=wrap_at)[:6]
    line_h = fsize + 14
    y = 210
    for line in lines:
        d.text((60, y), line, font=font, fill=(255, 255, 255))
        y += line_h

    # Footer: source + date
    foot = _font(28, bold=False)
    footer = f"{source}  •  {date_str}"
    d.text((60, H - 70), footer, font=foot, fill=b["orange"])
    d.text((W - 60 - d.textlength(b["site"], font=foot), H - 70),
           b["site"], font=foot, fill=(210, 230, 231))

    img.save(out_path, "PNG")
    return out_path
