"""Set Chinese Word text to Songti SC while preserving content and other formatting.

Install the document dependencies before use. This patches OOXML rather than rebuilding the
document, so existing annotations, hyperlinks, and document structure survive.
"""

import argparse
from copy import deepcopy
from itertools import groupby
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

CHINESE_FONT = "Songti SC"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def w(name):
    return f"{{{W}}}{name}"


def chinese_character(char):
    number = ord(char)
    return any(start <= number <= end for start, end in [
        (0x2E80, 0x2EFF), (0x2F00, 0x2FDF), (0x3000, 0x303F),
        (0x3100, 0x312F), (0x31A0, 0x31BF), (0x3400, 0x4DBF),
        (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0xFE10, 0xFE1F),
        (0xFE30, 0xFE4F), (0xFF00, 0xFFEF), (0x20000, 0x2FA1F),
        (0x30000, 0x323AF),
    ])


def chinese_run_properties(run):
    props = run.find(w("rPr"))
    if props is None:
        props = etree.Element(w("rPr"))
        run.insert(0, props)
    fonts = props.find(w("rFonts"))
    if fonts is None:
        fonts = etree.Element(w("rFonts"))
        props.insert(0, fonts)
    fonts.attrib.clear()
    for slot in ["ascii", "hAnsi", "eastAsia", "cs"]:
        fonts.set(w(slot), CHINESE_FONT)
    fonts.set(w("hint"), "eastAsia")
    language = props.find(w("lang"))
    if language is None:
        language = etree.SubElement(props, w("lang"))
    language.set(w("val"), "zh-CN")
    language.set(w("eastAsia"), "zh-CN")


def normalize_word_xml(root):
    # Set the East Asian slot in defaults, styles, numbering, and direct fonts.
    # Retain the existing Latin font attributes and remove only its CJK theme.
    for fonts in root.iter(w("rFonts")):
        fonts.set(w("eastAsia"), CHINESE_FONT)
        fonts.attrib.pop(w("eastAsiaTheme"), None)
    for run in list(root.iter(w("r"))):
        text_nodes = run.findall(w("t"))
        if len(text_nodes) != 1 or not any(chinese_character(c) for c in text_nodes[0].text or ""):
            continue
        # Split simple text runs so Word's font selector also shows Songti for
        # Chinese characters inside a mixed English/Chinese sentence.
        if any(child.tag not in {w("rPr"), w("t")} for child in run):
            props = run.find(w("rPr"))
            if props is None:
                props = etree.Element(w("rPr"))
                run.insert(0, props)
            fonts = props.find(w("rFonts"))
            if fonts is None:
                fonts = etree.SubElement(props, w("rFonts"))
            fonts.set(w("eastAsia"), CHINESE_FONT)
            fonts.attrib.pop(w("eastAsiaTheme"), None)
            continue
        text = text_nodes[0].text
        groups = [(kind, "".join(chars)) for kind, chars in groupby(
            text, key=lambda c: chinese_character(c) or c in "‘’“”"
        )]
        parent = run.getparent()
        position = parent.index(run)
        for offset, (is_chinese, value) in enumerate(groups):
            replacement = deepcopy(run)
            node = replacement.find(w("t"))
            node.text = value
            if value[:1].isspace() or value[-1:].isspace():
                node.set(XML_SPACE, "preserve")
            if is_chinese:
                chinese_run_properties(replacement)
            parent.insert(position + offset, replacement)
        parent.remove(run)


def normalize_theme_xml(root):
    for group in ["majorFont", "minorFont"]:
        fonts = root.find(f".//{{{A}}}{group}")
        if fonts is None:
            continue
        east_asia = fonts.find(f"{{{A}}}ea")
        if east_asia is not None:
            east_asia.set("typeface", CHINESE_FONT)
        for font in fonts.findall(f"{{{A}}}font"):
            if font.get("script") in {"Hans", "Hant"}:
                font.set("typeface", CHINESE_FONT)


def normalize_font_table(root):
    if any(font.get(w("name")) == CHINESE_FONT for font in root.findall(w("font"))):
        return
    font = etree.SubElement(root, w("font"))
    font.set(w("name"), CHINESE_FONT)
    alias = etree.SubElement(font, w("altName"))
    alias.set(w("val"), "宋体-简")
    family = etree.SubElement(font, w("family"))
    family.set(w("val"), "roman")
    pitch = etree.SubElement(font, w("pitch"))
    pitch.set(w("val"), "variable")


def apply_bilingual_fonts(path):
    original = path.read_bytes()
    temporary = path.with_name(f".{path.name}.fonts.tmp")
    try:
        with ZipFile(path) as source, ZipFile(temporary, "w") as target:
            for part in source.infolist():
                content = source.read(part.filename)
                if part.filename.startswith("word/") and part.filename.endswith(".xml"):
                    root = etree.fromstring(content)
                    text_before = [node.text for node in root.iter(w("t"))]
                    if root.tag == w("fonts"):
                        normalize_font_table(root)
                    elif root.tag == f"{{{A}}}theme":
                        normalize_theme_xml(root)
                    else:
                        normalize_word_xml(root)
                    text_after = [node.text for node in root.iter(w("t"))]
                    if "".join(t or "" for t in text_before) != "".join(t or "" for t in text_after):
                        raise ValueError(f"Text changed unexpectedly in {part.filename}")
                    content = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                target.writestr(part, content)
        # Avoid replacing a document that changed during the font operation.
        if path.read_bytes() != original:
            raise ValueError("Document changed during font editing; preserving it")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    args = parser.parse_args()
    apply_bilingual_fonts(args.document)
    print(f"Chinese text set to {CHINESE_FONT}: {args.document}")
