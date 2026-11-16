"""No two glyphs of a pair touch, in every master and at every static.

The pair tests measure the horizontal gap in rows 4 units tall, which cannot see two shapes that meet along a near-vertical edge
or sit one above the other (the diaeresis of `ḯ` on the bar of `Ħ`). `outline_distance` measures the outlines themselves and returns 0
for outlines that cross, share an edge or lie inside each other. Two tests use it: the pairs that touched before they were
kerned, at all 18 statics, and a scan of every pair of encoded characters in the six masters.
"""
import numpy as np
import pytest

from conftest import static_path
from ink import outline_distance, placed_contours
from pairs import PairTable
from test_accent_pairs import encoded_texts
from test_spacing import ALL_FONTS, ALL_IDS, MASTER_FONTS, MASTER_IDS, shaper

MIN_DISTANCE = 30
# Pairs that touched in Regular or Black Italic before their exceptions were fitted, and `ŀ` with `t f ﬁ ﬂ`.
TOUCHING = {
    False: ["ḯĦ", "Ħḯ", "īĦ", "Ħī", "ǐ²", "ǰ²", "ĭ²", "ị̌²", "ɨ̌²", "ŀt", "ŀf", "ŀﬁ", "ŀﬂ"],
    True: ["ŀt", "ŀf", "ŀﬁ", "ŀﬂ", "ïĦ", "Ħï", "ḯĦ", "Ħḯ", "īĦ", "Ħī", "ị̈Ħ", "Ħị̈", "ấǐ", "ếì", "ố¥", "ốǐ", "ốǰ", "ốȅ"],
}
# Pairs with a feature on that were under 30 apart by outline distance, though their row gap passed: `ŀ` with `t f ﬁ ﬂ` under
# `ss02`+`ss03` and `salt`+`ss03`, the diaeresis and macron `i` against `Ħ` under `ss03`, and the doubled daggers at Thin Italic.
FEATURE_PAIRS = (
    [({"ss02": 1, "ss03": 1}, t) for t in ("ŀt", "ŀf", "ŀﬁ", "ŀﬂ")]
    + [({"salt": 1, "ss03": 1}, t) for t in ("ŀt", "ŀf", "ŀﬁ", "ŀﬂ")]
    + [({"ss03": 1}, t) for t in ("ḯĦ", "Ħḯ", "ïĦ", "Ħï", "īĦ", "Ħī")]
    + [({}, t) for t in ("††", "†‡", "‡†", "‡‡")]
)
# Pairs the test leaves alone, each reviewed by the design-decision audit in the ROADMAP: the fraction slash and the figures it
# builds fractions with, and the double grave (Icebox in the ROADMAP).
LEFT_OUT = ("⁄", "ȉ", "ȑ")


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_the_pairs_that_touched_keep_clear(weight, italic):
    close = []
    for text in TOUCHING[italic]:
        glyphs = placed_contours(static_path(weight, italic), text)
        if len(glyphs) == 2:
            d = outline_distance(*glyphs)
            if d < MIN_DISTANCE:
                close.append((text, round(d)))
    assert close == []


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_pairs_with_a_feature_on_keep_clear_by_outline_distance(weight, italic):
    close = []
    for features, text in FEATURE_PAIRS:
        glyphs = placed_contours(static_path(weight, italic), text, features)
        if len(glyphs) == 2 and outline_distance(*glyphs) < MIN_DISTANCE:
            close.append((sorted(features), text, round(outline_distance(*glyphs), 1)))
    assert close == []


def dilated(rows, widest, steps=5):
    """Rows widened by `steps` rows above and below (20 units): shapes that sit one above the other overlap there."""
    out = rows.copy()
    for k in range(1, steps + 1):
        for shifted in (np.roll(rows, k, axis=1), np.roll(rows, -k, axis=1)):
            out = np.maximum(out, shifted) if widest else np.minimum(out, shifted)
    return out


@pytest.mark.parametrize("weight,italic", MASTER_FONTS, ids=MASTER_IDS)
def test_no_two_glyphs_touch_in_the_masters(weight, italic):
    table = PairTable(static_path(weight, italic), {}, encoded_texts(weight, italic), shaper=shaper(weight, italic))
    n = len(table.texts)
    everything = np.arange(n)
    kern = table.kerning(everything, everything)
    lmax = dilated(np.where(np.isfinite(table.lmax), table.lmax, -1e9), True)
    rmin = dilated(np.where(np.isfinite(table.rmin), table.rmin, 1e9), False)
    touching = []
    for a in range(n):
        near = (rmin - lmax[a]).min(axis=1) + table.advance[a] + kern[a]
        for b in np.nonzero(near <= 0)[0]:
            text = table.texts[a] + table.texts[b]
            if np.isnan(kern[a, b]) or any(c in text for c in LEFT_OUT):
                continue
            glyphs = placed_contours(static_path(weight, italic), text)
            if len(glyphs) == 2 and outline_distance(*glyphs) <= 0:
                touching.append(text)
    assert touching == []
