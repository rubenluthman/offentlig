"""Pair rules for the whole font: accents, round dots and the named plain pairs, measured on every static.

An accent never brings a pair below what the same pair has with the unaccented base letters, up to 30 units, less 2
(`ACCENT_SLACK`). The checks run over every encoded letter, digit, punctuation mark and symbol on both sides of every accented
letter (and the typed `ị` and `ɨ` with a top mark, which shape as one glyph), at all 18 statics, with no feature, with the round
dots (`ss03`) and with the single-storey `a` (`cv04`).
"""
import unicodedata
from functools import lru_cache

import numpy as np
import pytest
from fontTools.ttLib import TTFont

from conftest import static_path
from pairs import PairTable
from test_spacing import ALL_FONTS, ALL_IDS, CLOSING_PUNCTUATION, DIAERESIS_TALL, LEFT_FOR_THE_ICEBOX, OPENING_PUNCTUATION, shaper

FLOOR = 30
ACCENT_SLACK = 2
TOP_MARKS = "́̀̂̄̃̆̈̌"
# The diaeresis of ï ḯ and typed ị̈ ɨ̈ is held to 8 units only next to H l i b k h d in ExtraBold and Black Italic.
DIAERESIS_FLOOR = {char: neighbours for char, (_floor, neighbours) in DIAERESIS_TALL.items()}
FEATURE_SETS = {"default": {}, "ss03": {"ss03": True}, "cv04": {"cv04": True}}


@lru_cache(maxsize=None)
def cmap_characters(weight, italic):
    return sorted(TTFont(static_path(weight, italic)).getBestCmap())


def encoded_texts(weight, italic):
    """Every encoded letter, digit, punctuation mark and symbol, then the typed `ị` and `ɨ` with a top mark."""
    chars = [chr(c) for c in cmap_characters(weight, italic) if c > 32 and unicodedata.category(chr(c))[0] in "LNPS"]
    return chars + [base + mark for base in "ịɨ" for mark in TOP_MARKS]


def diaeresis_twin(text):
    """The typed `ị` and `ɨ` with a diaeresis kern like `ï` (test_spacing.py compares them), so they share its exceptions."""
    return "ï" if len(text) == 2 and text[1] == "\u0308" else text


def is_accented(text):
    if len(text) == 2:
        return True
    return unicodedata.category(text) in ("Lu", "Ll") and len(unicodedata.normalize("NFD", text)) > 1 and text not in LEFT_FOR_THE_ICEBOX


def base_of(text):
    if len(text) == 2:
        return "i" if text[0] == "ị" else "ɨ"
    return unicodedata.normalize("NFD", text)[0]


@lru_cache(maxsize=3)
def whole_table(weight, italic, features_name):
    """The pair table of every encoded text at one static: (table, kerning matrix, gap matrix)."""
    table = PairTable(static_path(weight, italic), FEATURE_SETS[features_name], encoded_texts(weight, italic))
    everything = np.arange(len(table.texts))
    kern = table.kerning(everything, everything)
    return table, kern, table.gaps(everything, everything, kern)


@pytest.mark.parametrize("features_name", list(FEATURE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_an_accent_never_closes_a_pair_below_the_unaccented_pair(weight, italic, features_name):
    """Every pair with an accented letter, on either side, keeps at least the smaller of the gap of the same pair with the
    unaccented base letters and 30 units, less 2. Pairs with `ȉ ȑ` (the narrower double grave is in the ROADMAP Icebox),
    and the diaeresis pairs held to 8 are left out."""
    table, kern, gap = whole_table(weight, italic, features_name)
    texts = table.texts
    accented = np.array([is_accented(t) and t not in LEFT_FOR_THE_ICEBOX for t in texts])
    reference = np.array([table.index.get(base_of(t), -1) if a else i for i, (t, a) in enumerate(zip(texts, accented))])
    xs, ys = np.nonzero((accented[:, None] | accented[None, :]) & ~np.isnan(kern))
    tight = []
    for x, y in zip(xs, ys):
        ref = np.inf
        if reference[x] >= 0 and reference[y] >= 0 and not np.isnan(gap[reference[x], reference[y]]):
            ref = gap[reference[x], reference[y]]
        found = accent_violation(texts[x], texts[y], accented[x], accented[y], gap[x, y], ref, weight, italic)
        if found:
            tight.append(found)
    assert tight == []


DIAERESIS_MIN = 8


def diaeresis_pair(a, b, weight, italic):
    """True for the pairs of ï ḯ ị̈ ɨ̈ with H l i b k h d in ExtraBold and Black Italic, which keep 8 units."""
    if not (italic and weight in ("ExtraBold", "Black")):
        return False
    ta, tb = diaeresis_twin(a), diaeresis_twin(b)
    return (ta in DIAERESIS_FLOOR and b in DIAERESIS_FLOOR[ta]) or (tb in DIAERESIS_FLOOR and a in DIAERESIS_FLOOR[tb])


def accent_violation(a, b, accented_a, accented_b, gap, ref, weight="", italic=False):
    """None, or (pair, gap, reference gap) when a pair with an accented letter breaks the rule above: `ref` is the gap of the
    same pair with the unaccented base letters (inf when there is none). Pairs with `ȉ ȑ` pass;
    the diaeresis pairs held to 8 in ExtraBold/Black Italic fail below 8 units."""
    if any(c in a + b for c in LEFT_FOR_THE_ICEBOX):
        return None
    if (len(b) == 1 and b in CLOSING_PUNCTUATION and accented_a) or (len(a) == 1 and a in OPENING_PUNCTUATION and accented_b):
        # brackets and quotes keep the 30 units of test_accented_letters_clear_the_punctuation_next_to_them, with no slack
        return (a + b, round(float(gap)), None) if gap < FLOOR else None
    if diaeresis_pair(a, b, weight, italic):
        return (a + b, round(float(gap)), None) if gap < DIAERESIS_MIN else None
    if gap < min(ref, FLOOR) - ACCENT_SLACK:
        return (a + b, round(float(gap)), round(float(ref)) if ref != np.inf else None)
    return None


ROUND_DOT_SLACK = 2


@lru_cache(maxsize=1)
def round_dot_tables(weight, italic):
    """Every encoded character (no marks, no spaces), shaped with and without `ss03`, and the ones `ss03` swaps."""
    path = static_path(weight, italic)
    s = shaper(weight, italic)
    chars = [chr(c) for c in cmap_characters(weight, italic) if c > 32 and chr(c).isprintable() and not unicodedata.category(chr(c)).startswith("M")]
    chars = [c for c in chars if len(s.shape(c)) == 1 and len(s.shape(c, {"ss03": True})) == 1]
    plain, rounded = PairTable(path, {}, chars), PairTable(path, {"ss03": True}, chars)
    everything = np.arange(len(chars))
    k1, k2 = plain.kerning(everything, everything), rounded.kerning(everything, everything)
    dotted = np.array([plain.gids[i] != rounded.gids[i] for i in range(len(chars))])
    return chars, dotted, plain.gaps(everything, everything, k1), rounded.gaps(everything, everything, k2)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_round_dot_pairs_keep_the_gap_of_the_default_pairs(weight, italic):
    """Every pair of encoded characters with a round-dot form on either side keeps at least the smaller of the default
    pair's gap and 30 units, less 2: `ss03` shares the default glyph's groups but not its glyph-to-glyph exceptions, so each
    exception needs a copy for the `.ss03` sibling."""
    chars, dotted, plain, rounded = round_dot_tables(weight, italic)
    xs, ys = np.nonzero((dotted[:, None] | dotted[None, :]) & ~np.isnan(plain) & ~np.isnan(rounded))
    tight = []
    for x, y in zip(xs, ys):
        a, b = chars[x], chars[y]
        if any(c in a + b for c in LEFT_FOR_THE_ICEBOX + "\u2044") or diaeresis_pair(a, b, weight, italic):
            continue
        if np.isinf(plain[x, y]) or np.isinf(rounded[x, y]):
            continue
        if rounded[x, y] < min(plain[x, y], FLOOR) - ROUND_DOT_SLACK:
            tight.append((a + b, round(float(plain[x, y])), round(float(rounded[x, y]))))
    assert tight == []


# Plain pairs that closed in a weight of Public Sans: the bracket before the dotless and the hooked j, the brace before the euro
# sign, and the closing brackets after f.
PLAIN_PAIRS = ["[j", "{j", "[ȷ", "{ȷ", "}€", "f)", "f]", "f}"]


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_named_plain_pairs_keep_30_units(weight, italic):
    s = shaper(weight, italic)
    tight = [(text, round(s.gap(text))) for text in PLAIN_PAIRS if s.gap(text) is not None and s.gap(text) < 30]
    assert tight == []
