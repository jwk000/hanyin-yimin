#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the cover and all chapter illustrations for the e-book."""

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
PROMPTS = PROJECT / "插画提示词.md"
ILLUSTRATIONS = ROOT / "插画"
CHAPTER_DIR = ILLUSTRATIONS / "章首"
VOLUME_DIR = ILLUSTRATIONS / "卷首"
REFERENCE_DIR = ILLUSTRATIONS / "参考"
COVER_DIR = ROOT / "封面"

COMMON = """电影感写实插画，冷峻压抑的科幻废土，不是概念海报，而是像在恶劣环境中拍到的旧胶片现场。极强年代感、损耗感和生存感。低照度、欠曝，重胶片颗粒，35mm 定焦，浅景深，构图留白。所有材料都有真实脏污：灰尘、泥、煤灰、油渍、盐霜、水痕、划痕、氧化、锈蚀、补丁、磨损和褪色。空气中有浮尘或水汽，光很弱。所有人物都必须是中国人，采用东亚人面部特征：黑发、深褐瞳、黄褐肤色和东亚骨相，不能出现欧美或混血面孔。人物不英雄化，不看镜头，不摆姿势；要显出长期寒冷、饥饿和劳作造成的瘦削、冻伤、干裂、佝偻与麻木。没有文字，没有水印，没有 logo。"""

GRAY_STYLE = """色彩只有灰、褐、锈红和脏白，唯一的暖色是火，唯一的亮色是血。天空是铅灰到铁锈色，没有蓝天白云，日照微弱。人物穿厚重分层的旧衣物，护目镜、面罩、绑腿、毛毡，颜色脏而旧。整个画面要冷、旧、脏，不精致、不干净。"""

EARTH_STYLE = """安静辽阔的自然光，湿润空气感，低到中饱和，颜色是湿绿、苔绿、海蓝、雾白，阳光是暖白而非金色。被植物覆盖的废墟，藤蔓，两米厚的新土层，没有人造垃圾。人物穿拆改过、洗得发浅且带补丁的旧衣服；长期劳作，朴素疲惫，但不英雄化。整个画面仍有真实年代感、损耗感和旧胶片质感。"""

NEGATIVE = """负面提示词：西方面孔, 欧美脸, 白人, 混血脸, 非东亚人, 干净, 崭新, 精致, 商业广告, 游戏原画, 概念海报, 英雄化, 看镜头, 微笑, 偶像感, 文字, 水印, 署名, logo, 边框, 卡通, 动漫, 赛博朋克霓虹, 蒸汽朋克, 华丽奇幻, 高饱和, 粉紫色调, 塑料感, 过度磨皮, 现代都市, 智能手机, 现代服饰。"""


def read_text(path):
    return path.read_text(encoding="utf-8")


def code_block_after(text, start, end=None):
    scope = text[start:end] if end is not None else text[start:]
    match = re.search(r"```(?:text)?\s*\n(.*?)\n```", scope, re.S)
    if not match:
        raise ValueError("没有找到提示词代码块")
    return " ".join(line.strip() for line in match.group(1).splitlines() if line.strip())


def parse_prompts():
    text = read_text(PROMPTS)
    prompts = {}

    cover_heading = re.search(r"^### 封面 B[^\n]*\n", text, re.M)
    if not cover_heading:
        raise ValueError("没有找到封面 B")
    cover_scope = text[cover_heading.end():]
    cover_next = re.search(r"^> 说明：", cover_scope, re.M)
    prompts["cover"] = code_block_after(
        cover_scope, 0, cover_next.start() if cover_next else None)

    volume_start = text.index("## 五、卷首插画")
    chapter_start = text.index("## 六、卷一至卷三")
    volume_text = text[volume_start:chapter_start]
    volume_re = re.compile(
        r"^### (卷[一二三四五]) · ([^\n]+)\n.*?```\s*\n(.*?)\n```",
        re.M | re.S,
    )
    for number, title, prompt in volume_re.findall(volume_text):
        prompts[f"volume-{number}"] = " ".join(
            line.strip() for line in prompt.splitlines() if line.strip())
        prompts[f"volume-title-{number}"] = title.strip()

    chapter_re = re.compile(
        r"^### 第\s*(\d+)\s*章[^\n]*\n"
        r".*?^\*\*中文\*\*\s*\n"
        r"(.*?)(?=^\*\*English\*\*)",
        re.M | re.S,
    )
    for number, prompt in chapter_re.findall(text):
        prompts[f"chapter-{int(number):02d}"] = " ".join(
            line.strip() for line in prompt.splitlines() if line.strip())

    if len([key for key in prompts if key.startswith("chapter-")]) != 51:
        raise ValueError("章节提示词数量不是 51")
    volume_count = sum(
        bool(re.fullmatch(r"volume-卷[一二三四五]", key)) for key in prompts
    )
    if volume_count != 5:
        raise ValueError("卷首提示词数量不是 5")
    return prompts


def build_prompt(key, prompt):
    if key == "cover":
        return (
            f"{COMMON} 一张文学小说封面，极简但旧。画面上方三分之二是铅灰色天空，"
            "由近黑渐变到冷灰，看不见太阳，有极细的雨丝纹理和旧胶片划痕；"
            "下方三分之一是一条笔直、微弱发亮的地平线，地平线以下是深蓝近黑、"
            "安静、无波纹的水面。画面正中保留大片空白，不画人、不画船、不画具体物体。"
            "整体像一张在极寒中放置很久、边缘受潮磨损的老照片：冷、旧、辽阔、悲伤，"
            "不精致、不干净、没有商业海报感。竖幅 2:3。"
            f" {NEGATIVE}"
        )

    if key.startswith("chapter-"):
        chapter = int(key.split("-")[1])
        style = GRAY_STYLE if chapter <= 23 else EARTH_STYLE
        extra = (
            "严禁出现海、大面积蓝色水体、树、绿草或大型动物。"
            if chapter <= 23
            else "允许海和绿色植物，但不要现代都市、垃圾或科技广告感。"
        )
    else:
        volume = key.split("-")[1]
        style = GRAY_STYLE if volume in {"卷一", "卷二", "卷三"} else EARTH_STYLE
        extra = (
            "严禁出现海、大面积蓝色水体、树、绿草或大型动物。"
            if volume in {"卷一", "卷二", "卷三"}
            else "允许海和绿色植物，但不要现代都市、垃圾或科技广告感。"
        )
    return f"{COMMON} {style} {extra} {prompt} 整体必须冷、旧、脏，人物疲惫颓废。 {NEGATIVE}"


def run_command(args):
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=360,
        check=False,
    )


def generate_one(item, force=False):
    key, output, size, prompt = item
    if output.exists() and not force:
        return key, True, f"跳过，已存在 {output.relative_to(ROOT)}"

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "animal-mediakit",
        "generate",
        "image",
        prompt,
        "--model",
        "gpt-image-2",
        "--size",
        size,
        "--quality",
        "high",
        "-o",
        str(output),
        "--json",
    ]
    last_error = ""
    for attempt in range(1, 4):
        result = run_command(command)
        if result.returncode == 0:
            return key, True, f"完成 {output.relative_to(ROOT)}"
        last_error = result.stdout[-1200:]
        if attempt < 3:
            print(f"[{key}] 第 {attempt} 次失败，重试", file=sys.stderr, flush=True)
    return key, False, last_error


def build_items(prompts):
    items = []
    cover_base = REFERENCE_DIR / "封面-B-底图.png"
    items.append((
        "cover",
        cover_base,
        "1024x1536",
        build_prompt("cover", prompts["cover"]),
    ))
    for volume in ("卷一", "卷二", "卷三", "卷四", "卷五"):
        key = f"volume-{volume}"
        items.append((
            key,
            VOLUME_DIR / f"{key}.png",
            "1536x1024",
            build_prompt(key, prompts[key]),
        ))
    for number in range(1, 52):
        key = f"chapter-{number:02d}"
        items.append((
            key,
            CHAPTER_DIR / f"{key}.png",
            "1536x1024",
            build_prompt(key, prompts[key]),
        ))
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="只生成指定 key，如 cover chapter-03")
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if shutil.which("animal-mediakit") is None:
        raise SystemExit("找不到 animal-mediakit，请先运行 animal-mediakit Skill 的 init.sh")

    prompts = parse_prompts()
    items = build_items(prompts)
    if args.only:
        wanted = set(args.only)
        items = [item for item in items if item[0] in wanted]
        missing = wanted - {item[0] for item in items}
        if missing:
            raise SystemExit("未知 key: " + ", ".join(sorted(missing)))

    ILLUSTRATIONS.mkdir(parents=True, exist_ok=True)
    print(f"准备生成 {len(items)} 张图，并行 {args.parallel}", flush=True)
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [pool.submit(generate_one, item, args.force) for item in items]
        for future in concurrent.futures.as_completed(futures):
            key, ok, message = future.result()
            print(f"[{key}] {message}", flush=True)
            if not ok:
                failed.append(key)

    manifest = {
        key: str(path.relative_to(ROOT))
        for key, path, _, _ in items
        if path.exists()
    }
    (ILLUSTRATIONS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if failed:
        raise SystemExit("失败: " + ", ".join(failed))


if __name__ == "__main__":
    main()
