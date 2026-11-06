"""Stroke-weight invariants of `percent`, `asciitilde` and `approxequal` (Rosalie Wagner's list, uswds/public-sans#158)."""
import math

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


def segments(font, name):
    gs = font.getGlyphSet()
    pen = _Flat(gs)
    gs[name].draw(pen)
    return pen.segments


def spans_at_y(segs, y):
    xs = sorted(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]) for a, b in segs if (a[1] - y) * (b[1] - y) < 0)
    return list(zip(xs[0::2], xs[1::2]))


def gaps_at_x(segs, x):
    ys = sorted(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]) for a, b in segs
                if (a[0] - x) * (b[0] - x) < 0 and a[0] != b[0])
    return [t - b for b, t in zip(ys[0::2], ys[1::2])]


def min_wave_stroke(font, name):
    """Smallest vertical gap across the middle 70 percent of the glyph, where gap equals perpendicular stroke at the extrema."""
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    x0, _, x1, _ = pen.bounds
    segs = segments(font, name)
    # The 0.37 offset keeps samples off integer vertices, where a crossing would be missed.
    return min(g for i in range(61) for g in gaps_at_x(segs, x0 + (0.15 + 0.7 * i / 60) * (x1 - x0) + 0.37))


def hyphen_thickness(font):
    return gaps_at_x(segments(font, "hyphen"), 400)[0]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_percent_slash_keeps_weight_of_zero_stems(weight, italic):
    """The slash is at least 0.80 of the zero stem thickness (measured perpendicular to the slash axis)."""
    font = TTFont(static_path(weight, italic))
    segs = segments(font, "percent")
    low = [spans_at_y(segs, y)[0] for y in (250, 450)]  # leftmost span is the slash: the zeros start higher and further right
    centres = [(a + b) / 2 for a, b in low]
    theta = math.atan((centres[1] - centres[0]) / 200)
    slash = (sum(b - a for a, b in low) / 2) * math.cos(theta)
    a, b = spans_at_y(segs, 1054)[0]  # left zero, left stem
    stem = b - a
    # The zero stem measured here is the left zero's stem only where the slash does not touch it at y=1054.
    assert slash / stem >= 0.80, f"slash {slash:.0f} vs stem {stem:.0f}"


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
@pytest.mark.parametrize("name", ["asciitilde", "approxequal"])
def test_tilde_waves_keep_hyphen_weight(weight, italic, name):
    """The wave stroke is at least 0.85 of the hyphen thickness at every weight."""
    font = TTFont(static_path(weight, italic))
    ratio = min_wave_stroke(font, name) / hyphen_thickness(font)
    assert ratio >= 0.85, f"{name}: {ratio:.2f}"
