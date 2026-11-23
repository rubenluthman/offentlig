"""The joins of W and N in Bold to Black stay no wider than the reference fonts allow.

At the lower vertices of W and the two crotches of N the diagonals merge, and the ink there can hold a circle wider
than the stem. Each is measured as the widest circle inside the outline whose centre lies in the lower or the upper
half of the cap height, divided by the stem of H (the horizontal run at a quarter of the cap height, below the bar).
Measured on seven reference fonts at Bold, ExtraBold and Black, the median is 1.02 – 1.13 for the W vertices and
1.31 – 1.39 for the N crotches (docs/design-decisions.md, G26). The limits sit just above those medians, so the
0.6.0 shapes (W 1.31 – 1.34, N 1.43 – 1.48) fail them.
"""
import numpy as np
import pytest
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from conftest import static_path

W_LIMIT = 1.12
N_LIMIT = 1.38
STEP = 4   # grid step in units; the widest circle is found to within about 2 units


def contours(font, name):
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    out, cur = [], []
    for op, args in pen.value:
        assert op in ("moveTo", "lineTo", "closePath", "endPath"), f"{name} has curves"
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif cur:
            out.append(cur); cur = []
    return out


def widest_circle(polys, y_lo, y_hi):
    """Diameter of the widest circle inside the polygons with its centre in y_lo <= y < y_hi."""
    segs = np.array([(p[i], p[(i + 1) % len(p)]) for p in polys for i in range(len(p))], float)   # n x 2 x 2
    xs, ys = segs[:, :, 0], segs[:, :, 1]
    gx, gy = np.meshgrid(np.arange(xs.min(), xs.max(), STEP), np.arange(max(y_lo, ys.min()), min(y_hi, ys.max()), STEP))
    px, py = gx.ravel(), gy.ravel()
    ax, ay, bx, by = xs[:, 0][:, None], ys[:, 0][:, None], xs[:, 1][:, None], ys[:, 1][:, None]
    cross = ((ay <= py) != (by <= py)) & (px < ax + (py - ay) / np.where(by == ay, 1, by - ay) * (bx - ax))
    inside = cross.sum(axis=0) % 2 == 1
    px, py = px[inside], py[inside]
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0, 1)
    dist = np.hypot(px - ax - t * dx, py - ay - t * dy).min(axis=0)
    return 2 * dist.max()


def h_stem(font):
    polys = contours(font, "H")
    y = font["OS/2"].sCapHeight * 0.25
    xs = sorted(p[0] + (y - p[1]) / (q[1] - p[1]) * (q[0] - p[0]) for c in polys for p, q in zip(c, c[1:] + c[:1])
                if (p[1] <= y) != (q[1] <= y))
    return xs[1] - xs[0]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", ["Bold", "ExtraBold", "Black"])
def test_join_circles(weight, italic):
    font = TTFont(static_path(weight, italic))
    stem = h_stem(font)
    cap = font["OS/2"].sCapHeight
    w = widest_circle(contours(font, "W"), 0, cap / 2) / stem
    n_top = widest_circle(contours(font, "N"), cap / 2, cap + 1) / stem
    n_bottom = widest_circle(contours(font, "N"), 0, cap / 2) / stem
    assert w <= W_LIMIT, f"W lower vertices: circle {w:.2f} x stem, limit {W_LIMIT}"
    assert n_top <= N_LIMIT, f"N top-left crotch: circle {n_top:.2f} x stem, limit {N_LIMIT}"
    assert n_bottom <= N_LIMIT, f"N bottom-right crotch: circle {n_bottom:.2f} x stem, limit {N_LIMIT}"


WEIGHT_STEPS = list(range(400, 901, 25))


def lower_w_vertex_heights(path):
    """Height of the two lower vertices of `W` (the points where the inner edges of each stroke pair meet, between the baseline and half
    the cap height) on the variable font at each of `WEIGHT_STEPS`."""
    font = TTFont(path)
    cap = font["OS/2"].sCapHeight
    heights = []
    for wght in WEIGHT_STEPS:
        gs = font.getGlyphSet(location={"wght": wght})
        pen = DecomposingRecordingPen(gs)
        gs["W"].draw(pen)
        ys = [args[0][1] for op, args in pen.value if op in ("moveTo", "lineTo") and 50 < args[0][1] < cap / 2]
        assert len(ys) == 2 and abs(ys[0] - ys[1]) <= 1, (wght, ys)
        heights.append(round(sum(ys) / 2))
    return heights


def check_w_vertices_rise(heights):
    """Pairs (wght, height) where the height falls from one step to the next; a rounding step of 1 unit is allowed."""
    return [(w, h, nxt) for w, h, nxt in zip(WEIGHT_STEPS, heights, heights[1:]) if nxt < h - 1]


def test_lower_vertices_of_w_never_fall_with_weight(variable_path):
    """The lower vertices of `W` rise with weight from 400 to 900 (295 at 400 and 500, 335 at 700, 360 at 800 upright; 345 and 377
    in the italic). The 0.7.0 fonts fell from 295 at 400 to 248 at 500 before rising again, and this test fails on them."""
    heights = lower_w_vertex_heights(variable_path)
    assert check_w_vertices_rise(heights) == []
    assert heights[-1] > heights[0]
