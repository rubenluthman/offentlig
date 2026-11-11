"""The straight wedge on ď ľ ť Ľ keeps clear of a following l, b, h or k, kerning included, in every weight."""
import math

import pytest
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from conftest import STATICS, STATIC_IDS, static_path

# Smallest measured gap is 78 units (ľ before l in Black, 80 for ď). In Public Sans the same pairs overlapped by
# 50 (ľ) and 144 (ď). 60 units is 3% of the em: below every gap measured here, so only a real loss of room fails.
MIN_GAP = 60
WEDGE_LETTERS = ["dcaron", "lcaron", "tcaron", "Lcaron"]
FOLLOWERS = "lbhk"


class _Flat(BasePen):
    """Collect a glyph's contours as polylines, with curves sampled finely."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours = []
        self._cur = None

    def _moveTo(self, pt):
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, a, b, c):
        p0 = self._cur[-1]
        for i in range(1, 17):
            t = i / 16
            m = 1 - t
            self._cur.append(tuple(m**3 * p0[k] + 3 * m * m * t * a[k] + 3 * m * t * t * b[k] + t**3 * c[k] for k in (0, 1)))

    def _qCurveToOne(self, a, b):
        p0 = self._cur[-1]
        for i in range(1, 13):
            t = i / 12
            m = 1 - t
            self._cur.append(tuple(m * m * p0[k] + 2 * m * t * a[k] + t * t * b[k] for k in (0, 1)))

    def _closePath(self):
        self.contours.append(self._cur)

    _endPath = _closePath


def _points(contours, dx=0, dy=0):
    return [[(x + dx, y + dy) for x, y in contour] for contour in contours]


def _point_to_polyline(p, contour):
    best = math.inf
    for (ax, ay), (bx, by) in zip(contour, contour[1:] + contour[:1]):
        abx, aby = bx - ax, by - ay
        length = abx * abx + aby * aby
        t = 0 if length == 0 else max(0, min(1, ((p[0] - ax) * abx + (p[1] - ay) * aby) / length))
        best = min(best, math.hypot(p[0] - (ax + abx * t), p[1] - (ay + aby * t)))
    return best


def _distance(a, b):
    """Smallest distance between two outlines (they do not cross, or the gap is 0 anyway)."""
    return min(
        min(_point_to_polyline(p, other) for contour in one for p in contour for other in two)
        for one, two in ((a, b), (b, a))
    )


def _wedge(font, glyph_name):
    """The accent component of a letter with a caron: its outline in the letter's coordinates."""
    comp = font["glyf"][glyph_name].components[1]
    pen = _Flat(font.getGlyphSet())
    font.getGlyphSet()[comp.glyphName].draw(pen)
    return _points(pen.contours, comp.x, comp.y)


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_wedge_clears_following_ascender(weight, italic):
    path = static_path(weight, italic)
    font = TTFont(path)
    glyph_set = font.getGlyphSet()
    cmap = {name: code for code, name in font.getBestCmap().items()}
    hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    too_close = []
    for name in WEDGE_LETTERS:
        wedge = _wedge(font, name)
        for follower in FOLLOWERS:
            buf = hb.Buffer()
            buf.add_str(chr(cmap[name]) + follower)
            buf.guess_segment_properties()
            hb.shape(hb_font, buf)
            first, second = buf.glyph_positions
            pen = _Flat(glyph_set)
            glyph_set[font.getGlyphName(buf.glyph_infos[1].codepoint)].draw(pen)
            gap = _distance(wedge, _points(pen.contours, first.x_advance + second.x_offset, second.y_offset))
            if gap < MIN_GAP:
                too_close.append((name, follower, round(gap)))
    assert not too_close, f"wedge closer than {MIN_GAP} units to the next letter: {too_close}"
