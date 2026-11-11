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
