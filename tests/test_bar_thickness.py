"""Bars added to letters stay lighter than the stems in Bold and Black.

Each bar is measured as the vertical run through its centre, over the stem of H (the horizontal run at a quarter
of the cap height), in the built static fonts. Ɨ ɨ follow the bars of Ħ ħ. ŧ, Ǥ and ǥ keep the lighter bar that
Inter and Source Sans 3 use in heavy weights.
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


def runs(polys, coord, horizontal):
    hits = []
    for poly in polys:
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            (ax, ay), (bx, by) = (a, b) if horizontal else ((a[1], a[0]), (b[1], b[0]))
            if (ay <= coord < by) or (by <= coord < ay):
                hits.append((ax + (coord - ay) / (by - ay) * (bx - ax), 1 if by > ay else -1))
    hits.sort()
    res, wind, start = [], 0, None
    for x, d in hits:
        prev, wind = wind, wind + d
        if prev == 0 and wind != 0:
            start = x
        elif prev != 0 and wind == 0:
            res.append((start, x))
    return res


def run_at(runs_, y):
    inside = [r for r in runs_ if r[0] <= y <= r[1]]
    return inside[0] if inside else min(runs_, key=lambda r: abs((r[0] + r[1]) / 2 - y))


def thickness(font, ch, y_centre, column):
    """Bar thickness of `ch`: the vertical run through `y_centre` at the x that `column(polys)` picks."""
    cmap = font.getBestCmap()
    polys = polygons(font, cmap[ord(ch)])
    r = run_at(runs(polys, column(polys), False), y_centre)
    return r[1] - r[0]


def left_end(y):
    return lambda polys: runs(polys, y, True)[0][0] + 40


def h_stem(font):
    polys = polygons(font, font.getBestCmap()[ord("H")])
    cap = font["OS/2"].sCapHeight
    r = runs(polys, cap * 0.25, True)[0]
    return r[1] - r[0]


def measured(weight, italic):
    font = TTFont(static_path(weight, italic))
    stem = h_stem(font)
    cmap = font.getBestCmap()
    gbar = polygons(font, "g.ss01")
    stem_right = runs(gbar, 517, True)[-1]
    out = {
        "Ħ": thickness(font, "Ħ", 1170, left_end(1170)),
        "Ɨ": thickness(font, "Ɨ", 723, left_end(723)),
        "ɨ": thickness(font, "ɨ", 560, left_end(560)),
        "ŧ": thickness(font, "ŧ", 555, left_end(555)),
        "ǥ": thickness(font, "ǥ", 517, lambda p: stem_right[1] + 0.08 * (stem_right[1] - stem_right[0])),
        "Ǥ": thickness(font, "Ǥ", 395, lambda p: max(x for poly in p for x, _ in poly) - 15),
    }
    assert cmap[ord("ǥ")]
    return stem, out


# upper bounds as a share of the H stem
BOUNDS = {
    "Bold": {"Ɨ": 0.60, "ɨ": 0.60, "ŧ": 0.50, "ǥ": 0.42, "Ǥ": 0.42},
    "Black": {"Ɨ": 0.56, "ɨ": 0.56, "ŧ": 0.42, "ǥ": 0.32, "Ǥ": 0.32},
}


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", ["Bold", "Black"])
def test_added_bars_stay_lighter_than_the_stem(weight, italic):
    stem, bars = measured(weight, italic)
    over = {ch: round(bars[ch] / stem, 2) for ch, cap in BOUNDS[weight].items() if bars[ch] / stem > cap}
    assert over == {}, f"bar over stem too heavy at {weight}: {over}"


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", ["Bold", "Black"])
def test_barred_i_follows_the_bars_of_h_bar(weight, italic):
    _, bars = measured(weight, italic)
    assert abs(bars["Ɨ"] - bars["Ħ"]) <= 12 and abs(bars["ɨ"] - bars["Ħ"]) <= 12
