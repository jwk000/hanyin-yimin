# -*- coding: utf-8 -*-
"""把《寒垠遗民》的 GitBook 书稿打包成 EPUB，并另存一份可打印成 PDF 的单页 HTML。

只依赖 Python 标准库，不需要安装任何东西。
用法：  python 生成EPUB.py
产物：  输出/寒垠遗民.epub
        输出/打印版.html
"""

import html
import os
import re
import uuid
import zipfile
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(ROOT, "输出")

BOOK_TITLE = "寒垠遗民"
BOOK_SUBTITLE = ""
BOOK_AUTHOR = "jwk000"
BOOK_DESC = "未来 · 星际难民 · 生态科幻 · 回忆"

JUAN = {"卷一": "juan1", "卷二": "juan2", "卷三": "juan3", "卷四": "juan4", "卷五": "juan5"}
COVER_IMAGE = os.path.join(ROOT, "封面", "封面-寒垠遗民-插画版.jpg")
VOLUME_IMAGE_DIR = os.path.join(ROOT, "插画",  "卷首")
CHAPTER_IMAGE_DIR = os.path.join(ROOT, "插画",  "章首")

CSS = """@charset "utf-8";
html { font-size: 100%; }
body {
  font-family: "Songti SC", "Source Han Serif SC", "Noto Serif CJK SC", "SimSun", serif;
  line-height: 1.75;
  margin: 0 5%;
  color: #1a1a1a;
  text-align: justify;
}
h1 { font-size: 1.5em; line-height: 1.4; margin: 1.6em 0 1.2em; text-align: center; font-weight: normal; letter-spacing: .06em; }
h2 { font-size: 1.2em; margin: 1.4em 0 1em; text-align: center; font-weight: normal; }
p { margin: 0; text-indent: 2em; orphans: 2; widows: 2; }
p.noindent { text-indent: 0; }
hr.sep { border: 0; border-top: 1px solid #bbb; width: 22%; margin: 1.5em auto; }
blockquote { margin: 1.4em 12%; padding: 0; }
blockquote p { text-indent: 0; font-style: normal; line-height: 2; color: #333; }
strong { font-weight: bold; }
a { color: #3b5c78; text-decoration: none; }
.title-page { text-align: center; margin-top: 22%; }
.title-page h1 { font-size: 2.1em; letter-spacing: .18em; }
.title-page .sub { margin-top: 1.2em; color: #555; }
.title-page .desc { margin-top: .6em; color: #777; font-size: .92em; }
.cover-page { text-align: center; margin: 0; padding: 0; }
.cover-page img { max-width: 100%; max-height: 100vh; object-fit: contain; }
figure.art { margin: 0 0 1.6em; padding: 0; text-align: center; page-break-inside: avoid; }
figure.art img { max-width: 100%; max-height: 72vh; object-fit: contain; }
figure.volume-art img { max-height: 78vh; }
"""

PRINT_CSS = """@charset "utf-8";
@page { size: A4; margin: 20mm 18mm 22mm; }
body { font-family: "Songti SC", "SimSun", serif; font-size: 10.5pt; line-height: 1.7; color: #111; margin: 0; text-align: justify; }
h1 { font-size: 1.45em; font-weight: normal; text-align: center; margin: 0 0 1.1em; letter-spacing: .06em; }
h2 { font-size: 1.2em; font-weight: normal; text-align: center; }
p { margin: 0; text-indent: 2em; orphans: 2; widows: 2; }
hr.sep { border: 0; border-top: 1px solid #ccc; width: 16%; margin: 0.8em auto; }
blockquote { margin: 1.2em 12%; }
blockquote p { text-indent: 0; line-height: 2; }
.chapter { break-before: page; page-break-before: always; }
.chapter:first-of-type { break-before: auto; page-break-before: auto; }
.cover-page { break-after: page; page-break-after: always; text-align: center; margin: 0; padding: 0; }
.cover-page img { max-width: 100%; max-height: 255mm; object-fit: contain; }
.part { break-before: page; page-break-before: always; text-align: center; margin: 0; }
.part img { max-width: 100%; max-height: 165mm; object-fit: contain; margin-bottom: 6mm; }
.chapter-art { margin: 0 0 10mm; text-align: center; page-break-inside: avoid; }
.chapter-art img { max-width: 100%; max-height: 125mm; object-fit: contain; }
"""


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_summary(text):
    """解析 SUMMARY.md，返回 [(part, title, relpath), ...]"""
    pages = []
    part = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            part = m.group(1)
            continue
        m = re.match(r"^\*\s+\[(.+?)\]\((.+?)\)\s*$", line)
        if m:
            pages.append((part, m.group(1), m.group(2)))
    return pages


def outname(rel):
    base = os.path.basename(rel)[:-3]
    if base.lower() == "readme":
        return "readme.xhtml"
    if base in JUAN:
        return JUAN[base] + ".xhtml"
    return base + ".xhtml"


def illustration_for(rel):
    """返回页面使用的插画源文件路径，没有插画则返回 None。"""
    base = os.path.basename(rel)[:-3]
    if base in JUAN:
        return os.path.join(VOLUME_IMAGE_DIR, "volume-%s.jpg" % base)
    match = re.fullmatch(r"ch(\d+)", base)
    if match:
        return os.path.join(CHAPTER_IMAGE_DIR, "chapter-%s.jpg" % match.group(1))
    return None


def inline(text, link_map):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    def _link(m):
        label, href = m.group(1), m.group(2)
        target = link_map.get(href, href)
        return '<a href="%s">%s</a>' % (target, label)

    return re.sub(r"\[(.+?)\]\((.+?)\)", _link, text)


def md_to_body(text, link_map):
    out = []
    quote = []

    def flush():
        if quote:
            out.append("<blockquote><p>%s</p></blockquote>" % "<br/>".join(quote))
            quote.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith(">"):
            quote.append(inline(line[1:].strip(), link_map))
            continue
        flush()
        if re.match(r"^-{3,}$", line):
            out.append('<hr class="sep"/>')
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2), link_map), lvl))
            continue
        out.append("<p>%s</p>" % inline(line, link_map))
    flush()
    return "\n".join(out)


def xhtml_doc(title, body, extra_class=""):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
        'xml:lang="zh" lang="zh">\n'
        "<head>\n<meta charset=\"utf-8\"/>\n<title>%s</title>\n"
        '<link rel="stylesheet" type="text/css" href="style.css"/>\n'
        "</head>\n<body%s>\n%s\n</body>\n</html>\n"
        % (html.escape(title, quote=False), (' class="%s"' % extra_class) if extra_class else "", body)
    )


def main():
    pages = parse_summary(read_text(os.path.join(ROOT, "SUMMARY.md")))
    if not pages:
        raise SystemExit("SUMMARY.md 里没有找到任何页面")

    link_map = {rel: outname(rel) for _, _, rel in pages}
    os.makedirs(OUTDIR, exist_ok=True)

    docs = []          # (outname, title, part, xhtml)
    image_assets = []
    for part, title, rel in pages:
        src = os.path.join(ROOT, rel.replace("/", os.sep))
        body = md_to_body(read_text(src), link_map)
        art_path = illustration_for(rel)
        if art_path:
            if not os.path.exists(art_path):
                raise SystemExit("缺少插画：%s" % art_path)
            art_name = "art-" + os.path.basename(art_path)
            figure_class = "volume-art" if os.path.basename(rel)[:-3] in JUAN else "chapter-art"
            body = (
                '<figure class="art %s"><img src="images/%s" alt="%s"/></figure>\n%s'
                % (figure_class, html.escape(art_name, quote=True),
                   html.escape(title, quote=True), body)
            )
            image_assets.append((art_name, art_path))
        if os.path.basename(rel).lower() == "readme":
            head = ('<div class="title-page"><h1>%s</h1>'
                    '<p class="sub noindent">%s</p>'
                    '<p class="desc noindent">%s</p></div>'
                    % (BOOK_TITLE, BOOK_SUBTITLE, BOOK_DESC))
            body = head + "\n" + body
        docs.append((outname(rel), title, part, xhtml_doc(title, body)))

    uid = "urn:uuid:" + str(uuid.uuid4())
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    if not os.path.exists(COVER_IMAGE):
        raise SystemExit("缺少封面：%s" % COVER_IMAGE)

    # ---------- EPUB ----------
    manifest, spine, nav_items = [], [], []
    cover_doc = xhtml_doc(
        "封面",
        '<div class="cover-page"><img src="cover-art.jpg" alt="%s"/></div>'
        % html.escape(BOOK_TITLE, quote=True),
    )
    manifest.append(
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>'
    )
    manifest.append(
        '<item id="cover-image" href="cover-art.jpg" media-type="image/jpeg" '
        'properties="cover-image"/>'
    )
    spine.append('<itemref idref="cover"/>')
    for i, (name, title, part, _) in enumerate(docs):
        manifest.append('<item id="p%d" href="%s" media-type="application/xhtml+xml"/>' % (i, name))
        spine.append('<itemref idref="p%d"/>' % i)
        nav_items.append((part, title, name))
    for i, (name, _) in enumerate(image_assets):
        manifest.append(
            '<item id="img%d" href="images/%s" media-type="image/jpeg"/>'
            % (i, html.escape(name, quote=True))
        )
    manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    manifest.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
    manifest.append('<item id="css" href="style.css" media-type="text/css"/>')

    opf = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="zh">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:identifier id="bookid">%s</dc:identifier>\n'
        '<dc:title>%s</dc:title>\n'
        '<dc:creator>%s</dc:creator>\n'
        '<dc:language>zh</dc:language>\n'
        '<dc:description>%s</dc:description>\n'
        '<meta name="cover" content="cover-image"/>\n'
        '<meta property="dcterms:modified">%s</meta>\n'
        '</metadata>\n<manifest>\n%s\n</manifest>\n<spine toc="ncx">\n%s\n</spine>\n</package>\n'
        % (uid, BOOK_TITLE, BOOK_AUTHOR, html.escape(BOOK_DESC, quote=False), stamp,
           "\n".join(manifest), "\n".join(spine))
    )

    nav_parts, current, bucket = [], None, []
    for part, title, name in nav_items:
        if part != current:
            if current is not None:
                nav_parts.append((current, bucket))
            current, bucket = part, []
        bucket.append((title, name))
    if current is not None:
        nav_parts.append((current, bucket))

    nav_body = ['<nav epub:type="toc" id="toc"><h1>目录</h1>']
    loose = nav_parts[0][1] if nav_parts and nav_parts[0][0] is None else []
    if loose:
        nav_body.append("<ol>")
        for title, name in loose:
            nav_body.append('<li><a href="%s">%s</a></li>' % (name, html.escape(title, quote=False)))
        nav_body.append("</ol>")
    for part, items in nav_parts:
        if part is None:
            continue
        nav_body.append("<ol>")
        nav_body.append('<li><span>%s</span><ol>' % html.escape(part, quote=False))
        for title, name in items:
            nav_body.append('<li><a href="%s">%s</a></li>' % (name, html.escape(title, quote=False)))
        nav_body.append("</ol></li>")
        nav_body.append("</ol>")
    nav_body.append("</nav>")

    ncx_points = []
    for k, (part, title, name) in enumerate(nav_items, start=1):
        ncx_points.append(
            '<navPoint id="n%d" playOrder="%d"><navLabel><text>%s</text></navLabel>'
            '<content src="%s"/></navPoint>'
            % (k, k, html.escape(title, quote=False), name))
    ncx = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh">\n'
        '<head><meta name="dtb:uid" content="%s"/></head>\n'
        '<docTitle><text>%s</text></docTitle>\n<navMap>\n%s\n</navMap>\n</ncx>\n'
        % (uid, BOOK_TITLE, "\n".join(ncx_points))
    )

    container = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>\n'
    )

    epub_path = os.path.join(OUTDIR, BOOK_TITLE + ".epub")
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", xhtml_doc("目录", "\n".join(nav_body)), zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", ncx, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/style.css", CSS, zipfile.ZIP_DEFLATED)
        zf.write(COVER_IMAGE, "OEBPS/cover-art.jpg")
        for name, path in image_assets:
            zf.write(path, "OEBPS/images/" + name)
        for name, _, _, doc in docs:
            zf.writestr("OEBPS/" + name, doc, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/cover.xhtml", cover_doc, zipfile.ZIP_DEFLATED)

    # ---------- 打印版 HTML（给 Chrome 出 PDF 用） ----------
    cover_src = html.escape(os.path.relpath(COVER_IMAGE, OUTDIR), quote=True)
    blocks = ['<div class="cover-page"><img src="%s" alt="%s"/></div>'
              % (cover_src, html.escape(BOOK_TITLE, quote=True))]
    for name, title, part, _ in docs:
        base = os.path.basename(name)
        if base.startswith(("readme", "juan")):
            if name.startswith("juan"):
                volume = title.split(" · ", 1)[0]
                volume_src = html.escape(
                    os.path.relpath(
                        os.path.join(VOLUME_IMAGE_DIR, "volume-%s.jpg" % volume),
                        OUTDIR,
                    ),
                    quote=True,
                )
                blocks.append(
                    '<div class="part"><img src="%s" alt="%s"/><h1>%s</h1></div>'
                    % (volume_src, html.escape(title, quote=True),
                       html.escape(title, quote=False))
                )
            continue
        chapter_source = os.path.join(ROOT, "正文", name.replace(".xhtml", ".md"))
        chapter_body = md_to_body(read_text(chapter_source), link_map)
        art_path = illustration_for(chapter_source)
        art_html = ""
        if art_path:
            art_src = html.escape(os.path.relpath(art_path, OUTDIR), quote=True)
            art_html = '<figure class="chapter-art"><img src="%s" alt="%s"/></figure>' % (
                art_src, html.escape(title, quote=True))
        blocks.append('<div class="chapter">%s%s</div>' % (art_html, chapter_body))
    print_html = (
        '<!DOCTYPE html>\n<html lang="zh">\n<head>\n<meta charset="utf-8"/>\n<title>%s</title>\n'
        "<style>%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n"
        % (BOOK_TITLE, PRINT_CSS, "\n".join(blocks))
    )
    with open(os.path.join(OUTDIR, "打印版.html"), "w", encoding="utf-8") as fh:
        fh.write(print_html)

    print("EPUB  ->  %s" % epub_path)
    print("打印版 ->  %s" % os.path.join(OUTDIR, "打印版.html"))
    print("页面数：%d" % len(docs))


if __name__ == "__main__":
    main()
