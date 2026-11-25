"""A helper capital (`.tk01` - `.tk03`) kerns with the glyph before it exactly like its capital.

`calt` and `rclt` swap a capital for a helper after the letter before it was placed, so a helper that lacks one of the
glyph-to-glyph exceptions of its capital moves the letter in front of it (`éÝö`, `@Ťö`). Checked on the sources with
the kerning resolved the way a shaper does: glyph pair, glyph and group, group and glyph, group pair.
"""
import re

import pytest
import ufoLib2

from test_spacing import MASTERS, source

HELPER = re.compile(r"\.(tk\d\d)$")


def _groups(font):
    first, second = {}, {}
    for name, members in font.groups.items():
        for glyph in members:
            if name.startswith("public.kern1."):
                first[glyph] = name
            elif name.startswith("public.kern2."):
                second[glyph] = name
    return first, second


def _kern(font, first_of, second_of, left, right):
    k = font.kerning
    for a in (left, first_of.get(left)):
        for b in (right, second_of.get(right)):
            if a and b and (a, b) in k:
                return k[(a, b)]
    return 0


@pytest.mark.parametrize("master", MASTERS)
def test_helper_capitals_keep_the_left_kerning_of_their_capital(master):
    font = source(master)
    first_of, second_of = _groups(font)
    helpers = {n: HELPER.sub("", n) for n in font.keys() if HELPER.search(n)}
    assert len(helpers) > 90  # the `.tk` helpers only: 99 per master
    # Every glyph that can come before a capital: the glyphs and groups named on the left of a pair.
    lefts = {a for a, _ in font.kerning if not a.startswith("public.")} | set(first_of)
    wrong = []
    for helper, capital in helpers.items():
        assert capital in font, (helper, capital)
        for left in lefts:
            if _kern(font, first_of, second_of, left, helper) != _kern(font, first_of, second_of, left, capital):
                wrong.append((left, helper))
    assert wrong[:10] == []
