#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 AI 封面底图排版成正式封面，保留旧胶片与磨损质感。"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "插画" / "参考" / "封面-B-底图.png"
OUTPUT = Path(__file__).resolve().parent / "封面-寒垠遗民-插画版.png"
ORIGINAL_TITLE_ART = Path(__file__).resolve().parent / "题字-寒垠遗民-原创.png"
TITLE_ART = ORIGINAL_TITLE_ART if ORIGINAL_TITLE_ART.exists() else (
    Path(__file__).resolve().parent / "题字-寒垠遗民.png")
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Songti.ttc")
FONT_LIGHT_INDEX = 3


def font(size):
    return ImageFont.truetype(str(FONT_PATH), size=size, index=FONT_LIGHT_INDEX)


def draw_spaced(draw, center_x, y, text, text_font, fill, spacing):
    widths = [draw.textlength(char, font=text_font) for char in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = center_x - total / 2
    for char, width in zip(text, widths):
        draw.text((x, y), char, font=text_font, fill=fill)
        x += width + spacing


def add_surface_wear(image):
    width, height = image.size
    random.seed(8813)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for _ in range(95):
        x = random.randrange(width)
        y = random.randrange(height)
        length = random.randrange(12, 150)
        alpha = random.randrange(5, 20)
        draw.line((x, y, x + random.randrange(-4, 5), y + length),
                  fill=(220, 225, 228, alpha), width=1)

    for _ in range(220):
        x = random.randrange(width)
        y = random.randrange(height)
        radius = random.randrange(1, 4)
        alpha = random.randrange(3, 13)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     fill=(20, 24, 27, alpha))

    vignette = Image.new("L", image.size, 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse((-width * 0.2, -height * 0.1, width * 1.2, height * 1.1), fill=90)
    vignette = vignette.filter(ImageFilter.GaussianBlur(width // 8))
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade.putalpha(ImageOps.invert(vignette).point(lambda value: value * 0.42))
    image = Image.alpha_composite(image, overlay)
    return Image.alpha_composite(image, shade)


def main():
    if not SOURCE.exists():
        raise SystemExit(f"找不到封面底图：{SOURCE}")
    if not FONT_PATH.exists():
        raise SystemExit(f"找不到中文字体：{FONT_PATH}")

    image = Image.open(SOURCE).convert("RGB")
    image = ImageOps.fit(image, (1600, 2400), method=Image.Resampling.LANCZOS)
    image = ImageEnhance.Color(image).enhance(0.78)
    image = ImageEnhance.Brightness(image).enhance(0.89)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.convert("RGBA")
    image = add_surface_wear(image)

    draw = ImageDraw.Draw(image)
    pale = (232, 235, 234, 226)
    muted = (205, 213, 217, 148)
    faint = (188, 201, 211, 96)
    shadow = (0, 0, 0, 92)

    draw_spaced(draw, 800, 126, "未来 · 星际难民 · 生态科幻 · 回忆",
                font(24), muted, 11)
    if TITLE_ART.exists():
        title = Image.open(TITLE_ART).convert("RGBA")
        x = (1600 - title.width) // 2
        y = 275
        shadow_mask = title.getchannel("A").filter(ImageFilter.GaussianBlur(8))
        shadow = Image.new("RGBA", title.size, (0, 0, 0, 0))
        shadow.putalpha(shadow_mask.point(lambda value: int(value * 0.58)))
        image.alpha_composite(shadow, (x + 3, y + 8))
        image.alpha_composite(title, (x, y))
    else:
        draw_spaced(draw, 802, 354 + 3, "寒垠遗民", font(178), shadow, 36)
        draw_spaced(draw, 800, 354, "寒垠遗民", font(178), pale, 36)
    draw_spaced(draw, 800, 738, "jwk000", font(42), muted, 12)

    song = [
        "蓝的，咸的，一直响的，",
        "一直响的，回头又回过头，",
        "我在岸上等你，你在岸上等我，",
        "我们谁也没到过岸上。",
    ]
    for index, line in enumerate(song):
        draw_spaced(draw, 800, 1022 + index * 66, line, font(26), faint, 4)

    draw_spaced(draw, 800, 2248, "灰星　KN-8813-e", font(21), faint, 11)
    image.convert("RGB").save(OUTPUT, "PNG", optimize=True)
    print(f"封面 -> {OUTPUT}")


if __name__ == "__main__":
    main()
