#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成供 EPUB/PDF 使用的轻量 JPEG 插画副本，不修改生成稿。"""

from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "插画"
OUTPUT = SOURCE 
COVER_SOURCE = ROOT / "封面" / "封面-寒垠遗民-插画版.png"
COVER_OUTPUT = ROOT / "封面" / "封面-寒垠遗民-插画版.jpg"


def optimize(source, target, max_size, quality):
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")
    image = ImageOps.contain(image, max_size, method=Image.Resampling.LANCZOS)
    image.save(
        target,
        "JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling=0,
    )


def main():
    optimize(COVER_SOURCE, COVER_OUTPUT, (1600, 2400), 90)
    for source in sorted((SOURCE / "卷首").glob("*.png")):
        optimize(source, OUTPUT / "卷首" / (source.stem + ".jpg"), (1600, 1200), 86)
    for source in sorted((SOURCE / "章首").glob("*.png")):
        optimize(source, OUTPUT / "章首" / (source.stem + ".jpg"), (1600, 1200), 86)
    print("电子书版插画 -> %s" % OUTPUT)
    print("电子书版封面 -> %s" % COVER_OUTPUT)


if __name__ == "__main__":
    main()
