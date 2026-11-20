"""Every pair of plain characters keeps at least 30 units of ink gap, at all 18 statics.

"Plain" means every encoded letter, digit, punctuation mark and symbol that is not an accented letter (`test_accent_pairs.py` holds
those). Both orders of every pair are measured with no feature, with the square dots (`ss03`) and with the single-storey `a` (`cv04`).
Pair exceptions aim at 40 units and the floor is 30, as for the accent pairs.
"""
import pytest

import numpy as np

from conftest import static_path
from pairs import PairTable
from test_accent_pairs import FEATURE_SETS, cmap_characters, is_accented
from test_spacing import ALL_FONTS, ALL_IDS

import unicodedata

FLOOR = 30
FRACTION_SLASH = "⁄"
# Pairs the test leaves alone, each with the reason given; the design-decision audit in the ROADMAP reviews each of them.
LEFT_OUT = {
    # The fraction slash overlaps the figures around it; `frac` builds the fractions and the slash is kerned for them, not for letters or signs.
    "fraction slash": lambda a, b: FRACTION_SLASH in a + b,
}


def plain_violation(a, b, gap):
    """None, or (pair, gap) when a pair of plain characters is closer than 30 units and is not in `LEFT_OUT`."""
    if gap < FLOOR and not any(rule(a, b) for rule in LEFT_OUT.values()):
        return (a + b, round(float(gap)))
    return None


def plain_texts(weight, italic):
    chars = [chr(c) for c in cmap_characters(weight, italic) if c > 32 and unicodedata.category(chr(c))[0] in "LNPS"]
    return [c for c in chars if not is_accented(c)]


@pytest.mark.parametrize("features_name", list(FEATURE_SETS))
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_plain_pairs_keep_30_units(weight, italic, features_name):
    table = PairTable(static_path(weight, italic), FEATURE_SETS[features_name], plain_texts(weight, italic))
    everything = np.arange(len(table.texts))
    kern = table.kerning(everything, everything)
    gap = table.gaps(everything, everything, kern)
    xs, ys = np.nonzero((gap < FLOOR) & ~np.isnan(kern))
    tight = [found for x, y in zip(xs, ys) if (found := plain_violation(table.texts[x], table.texts[y], gap[x, y]))]
    assert tight == []
