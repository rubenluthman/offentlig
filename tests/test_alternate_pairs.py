"""Pair rules with the alternate forms on, at all 18 statics.

Every alternate glyph (`ss01`, `ss02`, `cv01`, `cv03`, `cv05`, `cv06`, `zero`, `onum`, and `cv04`, `ss03` and `salt` in the
combinations below) is measured against every encoded character, on both sides, with the two rules of `test_plain_pairs.py` and
`test_accent_pairs.py`: plain pairs keep 30 units, and a pair with an accented letter keeps the smaller of the gap of the same
pair with the base letters and 30 units, less 2. Only pairs where a glyph changes under the features are measured; the other
pairs are the default pairs, which those two files hold. Each feature is tested alone, and `cv04+ss03`, `salt+ss03`,
`onum+zero+cv06` and all features together are the combinations in which two alternates meet in one pair.
"""
import numpy as np
import pytest

from feature_pairs import ALTERNATE_SETS, FeaturePairs
from test_accent_pairs import AIM
from test_spacing import ALL_FONTS, ALL_IDS


@pytest.mark.parametrize("features_name", list(ALTERNATE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_pairs_with_an_alternate_keep_the_gap_of_the_rules(weight, italic, features_name):
    found = FeaturePairs(weight, italic, ALTERNATE_SETS[features_name]).violations()
    assert [(text, gap, ref, rule) for _, _, text, gap, ref, rule in found] == []


@pytest.mark.parametrize("features_name", ["ss01", "ss02", "cv01", "cv03", "cv05", "cv06", "zero", "onum", "all"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_an_alternate_never_closes_a_pair_below_the_default_pair(weight, italic, features_name):
    """A pair with an alternate keeps at least the smaller of the gap of the same characters without the feature and 30 units,
    less 2. This is the outcome the kerning groups of the alternates serve: an alternate that shares the groups of its default
    form but not its glyph-to-glyph exceptions would close the pair."""
    on = FeaturePairs(weight, italic, ALTERNATE_SETS[features_name])
    off = FeaturePairs(weight, italic, {})
    texts = on.table.texts
    todo = [(a, b) for a, b in on.pairs() if texts[a] in off.table.index and texts[b] in off.table.index]
    gap_on = on.table.gaps_pairs(todo, on.table.kerning_pairs(todo))
    pairs_off = [(off.table.index[texts[a]], off.table.index[texts[b]]) for a, b in todo]
    gap_off = off.table.gaps_pairs(pairs_off, off.table.kerning_pairs(pairs_off))
    tight = []
    for (a, b), x, y in zip(todo, gap_on, gap_off):
        if np.isnan(x) or np.isnan(y) or np.isinf(y):
            continue
        if any(c in texts[a] + texts[b] for c in "⁄ȉȑ"):
            continue  # the fraction slash overlaps figures by design; `ȉ ȑ` are in the ROADMAP Icebox
        if x < min(y, AIM) - 2 and (on.requirement(a, b, np.inf) is not None):
            tight.append((texts[a] + texts[b], round(float(x)), round(float(y))))
    assert tight == []
