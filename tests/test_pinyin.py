"""Pinyin letters (uswds/public-sans#258) exist as precomposed glyphs, and M/m take combining marks."""
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from conftest import static_path

PINYIN = "ǍǏǑǓǎǐǒǔǕǗǙǛǖǘǚǜḾǸḿǹ"
STACKED = "ǕǗǙǛǖǘǚǜ"
SINGLE_MARK = [c for c in PINYIN if c not in STACKED and c not in "Ǔǔ"]


def bounds(gs, name):
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return bp.bounds


def contours(gs, name):
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    return sum(1 for op, _ in pen.value if op == "moveTo")


def test_every_pinyin_letter_is_mapped(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert [c for c in PINYIN if ord(c) not in cmap] == []


def test_variable_fonts_map_pinyin(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert [c for c in PINYIN if ord(c) not in cmap] == []


@pytest.mark.parametrize("letter", PINYIN)
def test_pinyin_letter_keeps_base_advance_and_adds_marks(static_ttf, letter):
    cmap = static_ttf.getBestCmap()
    gs = static_ttf.getGlyphSet()
    base = unicodedata.normalize("NFD", letter)[0]
    base = "ı" if base == "i" else base  # the composite sits on dotless i
    name = cmap[ord(letter)]
    assert static_ttf["hmtx"][name][0] == static_ttf["hmtx"][cmap[ord(base)]][0]
    assert bounds(gs, name)[3] > bounds(gs, cmap[ord(base)])[3]
    extra = 2 if letter in STACKED else 1
    assert contours(gs, name) >= contours(gs, cmap[ord(base)]) + extra


@pytest.mark.parametrize("letter", STACKED)
def test_stacked_marks_do_not_touch(static_ttf, letter):
    """The tone mark clears the diaeresis: the stacked glyph is taller than the diaeresis-only letter."""
    cmap = static_ttf.getBestCmap()
    gs = static_ttf.getGlyphSet()
    diaeresis = cmap[ord("Ü" if letter.isupper() else "ü")]
    assert bounds(gs, cmap[ord(letter)])[3] > bounds(gs, diaeresis)[3] + 100


@pytest.mark.parametrize("letter", SINGLE_MARK)
def test_combining_sequence_matches_precomposed(letter):
    """Base plus combining mark shapes to the same ink extents as the precomposed letter (marks attach to M/m too)."""
    path = static_path("Regular", False)
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def ink(text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, {"kern": False})
        x0 = y0 = 1e9
        x1 = y1 = -1e9
        pen = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            b = bounds(gs, order[info.codepoint])
            if b:
                x0, x1 = min(x0, pen + pos.x_offset + b[0]), max(x1, pen + pos.x_offset + b[2])
                y0, y1 = min(y0, pos.y_offset + b[1]), max(y1, pos.y_offset + b[3])
            pen += pos.x_advance
        return x0, y0, x1, y1

    seq = ink(unicodedata.normalize("NFD", letter))
    pre = ink(letter)
    assert all(abs(a - b) <= 2 for a, b in zip(seq, pre)), (letter, seq, pre)
