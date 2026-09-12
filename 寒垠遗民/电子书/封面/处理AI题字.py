#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去除 AI 定制题字的浅色底，输出可叠加到封面的透明 PNG。"""

from pathlib import Path

from PIL import Image, ImageFilter


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "题字-AI方案A.png"
OUTPUT = HERE / "题字-寒垠遗民-原创.png"


def main():
    image = Image.open(SOURCE).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    foreground = Image.new("L", image.size, 255)
    foreground_pixels = foreground.load()
    for y in range(height):
        for x in range(width):
            red, green, blue, _ = pixels[x, y]
            low = min(red, green, blue)
            high = max(red, green, blue)
            # 生成稿把透明底画成了约 #EDEDED / #FBFBFB 的灰白棋盘格。
            if 210 <= low and high - low <= 24:
                foreground_pixels[x, y] = 0

    # 缩掉一像素浅色毛边，棋盘格即使穿过字腔也会被清掉。
    alpha = foreground.filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.25))
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit("题字去底后为空")
    image.putalpha(alpha)
    title = image.crop(bbox)

    target_height = 360
    target_width = max(1, round(title.width * target_height / title.height))
    title = title.resize((target_width, target_height), Image.Resampling.LANCZOS)
    clean = Image.new("RGBA", title.size, (0, 0, 0, 0))
    clean.alpha_composite(title)
    clean.save(OUTPUT, "PNG", optimize=True)
    print("原创题字 -> %s (%dx%d)" % (OUTPUT, clean.width, clean.height))


if __name__ == "__main__":
    main()
