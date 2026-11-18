"""Space characters: U+2007 figure space, U+2008 punctuation space, U+2009 thin space and U+202F narrow no-break space.

Each is mapped with a fixed advance in every static and in both variable fonts, has no outline and takes part in no
kerning group, so it never kerns. U+202F is the no-break form: Unicode gives it the line-break class GL, which apps
read from the character, so the font only has to map it.
"""
import pytest
import ufoLib2
from fontTools.ttLib import TTFont

from conftest import BUILD, STATIC_IDS, STATICS, static_path
from test_spacing import MASTERS, SOURCES

# Figure space = the tabular figure advance, thin space and narrow no-break space = a sixth of an em (2000 / 6), as
# Noto Sans. The punctuation space (U+2008) is the width of the period, so it follows the period at every weight.
FIXED = {0x2007: 1400, 0x2009: 333, 0x202F: 333}
SPACES = [0x2007, 0x2008, 0x2009, 0x202F]


def fonts():
    yield from ((id_, TTFont(static_path(w, i))) for (w, i), id_ in zip(STATICS, STATIC_IDS))
    for name in ("OffentligSans[wght].ttf", "OffentligSans-Italic[wght].ttf"):
        yield name, TTFont(BUILD / "variable" / name)


@pytest.mark.parametrize("font", [f for _, f in fonts()], ids=[n for n, _ in fonts()])
def test_the_spaces_are_mapped_with_their_advances_and_no_outline(font):
    cmap, hmtx, glyf = font.getBestCmap(), font["hmtx"], font["glyf"]
    for code in SPACES:
        name = cmap[code]
        assert hmtx[name][0] == FIXED.get(code, hmtx[cmap[0x2E]][0]), hex(code)
        assert glyf[name].numberOfContours == 0, hex(code)


@pytest.mark.parametrize("master", MASTERS)
def test_the_spaces_are_in_no_kerning_group_or_pair(master):
    ufo = ufoLib2.Font.open(SOURCES / f"OffentligSans-{master}.ufo")
    names = {g.name for g in ufo if set(g.unicodes) & set(SPACES)}
    assert len(names) == len(SPACES)
    assert all(g.width == FIXED.get(g.unicodes[0], ufo["period"].width) for g in ufo if g.name in names)
    assert [g for g, members in ufo.groups.items() if names & set(members)] == []
    assert [pair for pair in ufo.kerning if names & set(pair)] == []
