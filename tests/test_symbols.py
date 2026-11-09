"""Trademark signs at cap height and the Bitcoin sign."""
from fontTools.pens.boundsPen import BoundsPen

from conftest import static_path
from test_fixes import shape

TOLERANCE = 20  # font units; the registered sign overshoots cap height by 20
TABULAR_WIDTH = 1400


def top_of(font, glyph_name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[glyph_name].draw(pen)
    return pen.bounds[3]


def test_trademark_signs_top_out_at_cap_height(static_ttf):
    cmap = static_ttf.getBestCmap()
    cap = static_ttf["OS/2"].sCapHeight
    for cp in (0x2122, 0x2120):
        assert abs(top_of(static_ttf, cmap[cp]) - cap) <= TOLERANCE, hex(cp)


def test_bitcoin_sign_is_mapped(static_ttf):
    assert 0x20BF in static_ttf.getBestCmap()


def test_bitcoin_sign_is_mapped_in_variable(variable_ttf):
    assert 0x20BF in variable_ttf.getBestCmap()


def test_bitcoin_sign_has_a_tabular_form():
    path = static_path("Regular", False)
    plain = shape(path, "\u20bf")[1].glyph_positions[0].x_advance
    tabular = shape(path, "\u20bf", features={"tnum": True})[1].glyph_positions[0].x_advance
    assert plain != TABULAR_WIDTH
    assert tabular == TABULAR_WIDTH
