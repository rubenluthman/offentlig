"""Pair rules with the alternate forms on, at all 18 statics.

Every alternate glyph (`ss01`, `ss02`, `cv01`, `cv03`, `cv04`, `cv05`, `cv06`, `zero`, `onum`, and `ss03` and `salt` in the
combinations below) is measured against every encoded character, on both sides, with the two rules of `test_plain_pairs.py` and
`test_accent_pairs.py`: plain pairs keep 30 units, and a pair with an accented letter keeps the smaller of the gap of the same
pair with the base letters and 30 units, less 2. Only pairs where a glyph changes under the features are measured; the other
pairs are the default pairs, which those two files hold. Each feature is tested alone, and `cv04+ss03`, `salt+ss03`,
`onum+zero+cv06`, all features together and all but `onum` (lining figures) are the combinations in which two alternates meet
in one pair. Both tests run every set of `ALTERNATE_SETS` (`tests/feature_pairs.py`).

Two or more alternates without `ss03` are tested at the end of the file: every pair of features that can put two alternates side
by side, and all of them together. Those tests measure only the pairs with a swapped glyph on both sides, and list the pairs that
fail in `EXEMPT_RULES` and `EXEMPT_BELOW_DEFAULT` (see there).
"""
import itertools
from functools import lru_cache

import numpy as np
import pytest

from feature_pairs import ALTERNATE_SETS, FeaturePairs, combination_texts
from test_accent_pairs import FLOOR, diaeresis_pair
from test_spacing import ALL_FONTS, ALL_IDS, MASTERS, source


@pytest.mark.parametrize("features_name", list(ALTERNATE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_pairs_with_an_alternate_keep_the_gap_of_the_rules(weight, italic, features_name):
    found = FeaturePairs(weight, italic, ALTERNATE_SETS[features_name]).violations()
    assert [(text, gap, ref, rule) for _, _, text, gap, ref, rule in found] == []


def closed_below_default(weight, italic, features_name):
    """Pairs with an alternate that sit closer than the default pair of the same characters (see the test below), as (pair, gap, default gap)."""
    on = FeaturePairs(weight, italic, ALTERNATE_SETS[features_name])
    return tight_against_default(on, FeaturePairs(weight, italic, {}))


def tight_against_default(on, off, focus=()):
    """The pairs of `on` (a `FeaturePairs` with features) closer than the same characters in `off` (the same texts, no feature), as
    (pair, gap, default gap)."""
    texts = on.table.texts
    tight = []
    for todo in on.pair_chunks(focus):
        todo = [(a, b) for a, b in todo if texts[a] in off.table.index and texts[b] in off.table.index]
        gap_on = on.table.gaps_pairs(todo, on.table.kerning_pairs(todo))
        pairs_off = [(off.table.index[texts[a]], off.table.index[texts[b]]) for a, b in todo]
        gap_off = off.table.gaps_pairs(pairs_off, off.table.kerning_pairs(pairs_off))
        for (a, b), x, y in zip(todo, gap_on, gap_off):
            if np.isnan(x) or np.isnan(y) or np.isinf(y):
                continue
            if any(c in texts[a] + texts[b] for c in "⁄") or diaeresis_pair(texts[a], texts[b], on.weight, on.italic):
                continue  # the fraction slash overlaps figures (`frac` builds fractions); the diaeresis pairs keep 8 (above)
            if x < min(y, FLOOR) - 2 and (on.requirement(a, b, np.inf) is not None):
                tight.append((texts[a] + texts[b], round(float(x)), round(float(y))))
    return tight


@pytest.mark.parametrize("features_name", list(ALTERNATE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_an_alternate_never_closes_a_pair_below_the_default_pair(weight, italic, features_name):
    """A pair with an alternate keeps at least the smaller of the gap of the same characters without the feature and 30 units,
    less 2. This is the outcome the kerning groups of the alternates serve: an alternate that shares the groups of its default
    form but not its glyph-to-glyph exceptions would close the pair."""
    assert closed_below_default(weight, italic, features_name) == []


@pytest.mark.parametrize("master", MASTERS)
def test_y_before_the_ss01_g_with_a_mark_takes_the_value_of_its_group(master):
    """`Yğ` and `Yǧ` with `ss01` kern by the group of `g.ss01`: the glyph-to-glyph exceptions that used to sit on `public.kern1.Y` are gone."""
    exceptions = {b: v for (a, b), v in source(master).kerning.items() if a == "public.kern1.Y"}
    assert [b for b in exceptions if b in ("gbreve.ss01", "gcaron.ss01")] == []


# Two or more alternates without `ss03`. A pair can only be shorter than the single-feature pairs where a glyph that one feature
# swaps meets a glyph that another swaps, so each combination is measured over those pairs only (`combination_texts`), not over
# every encoded text. Any two of these features can meet (each swaps at least one glyph the others do not), so every pair of
# features is a combination; `salt` is `ss01` with `ss02` and adds nothing. The last two put all of them on, as `all` does with `ss03`.
COMBINATION_FEATURES = ("ss01", "ss02", "cv01", "cv03", "cv04", "cv05", "cv06", "zero", "onum", "case")
COMBINATIONS = {
    **{f"{a}+{b}": (a, b) for a, b in itertools.combinations(COMBINATION_FEATURES, 2)},
    "all but ss03": COMBINATION_FEATURES,
    "all but ss03 and onum": tuple(f for f in COMBINATION_FEATURES if f != "onum"),
}


@lru_cache(maxsize=None)
def default_pairs(weight, italic):
    """The pairs of every text the combinations measure, with no feature: the default gap of each pair. One table per font."""
    return FeaturePairs(weight, italic, {}, combination_texts(weight, italic, COMBINATION_FEATURES))


def combination_pairs(weight, italic, name):
    """The pairs of the combination `name` that break the rules, as two dicts from the pair's text to (gap, default gap): the
    plain and accent rule (`test_pairs_of_alternates_without_ss03_keep_the_gap_of_the_rules`) and the default-pair rule."""
    features = COMBINATIONS[name]
    on = FeaturePairs(weight, italic, {f: True for f in features}, combination_texts(weight, italic, features))
    off = default_pairs(weight, italic)

    rule = {}
    for a, b, text, gap, _, _ in on.violations("meeting"):
        ta, tb = on.table.texts[a], on.table.texts[b]
        pair = [(off.table.index[ta], off.table.index[tb])] if ta in off.table.index and tb in off.table.index else []
        shown = round(float(off.table.gaps_pairs(pair, off.table.kerning_pairs(pair))[0])) if pair else None
        rule[text] = (gap, shown)
    closed = {text: (gap, ref) for text, gap, ref in tight_against_default(on, off, "meeting")}
    return rule, closed


@lru_cache(maxsize=None)
def combination_result(weight, italic, name):
    return combination_pairs(weight, italic, name)


# Pairs of two alternates that break a rule and are left alone for now, each with its measured gap and the gap of the default pair
# (the same characters with no feature), one table per rule, keyed by (combination, static) and then by the pair's text:
#     "ĴÏ": (gap, default gap)
# A pair listed here must still fail with exactly these numbers, and a pair that fails must be listed: when kerning fits a pair,
# the test of its combination fails until the entry is removed, so the table cannot go stale. All 18 statics hold no pair at
# present, measured in every combination, so the tables are empty; an entry is added only with the measured gap of its pair.
EXEMPT_RULES = {}
EXEMPT_BELOW_DEFAULT = {}


def exemption_mismatch(found, exempt):
    """Lines that say how the pairs found differ from the exemption table: a pair not listed, a listed pair that now passes, or one
    whose numbers changed. An empty list means the table is the pairs that fail."""
    lines = [f"{pair}: gap {found[pair][0]}, default gap {found[pair][1]} is not in the exemption table" for pair in found if pair not in exempt]
    lines += [f"{pair}: listed at {exempt[pair]} but passes now; remove the entry" for pair in exempt if pair not in found]
    lines += [f"{pair}: listed at {exempt[pair]}, measured {found[pair]}" for pair in found if pair in exempt and tuple(exempt[pair]) != found[pair]]
    return lines


def test_the_exemption_check_fails_for_a_new_pair_a_pair_that_passes_and_changed_numbers():
    found = {"ĴÏ": (20, 120), "AB": (25, 60)}
    assert exemption_mismatch(found, dict(found)) == []
    assert len(exemption_mismatch(found, {"ĴÏ": (20, 120)})) == 1  # AB is new
    assert len(exemption_mismatch({"ĴÏ": (20, 120)}, dict(found))) == 1  # AB passes now
    assert len(exemption_mismatch(found, {"ĴÏ": (20, 120), "AB": (24, 60)})) == 1  # the gap moved


@pytest.mark.parametrize("combination", list(COMBINATIONS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_pairs_of_alternates_without_ss03_keep_the_gap_of_the_rules(weight, italic, combination):
    """Where two alternates without `ss03` meet, the pair keeps the plain and accent rule (30 units; the smaller of the base
    letters' gap and 30, less 2). The pairs that fail today are in `EXEMPT_RULES`."""
    found, _ = combination_result(weight, italic, combination)
    key = (combination, ALL_IDS[ALL_FONTS.index((weight, italic))])
    assert exemption_mismatch(found, EXEMPT_RULES.get(key, {})) == []


@pytest.mark.parametrize("combination", list(COMBINATIONS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_two_alternates_without_ss03_never_close_a_pair_below_the_default_pair(weight, italic, combination):
    """Where two alternates without `ss03` meet, the pair keeps at least the smaller of the gap of the same characters with no
    feature and 30 units, less 2. The pairs that fail today are in `EXEMPT_BELOW_DEFAULT`."""
    _, closed = combination_result(weight, italic, combination)
    key = (combination, ALL_IDS[ALL_FONTS.index((weight, italic))])
    assert exemption_mismatch(closed, EXEMPT_BELOW_DEFAULT.get(key, {})) == []
