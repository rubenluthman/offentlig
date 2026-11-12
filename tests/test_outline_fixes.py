"""Outline fixes: `two.osf`, `caroncomb.alt`, `aringacute.cv04`, ẞ and the hooks of Ƈ ƈ.

Everything is measured on the built static fonts, in font units per 2000 em.
"""
import glob
from pathlib import Path

import pytest
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

from conftest import BUILD, STATICS, STATIC_IDS, static_path
from test_bar_thickness import h_stem, polygons, runs

CHECKED = {"Thin": 100, "Regular": 400, "Bold": 700, "Black": 900}
STYLES = [False, True]
STYLE_IDS = ["roman", "italic"]


def font_of(weight, italic):
    return TTFont(static_path(weight, italic))


def signed_area(font, name):
    gs = font.getGlyphSet()
    pen = AreaPen(gs)
    gs[name].draw(pen)
    return pen.value


# caroncomb.alt: the contour runs the same way as every other glyph


def test_caroncomb_alt_runs_the_same_way_as_other_glyphs(static_ttf):
    alt = signed_area(static_ttf, "uni030C.alt")  # production name of caroncomb.alt
    for ref in ("l", "uni030C"):
        assert alt * signed_area(static_ttf, ref) > 0, f"caroncomb.alt runs against {ref}"


# _hook.C and _hook.c are drawing parts and are not exported


def test_hook_parts_are_in_no_built_font():
    paths = sorted(p for p in glob.glob(str(BUILD / "*" / "*")) if Path(p).suffix in {".ttf", ".otf", ".woff2"})
    assert paths, "no built fonts found"
    leaked = {}
    for path in paths:
        names = [n for n in TTFont(path).getGlyphOrder() if n.startswith("_hook.")]
        if names:
            leaked[Path(path).name] = names
    assert leaked == {}


@pytest.mark.parametrize("italic", STYLES, ids=STYLE_IDS)
def test_hook_letters_still_have_their_hook(italic):
    font = font_of("Bold", italic)
    cmap = font.getBestCmap()
    for cp in (0x187, 0x188):
        name = cmap[cp]
        top = max(y for poly in polygons(font, name) for _, y in poly)
        assert top >= (1740 if cp == 0x187 else 1430), f"{name} lost its hook"


# two.osf: the base bar is as thick as the bar of z


def bar(font, name):
    """Thickness of the bottom bar, as the lowest vertical run at x = 70 % of the advance."""
    polys = polygons(font, name)
    x = font["hmtx"][name][0] * 0.70
    return runs(polys, x, False)[0]


@pytest.mark.parametrize("italic", STYLES, ids=STYLE_IDS)
@pytest.mark.parametrize("weight", CHECKED)
def test_two_osf_bar_is_the_bar_of_z(weight, italic):
    font = font_of(weight, italic)
    z, two = bar(font, "z"), bar(font, "two.osf")
    assert abs((two[1] - two[0]) - (z[1] - z[0])) <= 1, f"two.osf bar {two} against z {z} at {weight}"


# ẞ: the slot between the stem and the lower terminal stays open


def slot(font, name):
    polys = polygons(font, name)
    best = None
    for y in range(20, 520, 10):
        r = runs(polys, y, True)
        if len(r) >= 2:
            gap = r[1][0] - r[0][1]
            best = gap if best is None else min(best, gap)
    return best


@pytest.mark.parametrize("italic", STYLES, ids=STYLE_IDS)
@pytest.mark.parametrize("weight", CHECKED)
def test_capital_sharp_s_slot_stays_open(weight, italic):
    font = font_of(weight, italic)
    gap = slot(font, font.getBestCmap()[0x1E9E])
    assert gap >= 60, f"ẞ slot is {gap:.0f} at {weight}"


def test_capital_sharp_s_slot_unchanged_in_regular():
    for italic in STYLES:
        font = font_of("Regular", italic)
        assert 120 <= slot(font, font.getBestCmap()[0x1E9E]) <= 128


# aringacute.cv04: ring and `a` leave exactly two counters, at every weight


def enclosed_counters(font, name, cell=6):
    polys = polygons(font, name)
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    x0, y0 = int(min(xs)) - 2 * cell, int(min(ys)) - 2 * cell
    w, h = int((max(xs) - x0) / cell) + 3, int((max(ys) - y0) / cell) + 3
    ink = [[False] * w for _ in range(h)]
    for j in range(h):
        for a, b in runs(polys, y0 + (j + 0.5) * cell, True):
            for i in range(max(0, int((a - x0) / cell)), min(w, int((b - x0) / cell) + 1)):
                if x0 + (i + 0.5) * cell >= a and x0 + (i + 0.5) * cell <= b:
                    ink[j][i] = True
    seen = [[False] * w for _ in range(h)]
    comps = []
    for j in range(h):
        for i in range(w):
            if ink[j][i] or seen[j][i]:
                continue
            stack, size, outer = [(i, j)], 0, False
            seen[j][i] = True
            while stack:
                a, b = stack.pop()
                size += 1
                if a in (0, w - 1) or b in (0, h - 1):
                    outer = True
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p, q = a + da, b + db
                    if 0 <= p < w and 0 <= q < h and not ink[q][p] and not seen[q][p]:
                        seen[q][p] = True
                        stack.append((p, q))
            if not outer:
                comps.append(size * cell * cell)
    return sorted(comps)


@pytest.mark.parametrize("italic", STYLES, ids=STYLE_IDS)
@pytest.mark.parametrize("weight", ["Regular", "SemiBold", "Bold", "ExtraBold", "Black"])
def test_aringacute_cv04_has_no_pinhole(weight, italic):
    font = font_of(weight, italic)
    # the pinhole this guards against is 2000 units² and more; smaller cells are flattening slivers of the raster
    counters = [c for c in enclosed_counters(font, "aringacute.cv04") if c > 1000]
    assert len(counters) == 2, f"aringacute.cv04 has counters {counters} at {weight}"
    assert counters[0] > 10000, f"ring counter {counters[0]} is too small at {weight}"


# Ƈ ƈ: the hook is lighter than the stem and not much thinner than half of it


def hook_stroke(font, name, y):
    r = runs(polygons(font, name), y, True)[-1]
    return r[1] - r[0]


@pytest.mark.parametrize("italic", STYLES, ids=STYLE_IDS)
@pytest.mark.parametrize("weight", ["Regular", "Bold", "Black"])
def test_hook_stroke_share_of_the_stem(weight, italic):
    font = font_of(weight, italic)
    cmap = font.getBestCmap()
    stem = h_stem(font)
    for cp, y in ((0x187, 1430), (0x188, 1120)):
        share = hook_stroke(font, cmap[cp], y) / stem
        low = 0.55 if weight == "Regular" else 0.62
        assert low <= share <= 0.80, f"{cmap[cp]} hook is {share:.2f} of the stem at {weight}"
