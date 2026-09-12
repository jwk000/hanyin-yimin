#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用钢铁、冰、水、血和骨材质合成精确的《寒垠遗民》书名。"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


HERE = Path(__file__).resolve().parent
MATERIALS = HERE / "题字素材"
OUTPUT = HERE / "题字-寒垠遗民.png"
CANVAS = (1300, 380)
SCALE = 4
GLYPH_SIZE = 270
GLYPH_TOP = 50
GLYPH_START = 38
GLYPH_GAP = 36

# 自定义题字骨架。坐标位于单个 100×100 字面内，粗笔画和断口都手工设计。
GLYPHS = {
    "寒": [
        (((10, 16), (90, 16)), 12),
        (((21, 16), (21, 31)), 10),
        (((79, 16), (79, 31)), 10),
        (((50, 27), (50, 72)), 13),
        (((19, 39), (81, 39)), 11),
        (((18, 57), (82, 57)), 11),
        (((37, 46), (31, 68)), 9),
        (((63, 46), (69, 68)), 9),
        (((16, 79), (10, 91)), 10),
        (((30, 78), (24, 92)), 9),
        (((70, 78), (76, 92)), 9),
        (((84, 79), (90, 91)), 10),
    ],
    "垠": [
        (((9, 22), (46, 22)), 10),
        (((28, 15), (28, 86)), 12),
        (((9, 58), (46, 58)), 10),
        (((49, 17), (89, 17)), 11),
        (((49, 17), (49, 49)), 11),
        (((89, 17), (89, 47)), 9),
        (((56, 33), (83, 33)), 8),
        (((82, 39), (84, 74)), 9),
        (((53, 84), (85, 58)), 12),
        (((51, 84), (92, 84)), 11),
        (((55, 65), (76, 65)), 8),
    ],
    "遗": [
        (((49, 7), (49, 22)), 8),
        (((33, 20), (67, 20)), 9),
        (((38, 26), (63, 26)), 9),
        (((38, 26), (38, 48)), 8),
        (((63, 26), (63, 48)), 8),
        (((40, 43), (61, 43)), 8),
        (((42, 52), (61, 52)), 9),
        (((42, 52), (42, 78)), 8),
        (((61, 52), (61, 78)), 8),
        (((43, 67), (60, 67)), 7),
        (((18, 58), (25, 72)), 9),
        (((24, 76), (77, 72), (96, 89)), 10),
        (((17, 91), (79, 91)), 10),
    ],
    "民": [
        (((12, 18), (89, 18)), 12),
        (((14, 18), (14, 54)), 12),
        (((84, 18), (84, 52)), 11),
        (((50, 18), (50, 44)), 9),
        (((13, 48), (88, 48)), 12),
        (((61, 50), (24, 84)), 14),
        (((62, 48), (62, 81)), 12),
        (((57, 82), (93, 82)), 12),
        (((40, 71), (58, 71)), 8),
    ],
}

CUTS = {
    "寒": [(((34, 35), (29, 48)), 4), (((67, 57), (74, 66)), 3)],
    "垠": [(((23, 42), (34, 47)), 4), (((74, 72), (81, 64)), 3)],
    "遗": [(((31, 73), (39, 82)), 4), (((61, 34), (57, 44)), 3)],
    "民": [(((28, 55), (39, 66)), 4), (((73, 29), (80, 38)), 3)],
}


def load_material(name):
    image = Image.open(MATERIALS / name).convert("RGB")
    if name == "血.png":
        gray = ImageOps.grayscale(image)
        image = ImageOps.colorize(gray, black=(26, 4, 3), white=(132, 31, 22))
    elif name == "骨.png":
        gray = ImageOps.grayscale(image)
        image = ImageOps.colorize(gray, black=(39, 35, 28), white=(224, 215, 187))
    image = ImageEnhance.Color(image).enhance(0.78)
    image = ImageEnhance.Brightness(image).enhance(0.84)
    return ImageEnhance.Contrast(image).enhance(1.12)


def transform_points(points, left, top):
    return [
        (
            int(round(left + x / 100.0 * GLYPH_SIZE)),
            int(round(top + y / 100.0 * GLYPH_SIZE)),
        )
        for x, y in points
    ]


def draw_glyph(draw, char, left, width=None):
    for points, stroke_width in GLYPHS[char]:
        mapped = transform_points(points, left, GLYPH_TOP)
        mapped = [(x * SCALE, y * SCALE) for x, y in mapped]
        draw.line(
            mapped,
            fill=255,
            width=int(round((width or stroke_width) / 100.0 * GLYPH_SIZE * SCALE)),
            joint="curve",
        )
        radius = int(round((width or stroke_width) / 200.0 * GLYPH_SIZE * SCALE))
        for x, y in mapped:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)


def draw_cuts(draw, char, left):
    for points, width in CUTS[char]:
        mapped = transform_points(points, left, GLYPH_TOP)
        mapped = [(x * SCALE, y * SCALE) for x, y in mapped]
        draw.line(
            mapped,
            fill=0,
            width=int(round(width / 100.0 * GLYPH_SIZE * SCALE)),
            joint="curve",
        )


def region_mask(size, kind, strength):
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if kind == "left":
        draw.rectangle((0, 0, int(width * 0.42), height), fill=255)
    elif kind == "bottom":
        draw.rectangle((0, int(height * 0.56), width, height), fill=255)
    elif kind == "top_right":
        draw.polygon(
            ((int(width * 0.42), 0), (width, 0), (width, height), (int(width * 0.68), height)),
            fill=255,
        )
    elif kind == "diagonal":
        draw.polygon(
            ((int(width * 0.30), 0), (int(width * 0.54), 0),
             (int(width * 0.72), height), (int(width * 0.48), height)),
            fill=255,
        )
    elif kind == "top":
        draw.rectangle((0, 0, width, int(height * 0.36)), fill=255)
    else:
        draw.ellipse((-width * 0.1, -height * 0.1, width * 0.74, height * 0.74), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(width, height) * 0.025))
    return mask.point(lambda value: int(value * strength))


def material_swatch(spec, size, center_focus):
    base = ImageOps.fit(
        load_material(spec["base"]),
        size,
        method=Image.Resampling.LANCZOS,
        centering=center_focus,
    )
    for index, (name, kind, strength) in enumerate(spec["regions"], start=1):
        overlay = ImageOps.fit(
            load_material(name),
            size,
            method=Image.Resampling.LANCZOS,
            centering=(
                (center_focus[0] + index * 0.21) % 1.0,
                (center_focus[1] + index * 0.17) % 1.0,
            ),
        )
        base = Image.composite(overlay, base, region_mask(size, kind, strength))
    return base


def main():
    high_size = (CANVAS[0] * SCALE, CANVAS[1] * SCALE)
    high_mask = Image.new("L", high_size, 0)
    high_stroke = Image.new("L", high_size, 0)
    glyph_draw = ImageDraw.Draw(high_mask)
    stroke_draw = ImageDraw.Draw(high_stroke)
    glyph_boxes = []
    for index, char in enumerate(GLYPHS):
        left = GLYPH_START + index * (GLYPH_SIZE + GLYPH_GAP)
        draw_glyph(glyph_draw, char, left)
        draw_glyph(stroke_draw, char, left, width=18)
        draw_cuts(glyph_draw, char, left)
        glyph_boxes.append((left, GLYPH_TOP, left + GLYPH_SIZE, GLYPH_TOP + GLYPH_SIZE))

    title_mask = high_mask.resize(CANVAS, Image.Resampling.LANCZOS)
    stroke_mask = high_stroke.resize(CANVAS, Image.Resampling.LANCZOS)

    recipes = [
        {
            "base": "冰.png",
            "regions": [("钢铁.png", "left", 0.52), ("水.png", "bottom", 0.42)],
        },
        {
            "base": "钢铁.png",
            "regions": [("骨.png", "top_right", 0.58), ("冰.png", "left", 0.32)],
        },
        {
            "base": "水.png",
            "regions": [("血.png", "bottom", 0.70), ("冰.png", "top_right", 0.40)],
        },
        {
            "base": "骨.png",
            "regions": [("血.png", "left", 0.70), ("钢铁.png", "diagonal", 0.48)],
        },
    ]

    texture = Image.new("RGB", CANVAS, (8, 10, 11))
    bbox_draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    for index, recipe in enumerate(recipes):
        bbox = glyph_boxes[index]
        char_size = (
            max(1, int(round(bbox[2] - bbox[0]))),
            max(1, int(round(bbox[3] - bbox[1]))),
        )
        focus = ((0.32 + index * 0.14) % 0.8, (0.28 + index * 0.17) % 0.8)
        swatch = material_swatch(recipe, char_size, focus)
        char_mask = title_mask.crop(bbox)
        texture.paste(swatch, (bbox[0], bbox[1]), char_mask)

    # 局部干血和霜晶，避免只在整字上机械贴材质。
    noise = Image.effect_noise(CANVAS, 68).filter(ImageFilter.GaussianBlur(2))
    blood_mask = noise.point(lambda value: 255 if value > 188 else 0)
    blood_mask = ImageChops.multiply(blood_mask, title_mask).filter(
        ImageFilter.GaussianBlur(0.7))
    blood_layer = Image.new("RGB", CANVAS, (108, 24, 18))
    texture = Image.composite(blood_layer, texture, blood_mask)

    blood_patch_mask = Image.new("L", CANVAS, 0)
    patch_draw = ImageDraw.Draw(blood_patch_mask)
    left, top, right, bottom = glyph_boxes[2]
    patch_draw.ellipse(
        (left - 5, top + (bottom - top) * 0.48, right + 5, bottom + 8),
        fill=225,
    )
    left, top, right, bottom = glyph_boxes[3]
    patch_draw.polygon(
        (
            (left - 4, top + (bottom - top) * 0.20),
            (left + (right - left) * 0.52, top + (bottom - top) * 0.03),
            (left + (right - left) * 0.60, bottom + 6),
            (left - 4, bottom + 6),
        ),
        fill=205,
    )
    blood_patch_mask = ImageChops.multiply(blood_patch_mask, title_mask).filter(
        ImageFilter.GaussianBlur(2.1))
    texture = Image.composite(Image.new("RGB", CANVAS, (102, 22, 17)),
                              texture, blood_patch_mask)

    edge = title_mask.filter(ImageFilter.FIND_EDGES).filter(
        ImageFilter.GaussianBlur(1.1)).point(lambda value: min(255, value * 2))
    frost = Image.new("RGB", CANVAS, (190, 218, 222))
    texture = Image.composite(frost, texture, edge.point(lambda value: value * 2 // 3))

    result = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    shadow_mask = stroke_mask.filter(ImageFilter.GaussianBlur(13))
    shadow_mask = ImageChops.offset(shadow_mask, 0, 7)
    shadow = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    shadow.putalpha(shadow_mask.point(lambda value: int(value * 0.78)))
    result = Image.alpha_composite(result, shadow)

    rim_mask = ImageChops.subtract(stroke_mask, title_mask).filter(
        ImageFilter.GaussianBlur(0.8))
    rim = Image.new("RGBA", CANVAS, (14, 19, 21, 0))
    rim.putalpha(rim_mask)
    result = Image.alpha_composite(result, rim)

    title = texture.convert("RGBA")
    title.putalpha(title_mask)
    result = Image.alpha_composite(result, title)
    result.save(OUTPUT, "PNG", optimize=True)
    print("题字 -> %s" % OUTPUT)


if __name__ == "__main__":
    main()
