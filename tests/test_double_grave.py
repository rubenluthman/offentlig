"""The narrow double grave on `ȉ ȑ` and on typed `i ı r` + U+030F, also on the bases with a mark below.

`ȉ ȑ` use `dblgravecomb.narrow`, drawn in the six masters to overhang the stem by no more than the breve of `ĭ`
(the full-width mark made pairs with `ȉ` need over 300 units of kerning). Typed `i ı r` + U+030F swap to the narrow mark in `ccmp`,
so they set exactly like `ȉ ȑ`; every other base keeps the full-width mark. `ị į ɨ ṛ ṟ ŗ` (precomposed or typed with the
mark below) take the narrow mark too, and no more overhang than they have with a breve.
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
    """`ȉ` overhangs its advance on each side by no more than `ĭ` does, in every weight (the full-width mark overhung by up to 390)."""
    lo, hi, advance = ink(weight, italic, "ȉ")
    blo, bhi, _ = ink(weight, italic, "ĭ")
    assert -lo <= max(-blo, 0) and hi - advance <= max(bhi - advance, 0), (lo, hi, advance, blo, bhi)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_other_letters_keep_the_full_width_double_grave(weight, italic):
    """`ȁ ȅ ȍ ȕ` and the capitals keep the mark they had: the typed `a` + U+030F is as wide as the precomposed `ȁ`."""
    typed = ink(weight, italic, "a" + DOUBLE_GRAVE)
    assert max(abs(x - y) for x, y in zip(typed, ink(weight, italic, "ȁ"))) <= 1
    narrow = ink(weight, italic, "ȉ")
    assert narrow[1] - narrow[0] < typed[1] - typed[0]


BELOW = ["ị", "į", "ɨ", "ṛ", "ṟ", "ŗ", "i\u0323", "i\u0328", "r\u0323", "r\u0331", "r\u0327", "ı\u0323"]


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_the_double_grave_on_a_base_with_a_mark_below_is_the_narrow_one(weight, italic):
    path = static_path(weight, italic)
    order = TTFont(path).getGlyphOrder()
    face = hb.Font(hb.Face(path.read_bytes()))
    wide = []
    for base in BELOW:
        buf = hb.Buffer()
        buf.add_str(base + DOUBLE_GRAVE)
        buf.guess_segment_properties()
        hb.shape(face, buf, {})
        if "dblgravecomb.narrow" not in [order[i.codepoint] for i in buf.glyph_infos]:
            wide.append(base)
    assert wide == []


@pytest.mark.parametrize("features", [None, {"ss03": True}], ids=["default", "ss03"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_the_double_grave_on_a_base_with_a_mark_below_overhangs_no_more_than_a_breve(weight, italic, features):
    over = []
    for base in BELOW:
        lo, hi, advance = ink(weight, italic, base + DOUBLE_GRAVE, features)
        blo, bhi, _ = ink(weight, italic, base + "\u0306", features)
        if -lo > max(-blo, 0) or hi - advance > max(bhi - advance, 0):
            over.append((base, round(lo), round(hi), advance, round(blo), round(bhi)))
    assert over == []
