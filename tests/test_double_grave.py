"""The narrow double grave on `ȉ ȑ` and on typed `i ı r` + U+030F.

`ȉ ȑ` use `dblgravecomb.narrow`, drawn in the six masters to overhang the stem by no more than the breve of `ĭ` plus 40 units
(the full-width mark made pairs with `ȉ` need over 300 units of kerning). Typed `i ı r` + U+030F swap to the narrow mark in `ccmp`,
so they set exactly like `ȉ ȑ`; every other base keeps the full-width mark.
"""
import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import static_path
from test_spacing import ALL_FONTS, ALL_IDS

DOUBLE_GRAVE = "̏"


def ink(weight, italic, text, features=None):
    """(left, right, advance) of the ink of the shaped text, in font units, marks placed by GPOS."""
    path = static_path(weight, italic)
    font = TTFont(path)
    glyphs, order = font.getGlyphSet(), font.getGlyphOrder()
    face = hb.Font(hb.Face(path.read_bytes()))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(face, buf, dict(features or {}, kern=False))
    x, lo, hi = 0, None, None
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = BoundsPen(glyphs)
        glyphs[order[info.codepoint]].draw(pen)
        if pen.bounds:
            a, b = x + pos.x_offset + pen.bounds[0], x + pos.x_offset + pen.bounds[2]
            lo, hi = (a if lo is None else min(lo, a)), (b if hi is None else max(hi, b))
        x += pos.x_advance
    return lo, hi, x


@pytest.mark.parametrize("features", [None, {"ss03": True}], ids=["default", "ss03"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_typed_i_dotless_i_and_r_with_a_double_grave_set_like_the_precomposed_letters(weight, italic, features):
    for typed, precomposed in (("i", "ȉ"), ("ı", "ȉ"), ("r", "ȑ")):
        a = ink(weight, italic, typed + DOUBLE_GRAVE, features)
        b = ink(weight, italic, precomposed, features)
        assert max(abs(x - y) for x, y in zip(a, b)) <= 1, (typed, a, b)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_the_double_grave_on_i_reaches_no_further_than_the_breve_of_i(weight, italic):
    """`ȉ` overhangs its advance on each side by no more than `ĭ` does, plus 40 units (the full-width mark overhung by up to 390)."""
    lo, hi, advance = ink(weight, italic, "ȉ")
    blo, bhi, _ = ink(weight, italic, "ĭ")
    assert -lo <= max(-blo, 0) + 40 and hi - advance <= max(bhi - advance, 0) + 40, (lo, hi, advance, blo, bhi)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_other_letters_keep_the_full_width_double_grave(weight, italic):
    """`ȁ ȅ ȍ ȕ` and the capitals keep the mark they had: the typed `a` + U+030F is as wide as the precomposed `ȁ`."""
    typed = ink(weight, italic, "a" + DOUBLE_GRAVE)
    assert max(abs(x - y) for x, y in zip(typed, ink(weight, italic, "ȁ"))) <= 1
    narrow = ink(weight, italic, "ȉ")
    assert narrow[1] - narrow[0] < typed[1] - typed[0]
