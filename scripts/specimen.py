"""Render docs/specimen.png from the built static TTFs, quoting the statutes in docs/proof/allemansratten.txt.

With --social it renders build/social-preview.png instead: the 1280 x 640 image GitHub shows when a link to the
repository is shared, uploaded by hand under Settings > General > Social preview.

HarfBuzz shapes each line (so GPOS kerning applies) and Pillow draws each glyph at its shaped position.
The page is drawn at twice the output size and downsampled, which keeps glyph positions sub-pixel accurate.
"""
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TTF = ROOT / "fonts" / "OffentligSans" / "ttf"
OUT = ROOT / "docs" / "specimen.png"
SOCIAL_OUT = ROOT / "build" / "social-preview.png"

WIDTH, MARGIN, SS = 1600, 100, 2
CONTENT = WIDTH - 2 * MARGIN
INK, MUTED = (17, 17, 17), (110, 110, 110)
WEIGHTS = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"]

QUOTE_RF = "Alla ska ha tillgång till naturen enligt allemansrätten."
QUOTE_MB = ("Var och en som utnyttjar allemansrätten eller annars vistas i naturen "
            "skall visa hänsyn och varsamhet i sitt umgänge med den.")
SOURCE_RF = "Regeringsformen 2 kap. 15 §"
SOURCE_MB = "Miljöbalken 7 kap. 1 §"
WEIGHT_SAMPLE = "Åäö"

_fonts = {}


def font(style):
    if style not in _fonts:
        path = TTF / f"OffentligSans-{style}.ttf"
        blob = hb.Blob.from_file_path(str(path))
        tt = TTFont(path)
        _fonts[style] = (path, hb.Font(hb.Face(blob)), tt["head"].unitsPerEm, tt.getBestCmap(), tt.getGlyphOrder())
    return _fonts[style]


def shape(style, text):
    _, hbfont, _, _, _ = font(style)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True})
    return buf.glyph_infos, buf.glyph_positions


def width(style, text, size):
    _, _, upem, _, _ = font(style)
    return sum(p.x_advance for p in shape(style, text)[1]) * size / upem


def draw_line(draw, style, text, size, x, baseline, fill):
    """Draw one shaped line; x and baseline are in output pixels."""
    path, _, upem, cmap, order = font(style)
    pil = ImageFont.truetype(str(path), round(size * SS), layout_engine=ImageFont.Layout.BASIC)
    infos, positions = shape(style, text)
    scale = size * SS / upem
    pen = x * SS
    for info, pos in zip(infos, positions):
        ch = text[info.cluster]
        # Pillow draws by character, so every shaped glyph must be the default glyph of its character.
        assert cmap.get(ord(ch)) == order[info.codepoint], f"{style}: {ch!r} shaped to {order[info.codepoint]}"
        if not ch.isspace():
            draw.text((pen + pos.x_offset * scale, baseline * SS - pos.y_offset * scale), ch,
                      font=pil, fill=fill, anchor="ls")
        pen += pos.x_advance * scale


def wrap(style, text, size, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and width(style, trial, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def fit(style, text, max_width):
    return max_width / width(style, text, 1)


def main():
    title_size = 132
    rf_size = fit("Regular", QUOTE_RF, CONTENT)
    mb_size = 44
    caption_size = 24
    mb_lines = wrap("Italic", QUOTE_MB, mb_size, CONTENT)
    column = CONTENT / len(WEIGHTS)
    sample_size = min(fit("Black", WEIGHT_SAMPLE, column * 0.86), 92)

    # Vertical layout: baselines measured from the top margin. Cap height is 0.723 em.
    y = MARGIN + 0.723 * title_size
    plan = [("line", "Bold", "Offentlig Sans", title_size, MARGIN, y, INK)]
    y += 0.723 * rf_size + 96
    plan.append(("line", "Regular", QUOTE_RF, rf_size, MARGIN, y, INK))
    y += 50
    plan.append(("line", "Regular", SOURCE_RF, caption_size, MARGIN, y, MUTED))
    y += 0.723 * mb_size + 64
    for i, text in enumerate(mb_lines):
        plan.append(("line", "Italic", text, mb_size, MARGIN, y, INK))
        y += mb_size * 1.3 if i < len(mb_lines) - 1 else 0
    y += 46
    plan.append(("line", "Regular", SOURCE_MB, caption_size, MARGIN, y, MUTED))
    y += 0.723 * sample_size + 92
    for i, weight in enumerate(WEIGHTS):
        left = MARGIN + i * column
        w = width(weight, WEIGHT_SAMPLE, sample_size)
        plan.append(("line", weight, WEIGHT_SAMPLE, sample_size, left + (column - w) / 2, y, INK))
        lw = width("Regular", weight, caption_size)
        plan.append(("line", "Regular", weight, caption_size, left + (column - lw) / 2, y + 48, MUTED))
    height = round(y + 48 + MARGIN)

    render(plan, WIDTH, height, OUT)


def render(plan, page_width, page_height, out):
    page = Image.new("RGB", (page_width * SS, page_height * SS), "white")
    draw = ImageDraw.Draw(page)
    for _, style, text, size, x, baseline, fill in plan:
        draw_line(draw, style, text, size, x, baseline, fill)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.resize((page_width, page_height), Image.Resampling.LANCZOS).save(out, optimize=True)
    print(f"wrote {out.relative_to(ROOT)} ({page_width} x {page_height})")


def social():
    """GitHub's recommended 1280 x 640, with wide side margins because some sites crop shared links to 1.91:1."""
    page_width, page_height, side = 1280, 640, 140
    content = page_width - 2 * side
    title_size = 104
    quote = "Alla ska ha tillgång till naturen"
    quote_size = fit("Regular", quote, content)
    column = content / len(WEIGHTS)
    sample_size = fit("Black", WEIGHT_SAMPLE, column * 0.86)

    # Baselines relative to the top of the block, then the block is centred vertically. Cap height is 0.723 em.
    y = 0.723 * title_size
    rows = [("Bold", "Offentlig Sans", title_size, side, y)]
    y += 0.723 * quote_size + 64
    rows.append(("Regular", quote, quote_size, side, y))
    y += 0.723 * sample_size + 80
    for i, weight in enumerate(WEIGHTS):
        w = width(weight, WEIGHT_SAMPLE, sample_size)
        rows.append((weight, WEIGHT_SAMPLE, sample_size, side + i * column + (column - w) / 2, y))
    top = (page_height - y) / 2
    plan = [("line", style, text, size, x, top + baseline, INK) for style, text, size, x, baseline in rows]
    render(plan, page_width, page_height, SOCIAL_OUT)


if __name__ == "__main__":
    social() if "--social" in sys.argv[1:] else main()
