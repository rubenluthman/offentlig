"""Anchors of combining marks and of the letters that take them sit where the ink is.

Units are font units (2000 per em). In the italic masters "on the slant line" means along the 8 degree lean.
"""
import math
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

SOURCES = Path(__file__).resolve().parent.parent / "sources"
MASTERS = ["Thin", "Regular", "Black", "ThinItalic", "RegularItalic", "BlackItalic"]
TAN8 = math.tan(math.radians(8))
GAP_UNDER_INK_TOP = 31.0  # `top` of a mark sits this far under the mark's own ink top


@pytest.fixture(scope="module")
def fonts():
    return {m: ufoLib2.Font.open(SOURCES / f"OffentligSans-{m}.ufo") for m in MASTERS}


def anchors(glyph):
    return {a.name: (a.x, a.y) for a in glyph.anchors}


def bounds(font, name):
    pen = BoundsPen(font)
    font[name].draw(pen)
    return pen.bounds


def slant_of(master):
    return TAN8 if master.endswith("Italic") else 0.0


@pytest.mark.parametrize("master", MASTERS)
def test_ring_below_is_anchored_under_the_ring_centre(fonts, master):
    font = fonts[master]
    x0, y0, x1, y1 = bounds(font, "ringbelowcomb")
    bx, by = anchors(font["ringbelowcomb"])["_bottom"]
    assert (x0 + x1) / 2 - (bx + (y0 + y1) / 2 * slant_of(master)) == pytest.approx(0, abs=1.0)


@pytest.mark.parametrize("master", MASTERS)
def test_double_macron_below_starts_on_the_slant_line_through_its_anchor(fonts, master):
    font = fonts[master]
    x0, y0, x1, y1 = bounds(font, "dblmacronbelowcomb")
    bx, _ = anchors(font["dblmacronbelowcomb"])["_bottom"]
    assert x0 - (bx + (y0 + y1) / 2 * slant_of(master)) == pytest.approx(0, abs=1.0)


@pytest.mark.parametrize("master", MASTERS)
def test_vertical_line_above_is_centred_on_the_slant_line_through_its_anchor(fonts, master):
    font = fonts[master]
    x0, y0, x1, y1 = bounds(font, "verticallineabovecomb")
    a = anchors(font["verticallineabovecomb"])
    slant = slant_of(master)
    assert (x0 + x1) / 2 - (a["_top"][0] + ((y0 + y1) / 2 - a["_top"][1]) * slant) == pytest.approx(0, abs=1.0)
    assert a["top"][0] - (a["_top"][0] + (a["top"][1] - a["_top"][1]) * slant) == pytest.approx(0, abs=0.5)


@pytest.mark.parametrize("name", ["ringcomb", "macroncomb", "_ringacute"])
@pytest.mark.parametrize("master", MASTERS)
def test_top_anchor_of_a_mark_is_31_under_its_ink_top(fonts, master, name):
    """A mark stacked on the mark keeps the same gap at every weight."""
    font = fonts[master]
    a = anchors(font[name])
    assert a["top"][1] == pytest.approx(bounds(font, name)[3] - GAP_UNDER_INK_TOP, abs=0.5)
    assert a["top"][0] - (a["_top"][0] + (a["top"][1] - a["_top"][1]) * slant_of(master)) == pytest.approx(0, abs=0.5)


@pytest.mark.parametrize("master", MASTERS)
def test_tcaron_top_clears_the_side_caron(fonts, master):
    """The caron stands beside the stem, so `top` is at the ink top, above the caron."""
    font = fonts[master]
    assert anchors(font["tcaron"])["top"][1] == pytest.approx(bounds(font, "tcaron")[3], abs=0.5)


@pytest.mark.parametrize("master", MASTERS)
def test_ogonek_and_horn_exist_on_c_and_s(fonts, master):
    """U+0328 and U+031B on C c S s (DIN 91379) attach at the lower right and the upper right of the letter."""
    font = fonts[master]
    for name in "CcSs":
        a = anchors(font[name])
        x0, y0, x1, y1 = bounds(font, name)
        assert {"ogonek", "horn"} <= set(a), name
        ox, oy = a["ogonek"]
        assert -30 <= oy <= 60 and x0 + 0.5 * (x1 - x0) < ox < x1, (name, a["ogonek"])
        hx, hy = a["horn"]
        assert hy > y0 + 0.55 * (y1 - y0) and hx > x0 + 0.6 * (x1 - x0), (name, a["horn"])


def _encoded(font):
    return {g.name for g in font if g.unicodes}


@pytest.mark.parametrize("style", ["Thin", "Regular", "Black"])
def test_every_encoded_glyph_has_the_same_anchors_upright_and_italic(fonts, style):
    upright, italic = fonts[style], fonts[style + "Italic"]
    bad = []
    for name in sorted(_encoded(upright) & _encoded(italic)):
        a = {k for k in anchors(upright[name]) if not k.startswith("_")}
        b = {k for k in anchors(italic[name]) if not k.startswith("_")}
        if a != b:
            bad.append((name, sorted(a - b), sorted(b - a)))
    assert not bad, f"anchors only upright / only italic: {bad}"


@pytest.mark.parametrize("master", MASTERS)
def test_iogonek_top_clears_the_dot(fonts, master):
    """Lithuanian į + acute or tilde: `top` is no lower than 31 under the dot top, and on the slant line in the italic."""
    font = fonts[master]
    for suffix in ("", ".ss03"):
        a = anchors(font["iogonek" + suffix])
        assert "top" in a
        dot_top = max(bounds(font, "iogonek" + suffix)[3], 0)
        assert a["top"][1] >= dot_top - GAP_UNDER_INK_TOP - 0.5
        assert a["top"][1] <= dot_top - GAP_UNDER_INK_TOP + 25


COMMAS = {"commaaccentcomb": max, "commaturnedabovecomb": min}  # which y edge faces the letter


def _area(font, name):
    pen = AreaPen(font)
    font[name].draw(pen)
    return abs(pen.value)


@pytest.mark.parametrize("master", MASTERS)
def test_round_comma_heads_keep_the_inner_edge_and_the_weight(fonts, master):
    """The `.ss03` head ends where the square head ends (nearest the letter) and carries at least 85 % of its ink (77 % in Thin)."""
    font = fonts[master]
    for name, edge in COMMAS.items():
        plain, rounded = bounds(font, name), bounds(font, name + ".ss03")
        index = 3 if edge is max else 1
        assert rounded[index] == pytest.approx(plain[index], abs=0.5), name
        assert _area(font, name + ".ss03") / _area(font, name) >= (0.77 if master.startswith("Thin") else 0.85), name


@pytest.mark.parametrize("style", ["Thin", "Regular", "Black"])
def test_comma_above_right_follows_the_slant_in_the_italic(fonts, style):
    """The comma's ink sits at the upright offset from `_top`, plus the lean over the height of the comma."""
    upright, italic = fonts[style], fonts[style + "Italic"]
    name = "commaaboverightcomb"
    ux0, _, ux1, _ = bounds(upright, name)
    ix0, iy0, ix1, iy1 = bounds(italic, name)
    up_offset = (ux0 + ux1) / 2 - anchors(upright[name])["_top"][0]
    ax, ay = anchors(italic[name])["_top"]
    want = up_offset + ((iy0 + iy1) / 2 - ay) * TAN8
    assert (ix0 + ix1) / 2 - ax == pytest.approx(want, abs=3.0)


@pytest.mark.parametrize("master", ["Thin", "Regular", "Black"])
def test_uhornacute_has_no_stray_mark_anchor(fonts, master):
    assert not [k for k in anchors(fonts[master]["uhornacute"]) if k.startswith("_")]
