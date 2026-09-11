# -*- coding: utf-8 -*-
"""生成《寒垠遗民》封面 SVG。

一次产出两个文件，画面完全一致，用的是同一份 LAYOUT：
  封面-寒垠遗民.svg        文字版：用 <text>，体积小，想改字直接改
  封面-寒垠遗民-转曲.svg    轮廓版：文字已转成路径，不依赖本机字体

用法：  python 生成封面SVG.py
"""
import os, re
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
WEIGHT = 300

W, H = 1600, 2400

SERIF = '"Noto Serif SC Light","Noto Serif SC","Source Han Serif SC",serif'

# name, lines, top, fontsize, line-height 倍数, 字距, 颜色, 不透明度
LAYOUT = [
    dict(name="genre",  lines=["未来 · 星际难民 · 生态科幻 · 第一人称"],
         top=150,  fs=25,  lh=1.448, ls=13.0,  fill="#ced8e4", op=0.44),
    dict(name="title",  lines=["寒垠遗民"],
         top=368,  fs=196, lh=1.448, ls=39.2,  fill="#f3f6f9", op=1.00, shadow=True),
    dict(name="author", lines=["jwk000"],
         top=790,  fs=41,  lh=1.448, ls=12.3,  fill="#eaf0f7", op=0.82),
    dict(name="alias",  lines=["又名《我从未见过海》"],
         top=886,  fs=33,  lh=1.448, ls=9.9,   fill="#d6e0ec", op=0.58),
    dict(name="song",   lines=["蓝的，咸的，一直响的，",
                               "一直响的，回头又回过头，",
                               "我在岸上等你，你在岸上等我，",
                               "我们谁也没到过岸上。"],
         top=1074, fs=29,  lh=2.35,  ls=4.64,  fill="#bcccdc", op=0.34),
    dict(name="plate",  lines=["灰星　KN-8813-e"],
         top=2246, fs=22,  lh=1.448, ls=13.64, fill="#98bcd8", op=0.42),
]

# ---------- 字体纵向度量：把 CSS 的 top 换算成 SVG 的基线 ----------
_f = TTFont(FONT_PATH)
_upem = _f["head"].unitsPerEm
_hhea = _f["hhea"]
ASC = _hhea.ascender / _upem
DESC = -_hhea.descender / _upem
GAP = _hhea.lineGap / _upem
LH_NORMAL = ASC + DESC + GAP

def baseline(top, fs, lh):
    return top + (lh * fs - LH_NORMAL * fs) / 2 + ASC * fs

# ---------- 轮廓版用的字形数据 ----------
_l = TTFont(FONT_PATH)
_l = instancer.instantiateVariableFont(_l, {"wght": WEIGHT})
CMAP = _l.getBestCmap()
GSET = _l.getGlyphSet()
HMTX = _l["hmtx"]
_cache = {}

def glyph(ch):
    """返回 (path 的 d，前进宽度 / upem)；没这个字形就 (None, 0)"""
    if ch in _cache:
        return _cache[ch]
    name = CMAP.get(ord(ch))
    if name is None:
        r = (None, 0.0)
    else:
        pen = SVGPathPen(GSET)
        GSET[name].draw(pen)
        r = (pen.getCommands() or None, HMTX[name][0] / _upem)
    _cache[ch] = r
    return r

def num(v):
    """坐标：一位小数就够"""
    return f"{v:.1f}".rstrip("0").rstrip(".")

def sc(v):
    """缩放系数：只有 0.0x 量级，必须留足精度"""
    return f"{v:.6f}".rstrip("0").rstrip(".")

def round_path(d):
    return re.sub(r"-?\d+\.\d+", lambda m: num(float(m.group(0))), d)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

DEFS = '''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0b0d11"/><stop offset=".24" stop-color="#14181e"/>
    <stop offset=".5" stop-color="#232931"/><stop offset=".78" stop-color="#39414b"/>
    <stop offset="1" stop-color="#4f5865"/>
  </linearGradient>
  <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1b3545"/><stop offset=".14" stop-color="#0e2233"/>
    <stop offset=".42" stop-color="#071624"/><stop offset="1" stop-color="#02080e"/>
  </linearGradient>
  <linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#82b9e1" stop-opacity=".2"/>
    <stop offset=".42" stop-color="#5a8cb9" stop-opacity=".07"/>
    <stop offset="1" stop-color="#000000" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="hline" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#96b4cd" stop-opacity="0"/>
    <stop offset=".18" stop-color="#c4def3" stop-opacity=".72"/>
    <stop offset=".5" stop-color="#e4f3ff" stop-opacity=".95"/>
    <stop offset=".82" stop-color="#c4def3" stop-opacity=".72"/>
    <stop offset="1" stop-color="#96b4cd" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" gradientUnits="userSpaceOnUse" cx="800" cy="1008" r="1"
      gradientTransform="translate(800 1008) scale(2400 2520)">
    <stop offset="0" stop-color="#000000" stop-opacity="0"/>
    <stop offset=".46" stop-color="#000000" stop-opacity=".06"/>
    <stop offset=".72" stop-color="#000000" stop-opacity=".28"/>
    <stop offset="1" stop-color="#000000" stop-opacity=".55"/>
  </radialGradient>
  <filter id="rainF" filterUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1620"
      color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.55 0.006" numOctaves="2" seed="9"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <filter id="grainF" filterUnits="userSpaceOnUse" x="0" y="0" width="1600" height="2400"
      color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" seed="1"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <filter id="hSoft" filterUnits="userSpaceOnUse" x="0" y="1500" width="1600" height="240">
    <feGaussianBlur stdDeviation="16"/>
  </filter>
  <filter id="hWide" filterUnits="userSpaceOnUse" x="0" y="1400" width="1600" height="440">
    <feGaussianBlur stdDeviation="56"/>
  </filter>
  <filter id="titleShadow" filterUnits="userSpaceOnUse" x="180" y="300" width="1240" height="440"
      color-interpolation-filters="sRGB">
    <feDropShadow dx="0" dy="3" stdDeviation="14" flood-color="#000000" flood-opacity=".6"/>
  </filter>
</defs>'''

BACKDROP = '''<rect width="1600" height="1620" fill="url(#sky)"/>
<rect y="1620" width="1600" height="780" fill="url(#sea)"/>
<rect y="1621" width="1600" height="460" fill="url(#glow)"/>
<rect width="1600" height="1620" filter="url(#rainF)" opacity=".05"/>
<rect y="1618" width="1600" height="2" fill="url(#hline)" filter="url(#hWide)" opacity=".55"/>
<rect y="1618" width="1600" height="2" fill="url(#hline)" filter="url(#hSoft)"/>
<rect y="1618" width="1600" height="2" fill="url(#hline)"/>
<rect width="1600" height="2400" fill="url(#vig)"/>'''

GRAIN = '<rect width="1600" height="2400" filter="url(#grainF)" opacity=".055"/>'

HEAD = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     role="img" aria-label="寒垠遗民 封面">
<title>寒垠遗民</title>
<desc>未来 · 星际难民 · 生态科幻 · 第一人称　作者 jwk000</desc>'''

def text_version():
    out = []
    for it in LAYOUT:
        y0 = baseline(it["top"], it["fs"], it["lh"])
        step = it["lh"] * it["fs"]
        attr = ' filter="url(#titleShadow)"' if it.get("shadow") else ""
        g = [f'<g fill="{it["fill"]}" fill-opacity="{it["op"]}"{attr}>']
        for i, s in enumerate(it["lines"]):
            y = y0 + i * step
            x = 800 + it["ls"] / 2
            g.append(f'<text x="{num(x)}" y="{num(y)}" text-anchor="middle" '
                     f'font-family=\'{SERIF}\' font-size="{num(it["fs"])}" '
                     f'font-weight="{WEIGHT}" letter-spacing="{num(it["ls"])}">{esc(s)}</text>')
        g.append("</g>")
        out.append("\n".join(g))
    return "\n".join(out)

def outline_version():
    scale = lambda fs: fs / _upem
    out = []
    for it in LAYOUT:
        fs, ls = it["fs"], it["ls"]
        y0 = baseline(it["top"], fs, it["lh"])
        step = it["lh"] * fs
        attr = ' filter="url(#titleShadow)"' if it.get("shadow") else ""
        g = [f'<g fill="{it["fill"]}" fill-opacity="{it["op"]}"{attr}>']
        for i, s in enumerate(it["lines"]):
            y = y0 + i * step
            adv = [glyph(c)[1] * fs for c in s]
            ink = sum(adv) + ls * (len(s) - 1)
            x = 800 - ink / 2
            for c, a in zip(s, adv):
                d, _ = glyph(c)
                if d:
                    g.append(f'<path transform="translate({num(x)} {num(y)}) '
                             f'scale({sc(scale(fs))} {sc(-scale(fs))})" d="{round_path(d)}"/>')
                x += a + ls
        g.append("</g>")
        out.append("\n".join(g))
    return "\n".join(out)

for fname, body in (("封面-寒垠遗民.svg", text_version()),
                    ("封面-寒垠遗民-转曲.svg", outline_version())):
    svg = f"{HEAD}\n{DEFS}\n{BACKDROP}\n{body}\n{GRAIN}\n</svg>\n"
    p = os.path.join(HERE, fname)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print(f"{fname}  {len(svg.encode('utf-8'))/1024:.1f} KB  ->  {p}")
print("-" * 46)
print(f"字体度量  升部 {ASC:.3f}  降部 {DESC:.3f}  normal={LH_NORMAL:.3f}")
for it in LAYOUT:
    print(f"  {it['name']:<7} baseline = {baseline(it['top'], it['fs'], it['lh']):.1f}")