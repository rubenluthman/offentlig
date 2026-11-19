"""Whole-font diagonal outline-distance check (K8).

Row-gap tests (4-unit horizontal bands) miss diagonal near-touches where one glyph's overhang sits just above or below
the neighbour's stroke. This test checks every encoded pair across all 18 statics against a 15-unit diagonal floor,
using a vectorized bounding-box pre-filter so only pairs that could possibly be closer than 15 units invoke
`outline_distance`.
"""
import unicodedata
from functools import lru_cache

import numpy as np
import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import static_path
from ink import outline_distance
from pairs import PairTable
from test_accent_pairs import cmap_characters
from test_spacing import ALL_FONTS, ALL_IDS, shaper

DIAGONAL_FLOOR = 15.0
LEFT_OUT = set("⁄")
# Narrowed E2 floor: only ExtraBold-italic and Black-italic ï/ḯ/ị̈/ɨ̈ next to tall letters H l i b k h d.
E2_NARROW_LEFT = set("ïḯ")
E2_NARROW_RIGHT = set("Hlibkhd")


def _is_e2_exempt(weight, italic, a, b):
    if not (italic and weight in ("ExtraBold", "Black")):
        return False
    return (a in E2_NARROW_LEFT and b in E2_NARROW_RIGHT) or (b in E2_NARROW_LEFT and a in E2_NARROW_RIGHT)


@lru_cache(maxsize=2)
def _glyph_geometry(path):
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    upm = tt["head"].unitsPerEm
    scale = 2000.0 / upm
    order = tt.getGlyphOrder()
    bounds = np.full((len(order), 4), np.nan)
    contours_cache = {}
    for gid, name in enumerate(order):
        bp = BoundsPen(gs)
        gs[name].draw(bp)
        if bp.bounds is not None:
            bounds[gid] = [v * scale for v in bp.bounds]
    return bounds, scale


@lru_cache(maxsize=2)
def _contour_cache(path):
    from fontTools.pens.basePen import BasePen

    class _SegPen(BasePen):
        def __init__(self, gs, scale):
            super().__init__(gs)
            self.scale = scale
            self.contours = []
            self._cur = []
            self._pt = (0.0, 0.0)

        def _moveTo(self, p0):
            if self._cur:
                self.contours.append(self._cur)
            self._cur = [(p0[0] * self.scale, p0[1] * self.scale)]
            self._pt = p0

        def _lineTo(self, p1):
            self._cur.append((p1[0] * self.scale, p1[1] * self.scale))
            self._pt = p1

        def _curveToOne(self, p1, p2, p3):
            x0, y0 = self._pt
            for i in range(1, 13):
                t = i / 12
                mt = 1 - t
                x = mt**3 * x0 + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
                y = mt**3 * y0 + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
                self._cur.append((x * self.scale, y * self.scale))
            self._pt = p3

        def _qCurveToOne(self, p1, p2):
            x0, y0 = self._pt
            for i in range(1, 9):
                t = i / 8
                mt = 1 - t
                x = mt**2 * x0 + 2 * mt * t * p1[0] + t**2 * p2[0]
                y = mt**2 * y0 + 2 * mt * t * p1[1] + t**2 * p2[1]
                self._cur.append((x * self.scale, y * self.scale))
            self._pt = p2

        def _closePath(self):
            if self._cur:
                self.contours.append(self._cur)
                self._cur = []

        def _endPath(self):
            if self._cur:
                self.contours.append(self._cur)
                self._cur = []

    tt = TTFont(path)
    gs = tt.getGlyphSet()
    scale = 2000.0 / tt["head"].unitsPerEm
    order = tt.getGlyphOrder()
    cache = {}
    for gid, name in enumerate(order):
        pen = _SegPen(gs, scale)
        gs[name].draw(pen)
        cache[gid] = [c for c in pen.contours if len(c) >= 2]
    return cache


def _shifted(contours, dx):
    return [[(x + dx, y) for x, y in c] for c in contours]


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_all_encoded_pairs_clear_diagonal_floor(weight, italic):
    path = static_path(weight, italic)
    s = shaper(weight, italic)
    chars = [
        chr(c)
        for c in cmap_characters(weight, italic)
        if c > 32 and unicodedata.category(chr(c))[0] in "LNPS" and chr(c) not in LEFT_OUT
    ]
    chars = [c for c in chars if len(s.shape(c)) == 1]
    table = PairTable(path, {}, chars)
    bounds, scale = _glyph_geometry(path)
    gids = np.array(table.gids)
    b = bounds[gids]  # (N, 4): xMin, yMin, xMax, yMax
    valid = ~np.isnan(b[:, 0])
    adv = np.array(table.advance, dtype=float)
    n = len(chars)
    idx = np.arange(n)
    k = table.kerning(idx, idx)  # (N, N) in 2000-UPM

    # Vectorized bbox distance^2 < DIAGONAL_FLOOR^2
    dx = np.maximum(0.0, (b[None, :, 0] + adv[:, None] + k) - b[:, None, 2])
    dx2 = np.maximum(0.0, b[:, None, 0] - (b[None, :, 2] + adv[:, None] + k))
    gap_x = np.maximum(dx, dx2)
    dy = np.maximum(0.0, b[None, :, 1] - b[:, None, 3])
    dy2 = np.maximum(0.0, b[:, None, 1] - b[None, :, 3])
    gap_y = np.maximum(dy, dy2)
    cand = (valid[:, None] & valid[None, :]) & ((gap_x**2 + gap_y**2) < DIAGONAL_FLOOR**2)

    # Dilated 4-unit row pre-filter: if every row of left is >= 15 units from every row of right within ±16 units vertically,
    # Euclidean distance is guaranteed >= 15.0 (0 false negatives).
    xs, ys = np.nonzero(cand)
    l_max = table.lmax  # (N, R), -inf where empty
    r_min = table.rmin  # (N, R), +inf where empty
    pad = np.full((n, 4), np.inf)
    r_pad = np.concatenate([pad, r_min, pad], axis=1)
    r_dil = np.min(np.stack([r_pad[:, i:i + r_min.shape[1]] for i in range(9)], axis=2), axis=2)

    ccache = _contour_cache(path)
    tight = []
    for x, y in zip(xs, ys):
        # `calt` can swap the first glyph (`.arm` capitals, `at.case`): measure the glyph that is shaped
        rows, advance = table.first_rows(x, y)
        row_dist = np.min(r_dil[y] + advance + k[x, y] - rows)
        if row_dist >= DIAGONAL_FLOOR:
            continue
        a, ch_b = chars[x], chars[y]
        if _is_e2_exempt(weight, italic, a, ch_b):
            continue
        c1 = ccache[table.first_shaped.get((int(x), int(y)), gids[x])]
        c2 = _shifted(ccache[gids[y]], advance + k[x, y])
        od = outline_distance(c1, c2)
        if od < DIAGONAL_FLOOR:
            tight.append((a + ch_b, round(od, 2)))
    assert not tight, f"{weight} {'It' if italic else 'Up'}: {len(tight)} pairs < {DIAGONAL_FLOOR}: {tight[:15]}"
