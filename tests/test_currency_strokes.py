"""The strokes added to $ ¢ ₿ stay lighter than the stems in Bold and Black.

Stroke thickness is the horizontal run at the top edge of the stroke, over the stem of H (the horizontal run at a
quarter of the cap height), in the built static fonts. Inter, Noto Sans and Source Sans 3 keep these strokes
between 0.30 and 0.65 of the stem in Black; Offentlig stays at or under 0.52.
"""
import pytest
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from conftest import static_path


def polygons(font, name):
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    out, cur, last = [], [], None
    for op, args in pen.value:
        if op == "moveTo":
            cur, last = [args[0]], args[0]
        elif op == "lineTo":
            cur.append(args[0]); last = args[0]
        elif op == "qCurveTo":
            offs, end, p0 = list(args[:-1]), args[-1], last
            for i, c in enumerate(offs):
                nxt = end if i == len(offs) - 1 else ((c[0] + offs[i + 1][0]) / 2, (c[1] + offs[i + 1][1]) / 2)
                for j in range(1, 9):
                    t = j / 8
                    cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * nxt[0],
                                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * nxt[1]))
                p0 = nxt
            last = end
        elif op in ("closePath", "endPath") and cur:
            out.append(cur); cur = []
    return out


def hruns(polys, y):
    hits = []
    for poly in polys:
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                hits.append((a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]), 1 if b[1] > a[1] else -1))
    hits.sort()
    res, wind, start = [], 0, None
    for x, d in hits:
        prev, wind = wind, wind + d
        if prev == 0 and wind != 0:
            start = x
        elif prev != 0 and wind == 0:
            res.append((start, x))
    return res


def first_run(font, ch, y):
    r = hruns(polygons(font, font.getBestCmap()[ord(ch)]), y)[0]
    return r[1] - r[0]


# upper bounds as a share of the H stem; targets are 0.58 at Bold and 0.50 at Black
BOUNDS = {"Bold": 0.60, "Black": 0.52}
PROBES = {"$": 1600, "¢": 1400, "₿": 1600}


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", ["Bold", "Black"])
def test_currency_strokes_stay_lighter_than_the_stem(weight, italic):
    font = TTFont(static_path(weight, italic))
    stem = first_run(font, "H", font["OS/2"].sCapHeight * 0.25)
    over = {ch: round(first_run(font, ch, y) / stem, 2) for ch, y in PROBES.items()
            if first_run(font, ch, y) / stem > BOUNDS[weight]}
    assert over == {}, f"stroke over stem too heavy at {weight}: {over}"


# Smallest counter of ₩ and ₦ (the diameter of the largest circle that fits inside the smallest enclosed shape of the glyph, in units of
# 2000 per em) at the nine weights, upright then italic. The bars sit apart so that no counter is a pinhole: before the bars were
# redrawn the smallest counter of ₩ was 13.
SMALLEST_COUNTER = {
    "₩": {False: [56, 86, 100, 60, 119, 107, 53, 54, 203], True: [56, 86, 89, 54, 106, 95, 48, 53, 196]},
    "₦": {False: [56, 96, 114, 80, 58, 35, 173, 141, 108], True: [56, 96, 104, 76, 57, 32, 169, 143, 108]},
}
COUNTER_SLACK = 1


def counters(font, ch):
    """Every enclosed shape of a glyph made of straight lines, as an array of points."""
    import numpy as np
    import pathops

    gs = font.getGlyphSet()
    recorded = DecomposingRecordingPen(gs)
    gs[font.getBestCmap()[ord(ch)]].draw(recorded)
    path = pathops.Path()
    pen = path.getPen()
    for op, args in recorded.value:
        if op == "moveTo":
            pen.moveTo(args[0])
        elif op == "lineTo":
            pen.lineTo(args[0])
        elif op in ("closePath", "endPath"):
            pen.closePath()
        else:
            raise AssertionError(f"{ch} has a curve ({op}); the counter measure takes straight lines")
    path.simplify(fix_winding=True)
    return [
        np.array([seg[1][-1] for seg in contour.segments if seg[0] != "closePath"], dtype=float)
        for contour in path.contours
        if contour.clockwise
    ]


def inscribed_diameter(poly, step=6):
    """Diameter of the largest circle inside a polygon, found on a grid of `step` units."""
    import numpy as np

    (x0, y0), (x1, y1) = poly.min(0), poly.max(0)
    grid = np.array([(x, y) for y in np.arange(y0, y1, step) for x in np.arange(x0, x1, step)])
    inside = np.zeros(len(grid), bool)
    edges = list(zip(poly, np.roll(poly, -1, axis=0)))
    for a, b in edges:
        crossing = (a[1] > grid[:, 1]) != (b[1] > grid[:, 1])
        with np.errstate(divide="ignore", invalid="ignore"):
            x = (b[0] - a[0]) * (grid[:, 1] - a[1]) / (b[1] - a[1]) + a[0]
        inside ^= crossing & (grid[:, 0] < x)
    points = grid[inside]
    if not len(points):
        return 0.0
    nearest = np.full(len(points), np.inf)
    for a, b in edges:
        ab = b - a
        t = np.clip(((points - a) @ ab) / max(float(ab @ ab), 1e-9), 0, 1)
        nearest = np.minimum(nearest, np.hypot(*(points - (a + t[:, None] * ab)).T))
    return 2 * float(nearest.max())


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("ch", ["₩", "₦"])
def test_won_and_naira_keep_their_smallest_counter(ch, italic):
    """The smallest counter of ₩ and ₦ is no smaller than today's value at each of the nine weights (1 unit of slack)."""
    weights = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"]
    found = {}
    for weight, want in zip(weights, SMALLEST_COUNTER[ch][italic]):
        sizes = [inscribed_diameter(c) for c in counters(TTFont(static_path(weight, italic)), ch)]
        assert sizes, f"{ch} has no counter at {weight}"
        if min(sizes) < want - COUNTER_SLACK:
            found[weight] = (round(min(sizes)), want)
    assert found == {}, f"smallest counter of {ch} (found, today's value): {found}"
