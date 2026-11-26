"""Pair floor on the nearest ink (K3), per static.

Every encoded letter, and the typed `ị ɨ į ı i̇` with a top mark, is set against the characters of text (`a-z A-Z åäöÅÄÖéèüïîôçñ 0-9`
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


TYPED_BASES = ("ị", "ɨ", "į", "ı", "i\u0307")  # the typed `i̇` (Lithuanian) is `i` + U+0307
DOUBLE_GRAVE = "\u030f"


def row_texts(path):
    letters = [chr(c) for c in sorted(TTFont(path).getBestCmap()) if unicodedata.category(chr(c))[0] == "L"]
    return letters + [base + mark for base in TYPED_BASES for mark in TOP_MARKS + DOUBLE_GRAVE]


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
    for base in TYPED_BASES:
        assert len(s.shape(base + "̏")) == 1, base
        assert len(s.shape(base + "̏", {"ss03": True})) == 1, base


# T- and Y-group capitals before the lowercase letters with a top mark (`Ýá Ŷĕ Ÿê`, `Tš`, `Yî`, and the typed `ı́ i̇́ į́ ị́`). The capitals
# with a mark of their own are not in the column set of the main test, nor are most of these letters.
TY_CAPITALS = "TŤŦŢȚṪṬṮYÝŶŸẎỴỲỶȲỸ"
TY_MARKED_CAPITALS = "ÝŶŸȲẎỲỶỸŤṪ"
FLOOR_CAPITALS = "TY" + TY_MARKED_CAPITALS  # `Ŧ Ţ Ț Ṭ Ṯ Ỵ` have a bar or a mark below: see the note at the test


def lowercase_with_top_marks(path):
    """Every encoded lowercase letter whose decomposition has a mark above, then the typed bases with a top mark or a double grave."""
    letters = [
        chr(c) for c in sorted(TTFont(path).getBestCmap())
        if unicodedata.category(chr(c)) == "Ll" and any(unicodedata.combining(x) == 230 for x in unicodedata.normalize("NFD", chr(c)))
    ]
    return letters + [base + mark for base in TYPED_BASES for mark in TOP_MARKS + DOUBLE_GRAVE]


def short_pairs(weight, italic, features_name, lefts, rights, limit):
    """[(text, distance)] of the pairs `left + right` (each side one glyph, kerning on) closer than `limit` units, nearest ink."""
    path = static_path(weight, italic)
    sh, features = shaper(weight, italic), FEATURE_SETS[features_name]
    contours, bounds = glyph_contours(path)
    one = {t: sh.shape(t, features) for t in dict.fromkeys(list(lefts) + list(rights))}
    out = []
    for a in lefts:
        for b in rights:
            if len(one[a]) != 1 or len(one[b]) != 1:
                continue
            shaped = sh.shape(a + b, features)
            if len(shaped) != 2:
                continue
            (g1, advance), (g2, _) = shaped
            b1, b2 = bounds[g1], bounds[g2]
            if np.isnan(b1[0]) or np.isnan(b2[0]):
                continue
            gap_x = max(0.0, b2[0] + advance - b1[2], b1[0] - (b2[2] + advance))
            gap_y = max(0.0, b2[1] - b1[3], b1[1] - b2[3])
            if gap_x**2 + gap_y**2 >= limit**2:
                continue
            d = pair_distance(contours, g1, g2, advance, cap=limit + 1)
            if d < limit:
                out.append((a + b, round(float(d), 1)))
    return out


@pytest.mark.parametrize("features_name", list(FEATURE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_t_and_y_capitals_clear_the_top_marks_of_lowercase_letters(weight, italic, features_name):
    """`T Y Ý Ŷ Ÿ Ȳ Ẏ Ỳ Ỷ Ỹ Ť Ṫ` before every lowercase letter with a top mark clear the floor. The other capitals of the two groups
    (`Ŧ Ţ Ț Ṭ Ṯ Ỵ`) are held to floor + 10 at Black only, by the next test."""
    path = static_path(weight, italic)
    tight = short_pairs(weight, italic, features_name, FLOOR_CAPITALS, lowercase_with_top_marks(path), font_floor(path))
    assert [t for t in tight if t[0] not in EXEMPT] == [], f"floor {font_floor(path):.1f}"


AIM_AT_BLACK = 10  # K20: floor + 10 at the masters Black and Black Italic


@pytest.mark.parametrize("features_name", list(FEATURE_SETS))
@pytest.mark.parametrize("italic", [False, True], ids=["Black", "Black-italic"])
def test_t_and_y_capitals_clear_tall_marks_by_the_floor_plus_10_at_black(italic, features_name):
    """K20: every capital of the kern1 groups T and Y before a lowercase letter with a top mark is at least floor + 10 from it in
    Black and Black Italic. The one exemption is `ẗ` with `ss03` (in `alternates`): its round dots sit under the arm, so clearing
    them takes 61 – 161 units (P14) and the pair stays at 31 against a floor of 30, which the floor tests still hold."""
    path = static_path("Black", italic)
    limit = font_floor(path) + AIM_AT_BLACK
    tight = short_pairs("Black", italic, features_name, TY_CAPITALS, lowercase_with_top_marks(path), limit)
    if features_name == "alternates":
        tight = [(t, d) for t, d in tight if t[1:] != "ẗ"]
    assert tight == [], f"floor + {AIM_AT_BLACK} = {limit:.1f}"
