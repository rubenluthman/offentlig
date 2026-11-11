"""The straight wedge on ď ľ ť Ľ keeps clear of a following l, b, h or k, kerning included, in every weight."""
import numpy as np
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
        p0 = np.array(self._cur[-1])
        for t in np.linspace(0, 1, 17)[1:]:
            m = 1 - t
            self._cur.append(tuple(m**3 * p0 + 3 * m * m * t * np.array(a) + 3 * m * t * t * np.array(b) + t**3 * np.array(c)))

    def _qCurveToOne(self, a, b):
        p0 = np.array(self._cur[-1])
        for t in np.linspace(0, 1, 13)[1:]:
            m = 1 - t
            self._cur.append(tuple(m * m * p0 + 2 * m * t * np.array(a) + t * t * np.array(b)))

    def _closePath(self):
        self.contours.append(self._cur)

    _endPath = _closePath


def _segments(contours, dx=0, dy=0):
    out = []
    for contour in contours:
        pts = np.array(contour, float) + [dx, dy]
        out.append(np.stack([pts, np.roll(pts, -1, 0)], 1))
    return np.concatenate(out)


def _distance(a, b):
    """Smallest distance between two sets of segments (their outlines do not cross, or the gap is 0 anyway)."""
    best = np.inf
    for one, other in ((a, b), (b, a)):
        p = one[:, 0][:, None, :]
        start, end = other[None, :, 0], other[None, :, 1]
        ab = end - start
        length = np.where((ab**2).sum(-1) == 0, 1, (ab**2).sum(-1))
        t = np.clip(((p - start) * ab).sum(-1) / length, 0, 1)
        best = min(best, np.linalg.norm(p - (start + ab * t[..., None]), axis=-1).min())
    return best


def _wedge(font, glyph_name):
    """The accent component of a letter with a caron: its outline in the letter's coordinates."""
    comp = font["glyf"][glyph_name].components[1]
    pen = _Flat(font.getGlyphSet())
    font.getGlyphSet()[comp.glyphName].draw(pen)
    return _segments(pen.contours, comp.x, comp.y)


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
            gap = _distance(wedge, _segments(pen.contours, first.x_advance + second.x_offset, second.y_offset))
            if gap < MIN_GAP:
                too_close.append((name, follower, round(gap)))
    assert not too_close, f"wedge closer than {MIN_GAP} units to the next letter: {too_close}"
