"""Pair floor on the nearest ink (K3), per static.

Every encoded letter, and the typed `ị ɨ į ı i̇` with a top mark, is set against the characters of text (`a-z A-Z åäöÅÄÖéèüïîôçñ 0-9`
and the usual punctuation), in both orders with kerning on, and the distance between the two outlines (not the gap along one row)
must be at least a quarter of the `oo` distance of the same static: 55 units at Thin down to 30 at Black. The distance is measured to
the nearest ink in any direction, so corners that meet at an angle count. The test runs with no feature, with `ss01 ss02 ss03 cv04`
on together, with `cv01 cv03 cv05` on together and with `cv06 zero` on together (each swaps different glyphs), and again with `ss02`,
`ss03`, `cv04` and `case` each alone (a feature that swaps a glyph in a pair with a second feature hides what it does alone).
The column set also holds the characters the 0.9.0 review found tight (`Ì Ī Ý Î Ĵ È Ȉ ƒ ṟ € ₣ ȍ ħ ĵ`). Further tests set the typed `ị ɨ į ı i̇`
with a mark against every encoded letter, every capital of the `T`, `V` and `Y` kern groups against every lowercase letter, and the
small figures (`numr dnom subs sups frac`, with and without `cv06 zero`) against every letter and symbol.

`tests/data/floor-baseline.json.gz` lists the pairs that were already under the floor in 0.8.0 and that 0.9.0 left alone (`scripts/write_floor_baseline.py`
writes it from the built fonts). A pair under the floor that is not in the baseline fails the test, and so does a baseline pair that sits more than
`BASELINE_SLACK` units closer than the file says. Fixing a baseline pair means rerunning the script; the list is meant to shrink to nothing before 1.0.0.

A pair is first screened with the bounding boxes of its glyphs and with 4-unit rows (dilated by the floor), which can only rule out
pairs that are farther apart than the floor; `ink.fast_distance` then measures the rest.
"""
import gzip
import json
import unicodedata
from functools import lru_cache

import numpy as np
import pytest
from fontTools.ttLib import TTFont

from conftest import ROOT, static_path
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
# Each of these alone: with the four above together, a feature that another one swaps again never shows what it does alone.
SINGLE_SETS = {"ss02-alone": {"ss02": True}, "ss03-alone": {"ss03": True}, "cv04-alone": {"cv04": True}, "case-alone": {"case": True}}
ALL_SETS = {**FEATURE_SETS, **SINGLE_SETS}
# Characters the 0.9.0 review found within the floor of a typed or accented letter; they are columns of every set.
EXTRA_COLUMNS = "ÌĪÝÎĴÈȈƒṟ€₣ȍħĵ"
ROW_MARGIN = 6  # the rows hold ink at 4-unit steps
# Pairs left out, each with the measured reason. None yet.
EXEMPT = {}
BASELINE = ROOT / "tests" / "data" / "floor-baseline.json.gz"
BASELINE_SLACK = 1.0  # units a baseline pair may move closer before the test fails


@lru_cache(maxsize=None)
def baseline():
    """{static: {suite: {text: nearest-ink distance}}} of the pairs under the floor that 0.9.0 left for the 1.0.0 review."""
    with gzip.open(BASELINE, "rt", encoding="utf-8") as f:
        return json.load(f)


def static_id(weight, italic):
    return weight + ("-italic" if italic else "")


def outside_baseline(suite, weight, italic, found):
    """The pairs of `found` ([(text, distance, ...)]) that the baseline does not hold: not listed, or closer than listed by more than the slack."""
    held = baseline().get(static_id(weight, italic), {}).get(suite, {})
    return [f for f in found if f[0] not in EXEMPT and (f[0] not in held or f[1] < held[f[0]] - BASELINE_SLACK)]


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


def violations(weight, italic, features_name, **kwargs):
    """[(text, distance)] of the pairs closer than the floor of this static (distance in font units)."""
    return [(t, d) for t, d, _, _ in font_violations(static_path(weight, italic), features_name, shaper(weight, italic), **kwargs)]


def font_violations(path, features, sh=None, rows=None, cols=None, both_orders=True):
    """[(text, distance, first glyph name, second glyph name)] of the pairs closer than the floor of this font, as shaped.

    `features`: a key of `ALL_SETS` or a feature dict. `rows` (default: every encoded letter and the typed forms) and `cols`
    (default: `SET` and `EXTRA_COLUMNS`) are lists of texts that shape to one glyph; each row is set before and, with `both_orders`, after each column."""
    if isinstance(features, str):
        features = ALL_SETS[features]
    floor = font_floor(path)
    contours, bounds = glyph_contours(path)
    letters = row_texts(path) if rows is None else list(rows)
    columns = list(SET + EXTRA_COLUMNS) if cols is None else list(cols)
    texts = list(dict.fromkeys(letters + columns))
    table = PairTable(path, features, texts, shaper=sh or Shaper(path))
    rows = np.array([table.index[t] for t in letters if t in table.index], dtype=int)
    cols = np.array([table.index[t] for t in columns if t in table.index], dtype=int)
    gids = np.array(table.gids)
    found = {}
    r_dil = dilate(table.rmin, int(np.ceil((floor + ROW_MARGIN) / STEP)))
    for first, second in ((rows, cols), (cols, rows)) if both_orders else ((rows, cols),):
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


@pytest.mark.parametrize("features_name", list(ALL_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_every_pair_clears_the_nearest_ink_floor(weight, italic, features_name):
    tight = outside_baseline("main", weight, italic, suite_found("main", weight, italic, features_name))
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


# 0.9.0 review: the typed forms, the capitals of three kern groups and the small figures are set against every letter, not only the 98 of `SET`.
def encoded_letters(path):
    return [chr(c) for c in sorted(TTFont(path).getBestCmap()) if unicodedata.category(chr(c))[0] == "L"]


def typed_forms(path):
    """The typed `ị ɨ į ı i̇` with each top mark and the double grave (the rows of the main test that are not one codepoint)."""
    return [base + mark for base in TYPED_BASES for mark in TOP_MARKS + DOUBLE_GRAVE]


@pytest.mark.parametrize("features_name", list(ALL_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_typed_i_forms_clear_the_floor_against_every_encoded_letter(weight, italic, features_name):
    """`i̇́ į́ ị́ ɨ́ ı́` and the rest, in both orders, against every encoded letter (`i̇́Ì i̇́Ï i̇̂Î Ĵi̇̂` were 0 – 30 apart at Black)."""
    tight = outside_baseline("typed", weight, italic, suite_found("typed", weight, italic, features_name))
    assert tight == [], f"floor {static_floor(weight, italic):.1f}"


def tvy_group_capitals(path):
    """The encoded capitals of the kern1 groups `T`, `V` (with `W`) and `Y`, read from the Regular master."""
    from conftest import ROOT
    import plistlib

    groups = plistlib.loads((ROOT / "sources" / "OffentligSans-Regular.ufo" / "groups.plist").read_bytes())
    by_name = {n: chr(c) for c, n in TTFont(path).getBestCmap().items()}
    members = [m for g in ("public.kern1.T", "public.kern1.V", "public.kern1.Y") for m in groups[g]]
    return [by_name[m] for m in members if m in by_name and unicodedata.category(by_name[m]) == "Lu"]


def lowercase_letters(path):
    return [c for c in encoded_letters(path) if unicodedata.category(c) == "Ll"]


@pytest.mark.parametrize("features_name", list(ALL_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_t_v_y_group_capitals_clear_the_floor_before_every_lowercase_letter(weight, italic, features_name):
    """`Ŧȇ Ŧħ Ŧǐ Ỵĭ Ẃȗ Ŵǐ Ẃǐ` and the like: every capital of the groups before every lowercase letter (not only those with a top mark)."""
    tight = outside_baseline("tvy", weight, italic, suite_found("tvy", weight, italic, features_name))
    assert tight == [], f"floor {static_floor(weight, italic):.1f}"


SMALL_FIGURE_FEATURES = ("numr", "dnom", "subs", "sups")
FIGURE_VARIANTS = ({}, {"cv06": True}, {"zero": True}, {"cv06": True, "zero": True})


def symbol_characters(path):
    return [chr(c) for c in sorted(TTFont(path).getBestCmap()) if unicodedata.category(chr(c)) in ("Sc", "Sm", "Sk", "So") and c > 127]


@pytest.mark.parametrize("tag", SMALL_FIGURE_FEATURES)
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_small_figures_clear_the_floor(weight, italic, tag):
    """Figures with `numr`, `dnom`, `subs` or `sups`, with and without `cv06` and `zero`, against every letter, symbol and punctuation mark."""
    tight = outside_baseline("fig:" + tag, weight, italic, suite_found("fig:" + tag, weight, italic, None))
    assert tight == [], f"floor {static_floor(weight, italic):.1f}"


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_fractions_clear_the_floor(weight, italic):
    """`1⁄2€` and `€1⁄2`: with `frac` the numerator and denominator are small figures, set beside the letters and symbols around them."""
    tight = outside_baseline("frac", weight, italic, suite_found("frac", weight, italic, None))
    assert tight == [], f"floor {static_floor(weight, italic):.1f}"


def fraction_found(weight, italic):
    """[(text, distance)] of `1⁄2€`-style pairs (a denominator before a column, a column before a numerator) closer than the floor."""
    path = static_path(weight, italic)
    floor = font_floor(path)
    contours, bounds = glyph_contours(path)
    sh = shaper(weight, italic)
    cols = [c for c in dict.fromkeys(encoded_letters(path) + list(SET + EXTRA_COLUMNS) + symbol_characters(path)) if c != "⁄"]
    tight = []
    for extra in FIGURE_VARIANTS:
        features = {"frac": True, **extra}
        for digit in "0123456789":
            for col in cols:
                # (text, index of the first glyph of the pair): the denominator before the column, the column before the numerator
                for text, at in ((f"1⁄{digit}{col}", 2), (f"{col}{digit}⁄1", 0)):
                    shaped = sh.shape(text, features)
                    if len(shaped) != 4:
                        continue
                    (g1, advance), (g2, _) = shaped[at], shaped[at + 1]
                    b1, b2 = bounds[g1], bounds[g2]
                    if np.isnan(b1[0]) or np.isnan(b2[0]):
                        continue
                    gap_x = max(0.0, b2[0] + advance - b1[2], b1[0] - (b2[2] + advance))
                    gap_y = max(0.0, b2[1] - b1[3], b1[1] - b2[3])
                    if gap_x**2 + gap_y**2 >= floor**2:
                        continue
                    d = pair_distance(contours, g1, g2, advance, cap=floor + 1)
                    if d < floor:
                        tight.append((text, round(float(d), 1)))
    return tight


def suite_found(suite, weight, italic, key):
    """[(text, distance)] of the pairs of one suite that are under the floor of this static. `key` is a feature set name (`None` for the figures)."""
    path = static_path(weight, italic)
    sh = shaper(weight, italic)
    if suite == "main":
        return [(t, d) for t, d, _, _ in font_violations(path, key, sh)]
    if suite == "typed":
        return [(t, d) for t, d, _, _ in font_violations(path, key, sh, rows=typed_forms(path), cols=encoded_letters(path))]
    if suite == "tvy":
        return [(t, d) for t, d, _, _ in font_violations(path, key, sh, rows=tvy_group_capitals(path), cols=lowercase_letters(path), both_orders=False)]
    if suite.startswith("fig:"):
        cols = encoded_letters(path) + list(SET + EXTRA_COLUMNS) + symbol_characters(path)
        found = {}
        for extra in FIGURE_VARIANTS:
            for t, d, _, _ in font_violations(path, {suite[4:]: True, **extra}, sh, rows=list("0123456789"), cols=cols):
                found[t] = min(d, found.get(t, d))
        return sorted(found.items())
    if suite == "frac":
        found = {}
        for t, d in fraction_found(weight, italic):
            found[t] = min(d, found.get(t, d))
        return sorted(found.items())
    raise ValueError(suite)


def suites():
    """Every (suite, feature set key) the baseline covers."""
    return ([("main", k) for k in ALL_SETS] + [("typed", k) for k in ALL_SETS] + [("tvy", k) for k in ALL_SETS]
            + [("fig:" + tag, None) for tag in SMALL_FIGURE_FEATURES] + [("frac", None)])
