"""The gaps of `T V W Y` and the other capitals of their kern1 groups before `ȑ ȓ`, `ȁ ȅ ȍ ȕ`, `ȃ ȇ ȏ ȗ`, `ȉ` and `ĩ ī ĭ ǐ` (K21, K23).

Floor: no pair is closer than 30 units at any of the 18 statics, with and without `ss03`.

Ceiling: the pairs were fitted to the 40-unit aim, so they stay below the highest gap measured after the fit, plus 6 units. The
ceiling holds the fit at every static, and at Thin and Regular it is the check that a master does not loosen a pair that was
already clear (K6). Where a ceiling is far above 40 (`T` before an accent at Thin) the row gap is measured against the stem,
because the thin arm of `T` shares no ink row with the mark; the real clearance is the outline distance (`tests/ink.py`),
which `test_outline_distance_of_t_before_the_marks_of_i_stays_above_the_fitted_value` holds for `T` before `ĩ ī ĭ ǐ` at Thin and ExtraLight.
"""
import pytest

from conftest import WEIGHTS, static_path
from ink import placed_contours, outline_distance
from pairs import PairTable
from test_spacing import ALL_FONTS, ALL_IDS, source

import numpy as np

FLOOR = 30
FEATURE_SETS = [{}, {"ss03": True}]
GROUPS = {"ȑȓ": "ȑ ȓ", "ȁȅȍȕ": "ȁ ȅ ȍ ȕ", "ȃȇȏȗ": "ȃ ȇ ȏ ȗ", "ȉ": "ȉ", "ĩīĭǐ": "ĩ ī ĭ ǐ"}
# Highest gap of any pair of the group after the fit, plus 6, by weight (Thin to Black). Upright, then italic.
CEILING = {
    ("ȑȓ", False): [61, 61, 61, 61, 60, 61, 59, 59, 62],
    ("ȑȓ", True): [315, 63, 62, 62, 61, 59, 59, 57, 65],
    ("ȁȅȍȕ", False): [66, 56, 63, 70, 65, 61, 54, 46, 41],
    ("ȁȅȍȕ", True): [64, 55, 61, 67, 63, 60, 53, 45, 41],
    ("ȃȇȏȗ", False): [144, 97, 78, 74, 72, 71, 68, 66, 64],
    ("ȃȇȏȗ", True): [351, 166, 133, 103, 86, 74, 67, 65, 65],
    ("ȉ", False): [72, 61, 54, 47, 46, 47, 46, 48, 48],
    ("ȉ", True): [73, 60, 53, 47, 49, 52, 55, 60, 65],
    ("ĩīĭǐ", False): [500, 62, 65, 66, 63, 60, 65, 70, 78],
    ("ĩīĭǐ", True): [446, 72, 80, 111, 100, 90, 78, 62, 53],
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
    too_close, too_open = [], []
    for features in FEATURE_SETS:
        for rights, _ in GROUPS.items():
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
                for c, g in zip(names, gaps):
                    if not np.isfinite(g):
                        continue
                    if g < FLOOR:
                        too_close.append((c + letter, round(float(g)), features))
                    if g > ceiling:
                        too_open.append((c + letter, round(float(g)), ceiling, features))
    assert too_close == []
    assert too_open == []


# Pairs of T V W Y before the marks of `ĩ ī ĭ ǐ` whose outline distance was already under 30 before the fit (measured on the
# 0.8.0 fonts): mostly `ǐ` and the heavy italic, where the mark overhangs the arm diagonally while the row gap reads 30 or
# more, and italic Thin `Tǐ`. Each keeps its value (the test fails if it falls by more than 1 unit) and stays here only while it
# is under 30. Found, not fixed.
OUTLINE_UNDER_FLOOR = {
    ("ExtraBold", False, "Wǐ"): 28,
    ("ExtraBold", False, "Yǐ"): 29,
    ("Black", True, "Tǐ"): 28,
    ("Black", True, "Vĩ"): 27,
    ("Black", True, "Vī"): 27,
    ("Black", True, "Vǐ"): 27,
    ("Black", True, "Wĩ"): 27,
    ("Black", True, "Wī"): 27,
    ("Black", True, "Wǐ"): 27,
    ("Black", True, "Yĩ"): 24,
    ("Black", True, "Yī"): 23,
    ("Black", True, "Yĭ"): 29,
    ("Black", True, "Yǐ"): 27,
    ("Bold", True, "Vǐ"): 28,
    ("Bold", True, "Wǐ"): 26,
    ("Bold", True, "Yī"): 29,
    ("Bold", True, "Yĭ"): 28,
    ("Bold", True, "Yǐ"): 28,
    ("ExtraBold", True, "Vĭ"): 29,
    ("ExtraBold", True, "Vǐ"): 25,
    ("ExtraBold", True, "Wĩ"): 29,
    ("ExtraBold", True, "Wĭ"): 29,
    ("ExtraBold", True, "Wǐ"): 24,
    ("ExtraBold", True, "Yĩ"): 28,
    ("ExtraBold", True, "Yī"): 25,
    ("ExtraBold", True, "Yĭ"): 25,
    ("ExtraBold", True, "Yǐ"): 23,
    ("Regular", True, "Wǐ"): 29,
    ("SemiBold", True, "Vǐ"): 29,
    ("SemiBold", True, "Wǐ"): 28,
    ("SemiBold", True, "Yĭ"): 29,
    ("SemiBold", True, "Yǐ"): 29,
    ("Thin", True, "Tǐ"): 23,
}
OUTLINE_FLOOR = 30


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_outline_distance_of_t_v_w_y_before_the_marks_of_i_keeps_the_floor(weight, italic):
    """The row gap cannot see a mark that passes under the arm of `T` (Thin: the arm ends above the mark, so `Tī` reads the stem,
    362 - 379 units, while the outline distance is 27 - 47). So the outline distance (`tests/ink.py`) is held at 30 or more at all
    18 statics, for `T V W Y` before `ĩ ī ĭ ǐ`, except the pairs in `OUTLINE_UNDER_FLOOR`, which keep their value."""
    path = static_path(weight, italic)
    wrong = []
    for left in "TVWY":
        for letter in "ĩīĭǐ":
            glyphs = placed_contours(path, left + letter)
            distance = outline_distance(glyphs[0], glyphs[1])
            held = OUTLINE_UNDER_FLOOR.get((weight, italic, left + letter))
            if held is None:
                if distance < OUTLINE_FLOOR:
                    wrong.append((left + letter, round(distance)))
            elif not held - 1 <= distance < OUTLINE_FLOOR:
                wrong.append((left + letter, round(distance), "exempt at", held))
    assert wrong == []


# Outline distance of `T` before each mark at Thin and ExtraLight after the fit, less 1. Italic `Tǐ` at Thin (22) was already under 30 and stays as it was.
OUTLINE_MINIMUM = {
    ("Thin", False): {"ĩ": 63, "ī": 46, "ĭ": 50, "ǐ": 38},
    ("Thin", True): {"ĩ": 41, "ī": 30, "ĭ": 34, "ǐ": 22},
    ("ExtraLight", False): {"ĩ": 39, "ī": 39, "ĭ": 39, "ǐ": 39},
    ("ExtraLight", True): {"ĩ": 33, "ī": 40, "ĭ": 39, "ǐ": 40},
}


@pytest.mark.parametrize("weight,italic", list(OUTLINE_MINIMUM), ids=[f"{w}{'-italic' if i else ''}" for w, i in OUTLINE_MINIMUM])
def test_outline_distance_of_t_before_the_marks_of_i_stays_above_the_fitted_value(weight, italic):
    """At Thin the arm of `T` ends above the mark, so the row gap reads the stem; the outline distance is the real clearance."""
    path = static_path(weight, italic)
    short = []
    for letter, minimum in OUTLINE_MINIMUM[(weight, italic)].items():
        glyphs = placed_contours(path, "T" + letter)
        distance = outline_distance(glyphs[0], glyphs[1])
        if distance < minimum:
            short.append(("T" + letter, round(distance), minimum))
    assert short == []
