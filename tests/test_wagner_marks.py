"""Tilde, macron and hook-above invariants (Rosalie Wagner's list, uswds/public-sans#158)."""
import pytest
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path


class _Flat(BasePen):
    """Flatten an outline to line segments."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.segments = []

    def _moveTo(self, p):
        self.cur = self.start = p

    def _lineTo(self, p):
        self.segments.append((self.cur, p))
        self.cur = p

    def _curveToOne(self, a, b, c):
        p0, prev = self.cur, self.cur
        for i in range(1, 25):
            t = i / 24
            q = tuple((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * a[k] + 3 * (1 - t) * t * t * b[k] + t ** 3 * c[k]
                      for k in (0, 1))
            self.segments.append((prev, q))
            prev = q
        self.cur = c

    def _qCurveToOne(self, a, c):
        p0, prev = self.cur, self.cur
        for i in range(1, 25):
            t = i / 24
            q = tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * a[k] + t * t * c[k] for k in (0, 1))
            self.segments.append((prev, q))
            prev = q
        self.cur = c

    def _closePath(self):
        if self.cur != self.start:
            self.segments.append((self.cur, self.start))

    _endPath = _closePath


def glyph_for(font, char):
    return font.getBestCmap()[ord(char)]


def bounds(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def wave(font, char):
    """(minimum vertical stroke, wave swing) of a combining tilde, measured on the spacing tilde that reuses its outline."""
    name = glyph_for(font, char)
    gs = font.getGlyphSet()
    pen = _Flat(gs)
    gs[name].draw(pen)
    x0, y0, x1, y1 = bounds(font, name)
    gaps = []
    for i in range(80):
        x = x0 + (0.18 + 0.64 * i / 79) * (x1 - x0) + 0.37
        ys = sorted(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]) for a, b in pen.segments
                    if (a[0] - x) * (b[0] - x) < 0 and a[0] != b[0])
        if len(ys) == 2:
            gaps.append(ys[1] - ys[0])
    stroke = min(gaps)
    return stroke, (y1 - y0) - stroke


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_tilde_wave_is_visible_against_its_stroke(weight, italic):
    """The wave swing is at least 0.55 of the stroke, so a tilde stays distinct from a macron at small sizes."""
    stroke, swing = wave(TTFont(static_path(weight, italic)), "̃")
    assert swing / stroke >= 0.55, f"swing {swing:.0f} vs stroke {stroke:.0f}"


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_black_tilde_and_macron_stay_below_stroke_ceiling(italic):
    """In Black the tilde and macron strokes are at most 201 units (the hyphen is 274)."""
    font = TTFont(static_path("Black", italic))
    stroke, _ = wave(font, "̃")
    x0, y0, x1, y1 = bounds(font, glyph_for(font, "̄"))
    assert stroke <= 201, f"tilde stroke {stroke:.0f}"
    assert y1 - y0 <= 201, f"macron stroke {y1 - y0:.0f}"


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
@pytest.mark.parametrize("breve,circumflex", [("Ẳ", "Ể"), ("ẳ", "ể")], ids=["upper", "lower"])
def test_hook_over_breve_is_not_taller_than_hook_over_circumflex(weight, italic, breve, circumflex):
    """The hook above a breve sits no higher than the same hook above a circumflex (sources: the stack is lowered by the measured difference)."""
    font = TTFont(static_path(weight, italic))
    top_breve = bounds(font, glyph_for(font, breve))[3]
    top_circ = bounds(font, glyph_for(font, circumflex))[3]
    assert top_breve <= top_circ + 2, f"{top_breve:.0f} vs {top_circ:.0f}"


def _top_wave(font, name):
    """(smallest stroke, rise of the upper edge) of the uppermost wave in a mark glyph."""
    gs = font.getGlyphSet()
    pen = _Flat(gs)
    gs[name].draw(pen)
    x0, _, x1, _ = bounds(font, name)
    strokes, upper = [], []
    for i in range(80):
        x = x0 + (0.18 + 0.64 * i / 79) * (x1 - x0) + 0.37
        ys = sorted(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]) for a, b in pen.segments
                    if (a[0] - x) * (b[0] - x) < 0 and a[0] != b[0])
        strokes.append(ys[-1] - ys[-2])
        upper.append(ys[-1])
    return min(strokes), max(upper) - min(upper)


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
@pytest.mark.parametrize("name", ["uni03060303", "uni03020303"])
def test_stacked_tilde_marks_use_the_same_wave_as_the_tilde(weight, italic, name):
    """The tilde inside breve + tilde and circumflex + tilde (`ẵ`, `ẫ`, `ễ`, `ỗ`) is the same wave as `tildecomb`."""
    font = TTFont(static_path(weight, italic))
    stroke, rise = _top_wave(font, name)
    ref_stroke, ref_rise = _top_wave(font, "tildecomb")
    assert abs(stroke - ref_stroke) <= 2, f"stroke {stroke:.0f} vs {ref_stroke:.0f}"
    assert abs(rise - ref_rise) <= 2, f"rise {rise:.0f} vs {ref_rise:.0f}"
