"""Outline distance between shaped glyphs, for tests that measure the gap between a mark and its base."""
import math

import numpy as np
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


class Polyline(BasePen):
    """Flattens an outline into closed polylines, curves cut into steps of about 4 units."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours = []

    def _moveTo(self, p):
        self.contours.append([p])

    def _lineTo(self, p):
        self.contours[-1].append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.contours[-1][-1]
        n = max(4, int(sum(math.dist(a, b) for a, b in ((p0, p1), (p1, p2), (p2, p3))) / 4))
        for i in range(1, n + 1):
            t = i / n
            u = 1 - t
            self.contours[-1].append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                                      u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.contours[-1][-1]
        self._curveToOne((p0[0] + 2 / 3 * (p1[0] - p0[0]), p0[1] + 2 / 3 * (p1[1] - p0[1])),
                         (p2[0] + 2 / 3 * (p1[0] - p2[0]), p2[1] + 2 / 3 * (p1[1] - p2[1])), p2)

    def _closePath(self):
        self.contours[-1].append(self.contours[-1][0])


def _segments(contours):
    return [(c[i], c[i + 1]) for c in contours for i in range(len(c) - 1)]


def _point_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = 0 if dx == dy == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _on_segment(p, a, b):
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _segments_meet(a1, a2, b1, b2):
    """True when two segments cross, touch or share an edge."""
    d1, d2 = _cross(b1, b2, a1), _cross(b1, b2, a2)
    d3, d4 = _cross(a1, a2, b1), _cross(a1, a2, b2)
    if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
        return True
    return (
        (d1 == 0 and _on_segment(a1, b1, b2))
        or (d2 == 0 and _on_segment(a2, b1, b2))
        or (d3 == 0 and _on_segment(b1, a1, a2))
        or (d4 == 0 and _on_segment(b2, a1, a2))
    )


def _inside(p, contours):
    """Even-odd test: is the point inside the ink of the closed polylines?"""
    inside = False
    for c in contours:
        for (x0, y0), (x1, y1) in zip(c, c[1:]):
            if (y0 > p[1]) != (y1 > p[1]) and p[0] < x0 + (p[1] - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
    return inside


def outline_distance(a, b):
    """Smallest distance between two sets of closed polylines (contours of points); 0 when they touch, cross or one lies in the other.

    Contact is found for outlines that cross or share an edge as well as for a point on a segment, so a pair of glyphs whose ink
    meets along a near-vertical edge is not read as clear."""
    sa, sb = _segments(a), _segments(b)
    for s in sa:
        lo_x, hi_x = min(s[0][0], s[1][0]), max(s[0][0], s[1][0])
        lo_y, hi_y = min(s[0][1], s[1][1]), max(s[0][1], s[1][1])
        for t in sb:
            if max(t[0][0], t[1][0]) < lo_x or min(t[0][0], t[1][0]) > hi_x:
                continue
            if max(t[0][1], t[1][1]) < lo_y or min(t[0][1], t[1][1]) > hi_y:
                continue
            if _segments_meet(s[0], s[1], t[0], t[1]):
                return 0.0
    if any(_inside(c[0], b) for c in a if c) or any(_inside(c[0], a) for c in b if c):
        return 0.0
    best = math.inf
    for points, segments in ((a, sb), (b, sa)):
        for c in points:
            for p in c:
                for s in segments:
                    # a segment farther than `best` from the point in either axis cannot hold a nearer point
                    if (
                        min(s[0][0], s[1][0]) - best < p[0] < max(s[0][0], s[1][0]) + best
                        and min(s[0][1], s[1][1]) - best < p[1] < max(s[0][1], s[1][1]) + best
                    ):
                        best = min(best, _point_segment(p, *s))
    return best


def _np_segments(contours):
    return (np.concatenate([c[:-1] for c in contours]), np.concatenate([c[1:] for c in contours]))


def _np_inside(points, contours):
    """Even-odd test for each point (k, 2) against closed contours; the numpy form of `_inside`."""
    if len(points) == 0:
        return np.zeros(0, bool)
    a, b = _np_segments(contours)
    px, py = points[:, 0:1], points[:, 1:2]
    x0, y0, x1, y1 = a[:, 0], a[:, 1], b[:, 0], b[:, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        crossing = ((y0 > py) != (y1 > py)) & (px < x0 + (py - y0) * (x1 - x0) / (y1 - y0))
    return crossing.sum(axis=1) % 2 == 1


def _np_box_filter(a, b, lo, hi):
    keep = (np.maximum(a[:, 0], b[:, 0]) >= lo[0]) & (np.minimum(a[:, 0], b[:, 0]) <= hi[0])
    keep &= (np.maximum(a[:, 1], b[:, 1]) >= lo[1]) & (np.minimum(a[:, 1], b[:, 1]) <= hi[1])
    return a[keep], b[keep]


def _np_cross(o, a, b):
    return (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])


def _np_on(p, s, e):
    return (
        (np.minimum(s[..., 0], e[..., 0]) <= p[..., 0])
        & (p[..., 0] <= np.maximum(s[..., 0], e[..., 0]))
        & (np.minimum(s[..., 1], e[..., 1]) <= p[..., 1])
        & (p[..., 1] <= np.maximum(s[..., 1], e[..., 1]))
    )


def _np_meet_any(a1, a2, b1, b2):
    """Any segment of set A crosses, touches or shares an edge with any of set B; the numpy form of `_segments_meet`."""
    if len(a1) == 0 or len(b1) == 0:
        return False
    A1, A2, B1, B2 = a1[:, None, :], a2[:, None, :], b1[None, :, :], b2[None, :, :]
    box = (
        (np.maximum(B1[..., 0], B2[..., 0]) >= np.minimum(A1[..., 0], A2[..., 0]))
        & (np.minimum(B1[..., 0], B2[..., 0]) <= np.maximum(A1[..., 0], A2[..., 0]))
        & (np.maximum(B1[..., 1], B2[..., 1]) >= np.minimum(A1[..., 1], A2[..., 1]))
        & (np.minimum(B1[..., 1], B2[..., 1]) <= np.maximum(A1[..., 1], A2[..., 1]))
    )
    if not box.any():
        return False
    d1, d2 = _np_cross(B1, B2, A1), _np_cross(B1, B2, A2)
    d3, d4 = _np_cross(A1, A2, B1), _np_cross(A1, A2, B2)
    proper = (((d1 > 0) & (d2 < 0)) | ((d1 < 0) & (d2 > 0))) & (((d3 > 0) & (d4 < 0)) | ((d3 < 0) & (d4 > 0)))
    touch = (
        ((d1 == 0) & _np_on(A1, B1, B2))
        | ((d2 == 0) & _np_on(A2, B1, B2))
        | ((d3 == 0) & _np_on(B1, A1, A2))
        | ((d4 == 0) & _np_on(B2, A1, A2))
    )
    return bool((box & (proper | touch)).any())


def _np_point_segment_min(points, a, b):
    if len(points) == 0 or len(a) == 0:
        return math.inf
    d = b - a
    dd = (d * d).sum(axis=1)
    safe = np.where(dd == 0, 1, dd)
    best = math.inf
    for i in range(0, len(points), 512):
        p = points[i : i + 512, None, :]
        t = np.clip(np.where(dd == 0, 0.0, ((p - a) * d).sum(axis=2) / safe), 0, 1)
        q = a + t[..., None] * d
        best = min(best, float(np.sqrt(((p - q) ** 2).sum(axis=2)).min()))
    return best


def fast_distance(a, b, cap=math.inf):
    """`outline_distance` in numpy, with contours given as lists of points or (n, 2) arrays: the same contact rules and the same
    number, 0 when the outlines touch, cross or one lies in the other. Pieces farther than `cap` from the other glyph's box are
    skipped, so the result is exact below `cap` and `cap` or more above it."""
    a = [np.asarray(c, dtype=float) for c in a if len(c)]
    b = [np.asarray(c, dtype=float) for c in b if len(c)]
    if not a or not b:
        return math.inf
    all_a, all_b = np.concatenate(a), np.concatenate(b)
    lo_a, hi_a, lo_b, hi_b = all_a.min(axis=0), all_a.max(axis=0), all_b.min(axis=0), all_b.max(axis=0)
    seg_a, seg_b = _np_segments(a), _np_segments(b)
    lo, hi = np.maximum(lo_a, lo_b), np.minimum(hi_a, hi_b)
    if (lo <= hi).all():  # contact needs overlapping boxes
        if _np_meet_any(*_np_box_filter(*seg_a, lo, hi), *_np_box_filter(*seg_b, lo, hi)):
            return 0.0
        if _np_inside(np.array([c[0] for c in a]), b).any() or _np_inside(np.array([c[0] for c in b]), a).any():
            return 0.0
    near_a = all_a[(all_a >= lo_b - cap).all(axis=1) & (all_a <= hi_b + cap).all(axis=1)]
    near_b = all_b[(all_b >= lo_a - cap).all(axis=1) & (all_b <= hi_a + cap).all(axis=1)]
    d = min(
        _np_point_segment_min(near_a, *_np_box_filter(*seg_b, lo_a - cap, hi_a + cap)),
        _np_point_segment_min(near_b, *_np_box_filter(*seg_a, lo_b - cap, hi_b + cap)),
    )
    return min(d, cap)


def placed_contours(path, text, features=None):
    """Shape `text`; return one list of contours per glyph, moved to where it is drawn."""
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    out, x = [], 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        poly = Polyline(gs)
        gs[order[info.codepoint]].draw(TransformPen(poly, (1, 0, 0, 1, x + pos.x_offset, pos.y_offset)))
        out.append(poly.contours)
        x += pos.x_advance
    return out


def mark_clearance(path, text):
    """Distance from the last glyph (the mark) to all glyphs before it."""
    glyphs = placed_contours(path, text)
    base = [c for g in glyphs[:-1] for c in g]
    return outline_distance(base, glyphs[-1])
