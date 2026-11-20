"""The ring of the capitals `Å Ů`: top limit, clearance from the line above, and a ring that stays round and open."""
import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import WEIGHTS, static_path
from test_diacritics import contour_bounds

CAP_HEIGHT = 1446  # apex of `A`; ring contours lie above it
CLEARANCE = 30  # least distance from the ring top to the descenders of the line above, at the default line spacing
DESCENDERS = "gjpqy"
CAPITAL_RINGS = ["Aring", "Uring"]


def ring_contours(font, name):
    """Outer and inner contour bounds of the ring on a precomposed capital."""
    rings = [b for b in contour_bounds(font, name) if b[1] > CAP_HEIGHT]
    assert len(rings) == 2, f"{name} has {len(rings)} contours above the capitals"
    return sorted(rings, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))


def descender_reach(font):
    """Lowest ink of the descenders on the line above, in the em of the glyph below, at the default line spacing (hhea)."""
    hhea = font["hhea"]
    line = hhea.ascent - hhea.descent + hhea.lineGap
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    low = 0
    for ch in DESCENDERS:
        pen = BoundsPen(glyphs)
        glyphs[cmap[ord(ch)]].draw(pen)
        low = min(low, pen.bounds[1])
    return line + low


@pytest.mark.parametrize("name", CAPITAL_RINGS)
def test_capital_ring_clears_the_descenders_above(static_ttf, name):
    """At the default line spacing the ring of `Å Ů` ends at least 30 units below the lowest descender of the line above."""
    top = max(b[3] for b in contour_bounds(static_ttf, name))
    assert top <= descender_reach(static_ttf) - CLEARANCE


def test_ring_with_acute_stays_above_the_descenders(static_ttf):
    """`Ǻ` (its ring and acute are unchanged) ends below the lowest descender of the line above; Black Italic is 3 units under it."""
    top = max(b[3] for b in contour_bounds(static_ttf, "Aringacute"))
    assert top <= descender_reach(static_ttf)


@pytest.mark.parametrize("name", CAPITAL_RINGS)
def test_capital_ring_top_limit(static_ttf, name):
    """The ring of `Å Ů` stays at or below 1990 units at every weight (0.6.0 reached 2053 in Black, 45 units into the descenders above)."""
    top = max(b[3] for b in contour_bounds(static_ttf, name))
    assert top <= 1990


@pytest.mark.parametrize("name", CAPITAL_RINGS)
def test_capital_ring_leaves_the_apex_free(static_ttf, name):
    """The bottom of the ring is at least 25 units above the capital, so the ring and the letter do not touch (28 at Black, where the ring floors of D5 leave no more room)."""
    inner, outer = ring_contours(static_ttf, name)
    assert outer[1] - CAP_HEIGHT >= 25


@pytest.mark.parametrize("name", CAPITAL_RINGS)
def test_capital_ring_is_round(static_ttf, name):
    """Outer ring width to height stays between 0.93 and 1.03 at every weight, upright and italic."""
    _, outer = ring_contours(static_ttf, name)
    assert 0.93 <= (outer[2] - outer[0]) / (outer[3] - outer[1]) <= 1.03


@pytest.mark.parametrize("name", CAPITAL_RINGS)
def test_capital_ring_hole_stays_open(static_ttf, name):
    """The hole is at least as wide as the ring stroke, and 1.2 times as wide at Black."""
    inner, outer = ring_contours(static_ttf, name)
    hole = inner[2] - inner[0]
    stroke = ((outer[2] - outer[0]) - hole) / 2
    black = static_ttf["OS/2"].usWeightClass >= 900
    assert hole >= (1.2 if black else 1.0) * stroke


@pytest.mark.parametrize("weight", WEIGHTS)
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_capital_ring_stroke_keeps_pace_with_the_o(weight, italic):
    """The ring stroke of `Å Ů` is at least 40 % of the `o` stroke at every weight, like the ring of `å`."""
    font = TTFont(static_path(weight, italic))
    for name in CAPITAL_RINGS:
        inner, outer = ring_contours(font, name)
        stroke = ((outer[2] - outer[0]) - (inner[2] - inner[0])) / 2
        o_in, o_out = sorted(contour_bounds(font, "o"), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        o_stroke = ((o_out[2] - o_out[0]) - (o_in[2] - o_in[0])) / 2
        assert stroke / o_stroke >= 0.40
