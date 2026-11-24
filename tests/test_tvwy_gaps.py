"""The gaps of `T V W Y` and the other capitals of their kern1 groups before `ȑ ȓ`, `ȁ ȅ ȍ ȕ`, `ȃ ȇ ȏ ȗ`, `ȉ` and `ĩ ī ĭ ǐ` (K21, K23).

Floor: the nearest-ink floor of `test_ink_floor.py` holds every one of these pairs at all 18 statics, with and without `ss03` and
`cv04` (the tables of pairs left under 30 are gone). The typed `ị̃ ị̄ ɨ̃ ɨ̄` kern exactly like `ĩ ī`.

Ceiling: the pairs were fitted to the aim (the floor of the static plus 10 at the masters), so they stay below the highest gap measured
after the fit, plus 6 units. The ceiling holds the fit at every static, and at Thin and Regular it is the check that a master does
not loosen a pair that was already clear (K6). Where a ceiling is far above the aim (`T` before an accent at Thin) the row gap is
measured against the stem, because the thin arm of `T` shares no ink row with the mark; the real clearance is the outline distance
(`tests/ink.py`), which the floor test measures.
"""
import pytest

from conftest import WEIGHTS, static_path
from pairs import PairTable
from test_spacing import ALL_FONTS, ALL_IDS, source

import numpy as np

FEATURE_SETS = [{}, {"ss03": True}]
# `cv04` swaps `ȃ` and `ȁ` for their single-storey forms (`ainvertedbreve.cv04`, `adblgrave.cv04`), which have their own kerning keys.
CV04_SETS = [{"cv04": True}, {"cv04": True, "ss03": True}]
CV04_GROUPS = ("ȃȇȏȗ", "ȁȅȍȕ")
CV04_CEILING = {}
GROUPS = {"ȑȓ": "ȑ ȓ", "ȁȅȍȕ": "ȁ ȅ ȍ ȕ", "ȃȇȏȗ": "ȃ ȇ ȏ ȗ", "ȉ": "ȉ", "ĩīĭǐ": "ĩ ī ĭ ǐ"}
# Highest gap of any pair of the group after the fit, plus 6, by weight (Thin to Black), over every feature set the test measures
# (`cv04` included). Upright, then italic. The fit aims at the floor of the static plus 10 at each master (K3), so the light
# weights are higher than the 40-unit aim of 0.8.0.
CEILING = {
    ("ȑȓ", False): [105, 85, 83, 80, 77, 74, 69, 63, 62],
    ("ȑȓ", True): [385, 94, 85, 84, 79, 76, 72, 65, 66],
    ("ȁȅȍȕ", False): [74, 72, 72, 71, 66, 62, 58, 54, 49],
    ("ȁȅȍȕ", True): [74, 71, 69, 68, 64, 62, 58, 53, 50],
    ("ȃȇȏȗ", False): [144, 98, 82, 80, 76, 73, 68, 67, 64],
    ("ȃȇȏȗ", True): [352, 166, 133, 114, 100, 91, 79, 74, 78],
    ("ȉ", False): [73, 71, 68, 66, 62, 61, 56, 52, 49],
    ("ȉ", True): [73, 69, 67, 65, 63, 65, 63, 64, 65],
    ("ĩīĭǐ", False): [525, 97, 90, 93, 87, 80, 76, 77, 78],
    ("ĩīĭǐ", True): [496, 86, 85, 111, 101, 91, 78, 63, 58],
}


def left_capitals():
    """Every encoded capital in the kern1 groups of T, V (W sits in it) and Y."""
    font = source("Regular")
    out = []
    for group in ("public.kern1.T", "public.kern1.V", "public.kern1.Y"):
        for name in font.groups[group]:
            if name in font and font[name].unicodes:
                out.append(chr(font[name].unicodes[0]))
    return sorted(set(out))


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_capitals_before_the_double_grave_and_i_marks_keep_their_gap(weight, italic):
    path = static_path(weight, italic)
    lefts = left_capitals()
    too_open = []
    for features in FEATURE_SETS + CV04_SETS:
        for rights, _ in GROUPS.items():
            if features.get("cv04") and rights not in CV04_GROUPS:
                continue
            table = PairTable(path, features, lefts + list(rights))
            idx = table.index
            left = [idx[c] for c in lefts if c in idx]
            names = [c for c in lefts if c in idx]
            for letter in rights:
                if letter not in idx:
                    continue
                kern = table.kerning(left, [idx[letter]])
                gaps = table.gaps(left, [idx[letter]], kern)[:, 0]
                ceiling = CEILING[(rights, italic)][WEIGHTS.index(weight)]
                if features.get("cv04"):
                    ceiling = max(ceiling, CV04_CEILING.get((letter, italic), [0] * 9)[WEIGHTS.index(weight)])
                for c, g in zip(names, gaps):
                    if not np.isfinite(g):
                        continue
                    if features.get("cv04") and letter not in "ȃȁ":
                        continue  # `cv04` changes only `ȃ ȁ`; the others are the default pairs, measured above
                    if g > ceiling:
                        too_open.append((c + letter, round(float(g)), ceiling, features))
    assert too_open == []


TYPED_I = {"ị̃": "ĩ", "ị̄": "ī", "ɨ̃": "ĩ", "ɨ̄": "ī", "ị̏": "ȉ", "ɨ̏": "ȉ"}


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_typed_i_with_tilde_or_macron_kerns_like_the_precomposed_letter(weight, italic):
    """`ị̃ ị̄ ɨ̃ ɨ̄ ị̏ ɨ̏` (typed, shaped to one glyph by `ccmp`) have the advance and side bearing of `ĩ ī ȉ`, so `T V W Y` and the other
    capitals of their kern1 groups kern before them exactly as before `ĩ ī ȉ`, with and without `ss03`."""
    path = static_path(weight, italic)
    lefts = left_capitals()
    wrong = []
    for features in FEATURE_SETS:
        table = PairTable(path, features, lefts + list(TYPED_I) + list(TYPED_I.values()))
        idx = table.index
        names = [c for c in lefts if c in idx]
        left = [idx[c] for c in names]
        for typed, plain in TYPED_I.items():
            assert typed in idx, (typed, "does not shape to one glyph")
            assert table.advance[idx[typed]] == table.advance[idx[plain]], (typed, plain)
            typed_kern = table.kerning(left, [idx[typed]])[:, 0]
            plain_kern = table.kerning(left, [idx[plain]])[:, 0]
            wrong += [(c + typed, k, c + plain, p, features) for c, k, p in zip(names, typed_kern, plain_kern) if k != p]
    assert wrong == []
