"""The diaeresis dots sit at one height with and without `ss03`, and the anchors that stack marks follow them."""
import math
from pathlib import Path

import pytest
import ufoLib2

SOURCES = Path(__file__).resolve().parent.parent / "sources"
MASTERS = ["Thin", "Regular", "Black", "ThinItalic", "RegularItalic", "BlackItalic"]
TAN8 = math.tan(math.radians(8))

# Gap between the top of the dots and the `top` anchor of the mark: negative because the anchor sits inside the dots' height.
ANCHOR_BELOW_DOTS = -31.0

STACKED = """
    Adieresismacron Idieresisacute Odieresismacron Udieresisacute Udieresiscaron Udieresisgrave
    Udieresismacron adieresismacron idotlessdieresisacute odieresismacron udieresisacute udieresiscaron
    udieresisgrave udieresismacron
""".split()


@pytest.fixture(scope="module")
def fonts():
    return {m: ufoLib2.Font.open(SOURCES / f"OffentligSans-{m}.ufo") for m in MASTERS}


def anchors(glyph):
    return {a.name: (a.x, a.y) for a in glyph.anchors}


def dot_extent(glyph):
    """(bottom, top) of the two dots."""
    boxes = [c.getBounds() for c in glyph.contours]
    assert len(boxes) == 2
    return min(b[1] for b in boxes), max(b[3] for b in boxes)


@pytest.mark.parametrize("master", MASTERS)
def test_round_dots_sit_on_the_square_dots(fonts, master):
    """Default and `ss03` dots share the bottom edge, and their centres differ by under 15 % of the dot height."""
    font = fonts[master]
    bottom, top = dot_extent(font["dieresiscomb"])
    round_bottom, round_top = dot_extent(font["dieresiscomb.ss03"])
    assert round_bottom == pytest.approx(bottom, abs=0.5)
    centre, round_centre = (bottom + top) / 2, (round_bottom + round_top) / 2
    assert abs(round_centre - centre) < 0.15 * (top - bottom)


@pytest.mark.parametrize("master", MASTERS)
def test_top_anchor_keeps_its_distance_above_the_dots(fonts, master):
    """`top` is 31 units under the dot top, so a mark stacked above the dots keeps the same gap at every weight."""
    font = fonts[master]
    slant = TAN8 if master.endswith("Italic") else 0.0
    for name in ("dieresiscomb", "dieresiscomb.ss03"):
        glyph = font[name]
        _, top = dot_extent(glyph)
        ax, ay = anchors(glyph)["top"]
        if name == "dieresiscomb":
            assert ay - top == pytest.approx(ANCHOR_BELOW_DOTS, abs=0.01), name
        else:
            # the anchor follows the round dots when they rise above the square ones, and never sits lower than the plain one
            assert ay - top >= ANCHOR_BELOW_DOTS - 0.01, name
            assert ay >= anchors(font["dieresiscomb"])["top"][1] - 0.01
        if slant:
            # the anchor stays on the slanted line through `_top`
            px, py = anchors(font["dieresiscomb"])["top"]
            _x, _y = anchors(font["dieresiscomb"])["_top"]
            assert px - _x == pytest.approx((py - _y) * slant, abs=0.05)


@pytest.mark.parametrize("master", MASTERS)
def test_precomposed_stacks_follow_the_top_anchor(fonts, master):
    """The mark above the dots in ǖ ǘ ǚ ǜ ȫ Ǟ and the capitals sits where the `top` anchor puts it."""
    font = fonts[master]
    slant = TAN8 if master.endswith("Italic") else 0.0
    top_x, top_y = anchors(font["dieresiscomb"])["top"]
    for name in STACKED:
        comps = font[name].components
        index = next(i for i, c in enumerate(comps) if c.baseGlyph == "dieresiscomb")
        dots, upper = comps[index], comps[index + 1]
        mark_x, mark_y = anchors(font[upper.baseGlyph])["_top"]
        want_y = dots.transformation[5] + top_y - mark_y
        want_x = dots.transformation[4] + top_x - mark_x
        assert upper.transformation[5] == pytest.approx(want_y, abs=0.05), name
        if slant:
            assert upper.transformation[4] == pytest.approx(want_x, abs=0.05), name


@pytest.mark.parametrize("master", ["ThinItalic", "RegularItalic", "BlackItalic"])
def test_italic_dots_sit_on_the_slanted_line(fonts, master):
    """The middle of the two dots lies on the line through `_top` that leans 8 degrees (within 8 units)."""
    font = fonts[master]
    for name in ("dieresiscomb", "dieresiscomb.ss03"):
        glyph = font[name]
        boxes = [c.getBounds() for c in glyph.contours]
        mid_x = sum(b[0] + b[2] for b in boxes) / 4
        mid_y = sum(b[1] + b[3] for b in boxes) / 4
        _x, _y = anchors(glyph)["_top"]
        assert mid_x - (_x + (mid_y - _y) * TAN8) == pytest.approx(0, abs=8), name
