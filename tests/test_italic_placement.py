"""Italic glyphs sit on the slant line: their bearings, measured along the 8 degree slant, equal the upright glyph's.

The italic masters are sheared about half the x-height, so a point (x, y) is brought back to the upright frame with
x' = x - (y - xHeight / 2) * tan(8 degrees). A glyph that was sheared about the baseline instead lands about 73 units
(2000 per em) to the right of its upright form; that shows up here as a larger left bearing and a smaller right bearing.
"""
import math
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

SOURCES = Path(__file__).resolve().parent.parent / "sources"
WEIGHTS = ("Thin", "Regular", "Black")
TAN = math.tan(math.radians(8))
TOLERANCE = 5  # font units (2000 per em)
# G.cv03, J.cv01 and a.cv04 are redrawn for the italic and differ from the upright by up to 9 units; the fault this test
# guards against is 73 units.
REDRAWN = {"G.cv03", "J.cv01", "a.cv04"}
REDRAWN_TOLERANCE = 10

# ʹ ʺ ˈ ˌ ʾ ʿ
MODIFIER_LETTERS = ["primemod", "dblprimemod", "verticallinemod", "verticallinelowmod", "ringhalfright", "ringhalfleft"]
# ʰ ʳ ˢ ᵈ ᵗ ⁿ and the primes ′ ″ ‴
SMALL_LETTERS = ["hmod", "rmod", "smod", "dmod", "tmod", "nsuperior", "minute", "second", "tripleprime"]
# ʒ ǯ (ǯ is ezh with a caron above), ẞ
OTHERS = ["ezh", "ezhcaron", "Germandbls"]


def _fonts(weight):
    return ufoLib2.Font.open(SOURCES / f"OffentligSans-{weight}.ufo"), ufoLib2.Font.open(SOURCES / f"OffentligSans-{weight}Italic.ufo")


def _bearings(font, name, slanted):
    glyph = font[name]
    bounds = BoundsPen(font)
    shift = font.info.xHeight / 2 * TAN if slanted else 0
    glyph.draw(TransformPen(bounds, (1, 0, -TAN if slanted else 0, 1, shift, 0)))
    xmin, _, xmax, _ = bounds.bounds
    return xmin, glyph.width - xmax


def _names(italic):
    """Italic `.cvNN` glyphs that are drawn outlines (accented forms carry marks that lean on purpose), then the fixed lists."""
    cv = [g.name for g in italic if ".cv" in g.name and g.contours and not g.components]
    return cv + MODIFIER_LETTERS + SMALL_LETTERS + OTHERS


@pytest.mark.parametrize("weight", WEIGHTS)
def test_italic_bearings_follow_the_upright_glyph(weight):
    upright, italic = _fonts(weight)
    names = [n for n in _names(italic) if n in upright]
    assert {"I.cv05", "one.cv06", "one.cv06.osf", "ezh", "ezhcaron", "Germandbls", "primemod", "dmod", "tmod", "smod"} <= set(names)
    bad = []
    for name in names:
        (ul, ur), (il, ir) = _bearings(upright, name, False), _bearings(italic, name, True)
        limit = REDRAWN_TOLERANCE if name in REDRAWN else TOLERANCE
        if abs(il - ul) > limit or abs(ir - ur) > limit:
            bad.append((name, round(il - ul, 1), round(ir - ur, 1)))
    assert not bad, f"{weight}Italic: left and right bearing off the upright glyph's (glyph, left, right): {bad}"


@pytest.mark.parametrize("weight", WEIGHTS)
def test_italic_cv05_composites_keep_the_base_bearings(weight):
    """Every glyph built on `I.cv05` still starts where `I.cv05` does, so a mark never drags the bearing away from the slant."""
    upright, italic = _fonts(weight)
    for name in (g.name for g in italic if g.components and g.components[0].baseGlyph == "I.cv05" and not g.name.startswith("IJ")):
        assert italic[name].width == pytest.approx(italic["I.cv05"].width, abs=0.5), name


@pytest.mark.parametrize("weight", WEIGHTS)
def test_superior_and_subscript_nine_have_the_width_of_their_figure(weight):
    """Italic superior and subscript figures are as wide as their numerator and denominator figures (within 6 units: the other figures differ by up to 5)."""
    _, italic = _fonts(weight)
    bad = []
    for figure in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"):
        for small, form in ((f"{figure}superior", f"{figure}.numr"), (f"{figure}.subs", f"{figure}.dnom")):
            if small in italic and form in italic and abs(italic[small].width - italic[form].width) > 6:
                bad.append((small, italic[small].width, italic[form].width))
    assert "ninesuperior" in italic
    assert not bad, f"{weight}Italic: (glyph, width, width of its figure): {bad}"
