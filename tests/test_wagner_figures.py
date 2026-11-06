"""Figure invariants (Rosalie Wagner's list, uswds/public-sans#158)."""
import math

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path

ITALIC_ANGLE = 8  # degrees; `post.italicAngle` of the italic masters


def shaped_glyph(path, font, digit, feature):
    blob = hb.Blob.from_file_path(str(path))
    hbfont = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(digit)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {feature: True})
    return font.getGlyphOrder()[buf.glyph_infos[0].codepoint]


def bounds(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
@pytest.mark.parametrize("digit", "0123456789")
def test_superior_figures_follow_the_italic_slant(weight, italic, digit):
    """A superior figure sits where the numerator figure would be if raised along the slant: dx = rise * tan(angle) in italic, 0 in upright."""
    path = static_path(weight, italic)
    font = TTFont(path)
    sup = bounds(font, shaped_glyph(path, font, digit, "sups"))
    numr = bounds(font, shaped_glyph(path, font, digit, "numr"))
    rise = sup[1] - numr[1]
    expected = rise * math.tan(math.radians(ITALIC_ANGLE)) if italic else 0
    assert sup[0] - numr[0] == pytest.approx(expected, abs=3), f"dx {sup[0] - numr[0]:.1f}, rise {rise:.1f}"
