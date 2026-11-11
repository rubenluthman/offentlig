"""Italic accents sit on their base anchors: a mark's offset puts its `_name` anchor on the base's `name` anchor."""
import math
from pathlib import Path

import pytest
import ufoLib2

SOURCES = Path(__file__).resolve().parent.parent / "sources"
TOLERANCE = 10  # font units, 0.5% of the em


def _anchors(glyph):
    return {a.name: (a.x, a.y) for a in glyph.anchors}


def _is_combining_mark(font, name):
    # the `.ss03` form of a mark has no code point of its own
    return any(0x0300 <= u <= 0x036F for u in font[name.removesuffix(".ss03")].unicodes)


def _centre(font, comp):
    xmin, ymin, xmax, ymax = font[comp.baseGlyph].getBounds(font)
    return (xmin + xmax) / 2 + comp.transformation[4], (ymin + ymax) / 2 + comp.transformation[5]


def _off_slant(font, glyph):
    """Check a mark built only from other marks (`candrabinducomb` is a breve with a dot in it).

    The upper part has no anchor on the lower part to attach to; it is centred on it. In an italic, centred means
    on the line through the lower part's centre that leans at the italic angle, so the distance to that line is the
    error, not the horizontal offset.
    """
    slant = math.tan(math.radians(-font.info.italicAngle))
    base_x, base_y = _centre(font, glyph.components[0])
    bad = []
    for comp in glyph.components[1:]:
        x, y = _centre(font, comp)
        dx, dy = x - base_x, y - base_y
        across = (dx - dy * slant) / math.hypot(1, slant)
        if abs(across) > TOLERANCE:
            bad.append((glyph.name, comp.baseGlyph, round(across), round(dy)))
    return bad


def _misplaced(font):
    """Match each mark to the nearest preceding component that carries the anchor name it attaches to.

    `Abrevedotbelow` is A, `dotbelowcomb`, `brevecomb`: the breve's `_top` belongs to the A's `top`, not to the
    `dotbelowcomb` that happens to precede it.
    """
    bad = []
    for glyph in font:
        if len(glyph.components) < 2 or glyph.contours:
            continue
        if all(_is_combining_mark(font, c.baseGlyph) for c in glyph.components):
            bad.extend(_off_slant(font, glyph))
            continue
        for index, comp in enumerate(glyph.components[1:], start=1):
            mark_anchors = _anchors(font[comp.baseGlyph])
            attach = [k for k in mark_anchors if k.startswith("_")]
            if not attach:
                continue
            name = attach[0][1:]
            target = next(
                (c for c in reversed(glyph.components[:index]) if name in _anchors(font[c.baseGlyph])),
                None,
            )
            if target is None:
                continue
            bx, by = _anchors(font[target.baseGlyph])[name]
            mx, my = mark_anchors[attach[0]]
            dx = comp.transformation[4] - (bx + target.transformation[4] - mx)
            dy = comp.transformation[5] - (by + target.transformation[5] - my)
            if abs(dx) > TOLERANCE or abs(dy) > TOLERANCE:
                bad.append((glyph.name, comp.baseGlyph, round(dx), round(dy)))
    return bad


@pytest.mark.parametrize("ufo", ["OffentligSans-ThinItalic.ufo", "OffentligSans-RegularItalic.ufo", "OffentligSans-BlackItalic.ufo"])
def test_italic_marks_sit_on_anchors(ufo):
    font = ufoLib2.Font.open(SOURCES / ufo)
    bad = _misplaced(font)
    assert not bad, f"{ufo}: marks more than {TOLERANCE} units from their anchor (glyph, mark, dx, dy): {bad}"
