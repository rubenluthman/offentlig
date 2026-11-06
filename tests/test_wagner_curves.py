"""Smooth points stay smooth: handles on both sides of a smooth on-curve point are collinear."""
import math
from pathlib import Path

import pytest
import ufoLib2

SOURCES = Path(__file__).resolve().parent.parent / "sources"
LIMIT = 2.0  # degrees
# The five is redrawn by the figures work, which owns its corner.
EXEMPT = ("five",)


def _exempt(name):
    return any(name == e or name.startswith(e + ".") for e in EXEMPT)


def _kinks(glyph):
    found = []
    for ci, contour in enumerate(glyph.contours):
        pts = contour.points
        for i, p in enumerate(pts):
            if p.type not in ("curve", "line") or not p.smooth:
                continue
            a, b = pts[i - 1], pts[(i + 1) % len(pts)]
            v1 = (p.x - a.x, p.y - a.y)
            v2 = (b.x - p.x, b.y - p.y)
            if not any(v1) or not any(v2):
                continue
            angle = abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1])))
            if angle > LIMIT:
                found.append((ci, i, round(angle, 1)))
    return found


@pytest.mark.parametrize("ufo", sorted(p.name for p in SOURCES.glob("*.ufo")))
def test_smooth_points_have_collinear_handles(ufo):
    font = ufoLib2.Font.open(SOURCES / ufo)
    bad = {g.name: k for g in font if not _exempt(g.name) and (k := _kinks(g))}
    assert not bad, f"{ufo}: smooth points more than {LIMIT} degrees off collinear: {bad}"
