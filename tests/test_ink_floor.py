"""Pair floor on the nearest ink (K3), per static.

Every encoded letter, and the typed `ị` and `ɨ` with a top mark, is set against the characters of text (`a-z A-Z åäöÅÄÖéèüïîôçñ 0-9`
and the usual punctuation), in both orders with kerning on, and the distance between the two outlines (not the gap along one row)
must be at least a quarter of the `oo` distance of the same static: 55 units at Thin down to 30 at Black. The distance is measured to
the nearest ink in any direction, so corners that meet at an angle count. The test runs with no feature, with `ss01 ss02 ss03 cv04`
on together, with `cv01 cv03 cv05` on together and with `cv06 zero` on together (each swaps different glyphs).

A pair is first screened with the bounding boxes of its glyphs and with 4-unit rows (dilated by the floor), which can only rule out
pairs that are farther apart than the floor; `ink.fast_distance` then measures the rest.
"""
import unicodedata
from functools import lru_cache

import numpy as np
import pytest
from fontTools.ttLib import TTFont

from conftest import static_path
from ink import Polyline, fast_distance
from pairs import LOW, STEP, PairTable
from test_accent_pairs import TOP_MARKS, cmap_characters
from test_spacing import ALL_FONTS, ALL_IDS, Shaper, shaper

FLOOR_SHARE = 0.25  # of the `oo` distance
SET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZåäöÅÄÖéèüïîôçñ0123456789.,:;!?'\"‘’“”()[]{}-–/&"
FEATURE_SETS = {
    "default": {},
    "alternates": {"ss01": True, "ss02": True, "ss03": True, "cv04": True},
    "letters": {"cv01": True, "cv03": True, "cv05": True},
    "figures": {"cv06": True, "zero": True},
}
ROW_MARGIN = 6  # the rows hold ink at 4-unit steps
# Pairs left out, each with the measured reason. None yet.
EXEMPT = {}


@lru_cache(maxsize=None)
def glyph_contours(path):
    """Contours of every glyph as arrays (units per em is 2000 in every static), keyed by glyph id."""
    tt = TTFont(path)
    gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
    out, bounds = {}, np.full((len(order), 4), np.nan)
    for gid, name in enumerate(order):
        poly = Polyline(gs)
        gs[name].draw(poly)
        out[gid] = [np.array(c, dtype=float) for c in poly.contours if len(c) > 1]
        if out[gid]:
            allp = np.concatenate(out[gid])
            bounds[gid] = [*allp.min(axis=0), *allp.max(axis=0)]
    return out, bounds


def pair_distance(contours, first, second, offset, cap=300.0):
    left = contours[first]
    right = [c + (offset, 0) for c in contours[second]]
    return fast_distance(left, right, cap)


@lru_cache(maxsize=None)
def font_floor(path):
    """A quarter of the nearest-ink distance of `oo` in this font, kerning on."""
    contours, _ = glyph_contours(path)
    (g1, advance), (g2, _) = Shaper(path).shape("oo")
    return FLOOR_SHARE * pair_distance(contours, g1, g2, advance)


def static_floor(weight, italic):
    return font_floor(static_path(weight, italic))


def row_texts(path):
    letters = [chr(c) for c in sorted(TTFont(path).getBestCmap()) if unicodedata.category(chr(c))[0] == "L"]
    return letters + [base + mark for base in "ịɨį" for mark in TOP_MARKS + "̏"]


def dilate(rows, steps):
    """Smallest value within `steps` rows above or below, per row."""
    out = rows.copy()
    for k in range(1, steps + 1):
        out[:, k:] = np.minimum(out[:, k:], rows[:, :-k])
        out[:, :-k] = np.minimum(out[:, :-k], rows[:, k:])
    return out


def violations(weight, italic, features_name):
    """[(text, distance)] of the pairs closer than the floor of this static (distance in font units)."""
    return [(t, d) for t, d, _, _ in font_violations(static_path(weight, italic), features_name, shaper(weight, italic))]


def font_violations(path, features_name, sh=None):
    """[(text, distance, first glyph name, second glyph name)] of the pairs closer than the floor of this font, as shaped."""
    floor = font_floor(path)
    contours, bounds = glyph_contours(path)
    letters = row_texts(path)
    texts = list(dict.fromkeys(letters + list(SET)))
    table = PairTable(path, FEATURE_SETS[features_name], texts, shaper=sh or Shaper(path))
    rows = np.array([table.index[t] for t in letters if t in table.index])
    cols = np.array([table.index[t] for t in SET if t in table.index])
    gids = np.array(table.gids)
    found = {}
    r_dil = dilate(table.rmin, int(np.ceil((floor + ROW_MARGIN) / STEP)))
    for first, second in ((rows, cols), (cols, rows)):
        kern = table.kerning(first, second)
        b = bounds[gids]
        adv = table.advance
        # box distance between the first glyph and the second placed after it
        x_lo2 = b[second, 0][None, :] + adv[first][:, None] + kern
        x_hi2 = b[second, 2][None, :] + adv[first][:, None] + kern
        gap_x = np.maximum(0.0, np.maximum(x_lo2 - b[first, 2][:, None], b[first, 0][:, None] - x_hi2))
        gap_y = np.maximum(0.0, np.maximum(b[second, 1][None, :] - b[first, 3][:, None], b[first, 1][:, None] - b[second, 3][None, :]))
        near = ((gap_x**2 + gap_y**2) < floor**2) & ~np.isnan(kern)
        # a first glyph that `calt` swapped has other bounds: screen it by its rows only
        at_first, at_second = {int(i): n for n, i in enumerate(first)}, {int(i): n for n, i in enumerate(second)}
        for (a, c) in table.first_shaped:
            if a in at_first and c in at_second:
                near[at_first[a], at_second[c]] = not np.isnan(kern[at_first[a], at_second[c]])
        xs, ys = np.nonzero(near)
        for x, y in zip(xs, ys):
            a, c = int(first[x]), int(second[y])
            rows_a, advance = table.first_rows(a, c)
            if (r_dil[c] + advance + kern[x, y] - rows_a).min() >= floor + ROW_MARGIN:
                continue
            text = table.texts[a] + table.texts[c]
            d = pair_distance(contours, table.first_shaped.get((a, c), gids[a]), gids[c], advance + kern[x, y])
            if d < floor:
                found[text] = (round(float(d), 1), table.names[table.first_shaped.get((a, c), gids[a])], table.names[gids[c]])
    return [(t, d, f, g) for t, (d, f, g) in sorted(found.items())]


@pytest.mark.parametrize("features_name", list(FEATURE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_every_pair_clears_the_nearest_ink_floor(weight, italic, features_name):
    tight = [(t, d) for t, d in violations(weight, italic, features_name) if t not in EXEMPT]
    assert tight == [], f"floor {static_floor(weight, italic):.1f}"


# The neighbors of the ogonek hook that the 98-character set above leaves out: `ę` before `ƒ`, `ḻ`, `ṟ`, before the other forms of `g` and
# `j`, and before the parentheses in their `case` and `subs` forms (each shapes to a different glyph), and `( [ { \\` before `į`.
# 0.8.0 shipped `ęƒ` at 28.4 in Black Italic.
OGONEK_NEIGHBORS = [
    ("ę" + c, {}) for c in ")}ƒḻṟjgğĝġģĵ"
] + [("ę)", {"case": True}), ("ę)", {"subs": True}), ("ę}", {"case": True})] + [
    (c + "į", {}) for c in "([{\\"
] + [(c + "į", {"ss03": True}) for c in "([{\\"]


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_ogonek_neighbors_clear_the_floor(weight, italic):
    """Every pair of `OGONEK_NEIGHBORS` is at least the floor of its static from the nearest ink, kerning on."""
    path = static_path(weight, italic)
    floor = font_floor(path)
    contours, _ = glyph_contours(path)
    sh, cm = shaper(weight, italic), TTFont(path).getBestCmap()
    tight, checked = [], 0
    for text, features in OGONEK_NEIGHBORS:
        if not all(ord(c) in cm for c in text):
            continue
        shaped = sh.shape(text, features)
        if len(shaped) != 2:
            continue
        (first, advance), (second, _) = shaped
        checked += 1
        d = pair_distance(contours, first, second, advance)
        if d < floor:
            tight.append((text, features, round(float(d), 1)))
    assert checked >= 15
    assert tight == [], f"floor {floor:.1f}"


FLOORS = {
    ("Thin", False): 55, ("ExtraLight", False): 51.2, ("Light", False): 48.8, ("Regular", False): 46.5, ("Medium", False): 44,
    ("SemiBold", False): 41.8, ("Bold", False): 37.8, ("ExtraBold", False): 34, ("Black", False): 30,
}


@pytest.mark.parametrize("weight", [w for w, _ in FLOORS])
def test_the_floor_follows_the_weight(weight):
    assert static_floor(weight, False) == pytest.approx(FLOORS[(weight, False)], abs=0.6)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_the_typed_double_grave_forms_shape_as_one_glyph(weight, italic):
    s = shaper(weight, italic)
    for base in "ịɨį":
        assert len(s.shape(base + "̏")) == 1, base
        assert len(s.shape(base + "̏", {"ss03": True})) == 1, base
