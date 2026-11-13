"""Typed accents attach to V v Q q ð þ Þ ŋ ĸ Ə ƒ ɨ ẞ ị and clear them, upright and italic.

These bases had no `top` anchor, so a typed U+0301 stayed at the pen position beside the letter.
"""
import functools
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import static_path
from ink import Polyline, outline_distance

BASES = "VvQqðþÞŋĸƏƒɨẞị"
MARKS = ["́", "̀", "̂", "̃", "̄", "̣"]
CASES = [(w, i) for i in (False, True) for w in ("Thin", "Regular", "Black")]
CASE_IDS = [f"{w}{'-italic' if i else ''}" for w, i in CASES]
MIN_GAP = 40  # font units (2000 per em), the gap the comma-above test asks for


@functools.lru_cache(maxsize=None)
def _load(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    return tt, tt.getGlyphSet(), tt.getGlyphOrder(), hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))


def shape(weight, italic, text, features=None):
    _, _, order, font = _load(weight, italic)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def placed(weight, italic, text):
    _, gs, _, _ = _load(weight, italic)
    out, x = [], 0
    for name, adv, dx, dy in shape(weight, italic, text):
        poly = Polyline(gs)
        gs[name].draw(TransformPen(poly, (1, 0, 0, 1, x + dx, dy)))
        out.append(poly.contours)
        x += adv
    return out


def sequences():
    for base in BASES:
        for mark in MARKS:
            if base == "ị" and mark == "\u0323":
                continue  # a second dot below the dot below
            yield base + mark


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("seq", list(sequences()))
def test_mark_attaches_and_clears_base_and_next_letter(weight, italic, seq):
    with_mark = shape(weight, italic, seq)
    without = shape(weight, italic, seq, {"mark": False, "mkmk": False})
    assert len(with_mark) == len(without) == 2, with_mark
    assert with_mark[1][2:] != without[1][2:], f"{seq!r}: the mark is not positioned by GPOS"
    glyphs = placed(weight, italic, seq)
    assert outline_distance(glyphs[0], glyphs[1]) >= MIN_GAP, f"{seq!r} touches its base"
    if seq[0] in "ɨị" and seq[1] != "\u0323":
        # Narrow like ı: a typed top mark can reach the next letter, as typed ı́ does. The precomposed í ĩ ī are drawn
        # wider; typed marks cannot widen the base.
        return
    for nxt in "H":
        g = placed(weight, italic, seq + nxt)
        gap = outline_distance(g[1], g[2])
        assert gap >= MIN_GAP, f"{seq!r} + {nxt!r}: the mark comes within {gap:.0f} units of the next letter"


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("base,dotted", [("ị", "uni1ECB"), ("ɨ", "uni0268")])
@pytest.mark.parametrize("mark", MARKS[:5])
def test_top_mark_drops_the_dot(weight, italic, base, dotted, mark):
    """`i` loses its dot under a top mark; `ị` and `ɨ` do the same and keep their dot below and bar."""
    name = shape(weight, italic, base + mark)[0][0]
    assert name.endswith(".dotless") and name != dotted, name
    assert shape(weight, italic, base)[0][0] == dotted, "without a top mark the dotted letter stays"
    # the dotless form keeps the advance of the dotted letter
    assert shape(weight, italic, base + mark)[0][1] == shape(weight, italic, base)[0][1]


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
def test_typed_dot_below_and_acute_matches_precomposed_i_dot_below(weight, italic):
    assert shape(weight, italic, "ị́") == shape(weight, italic, "ị́")


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
def test_round_dots_follow_the_dotless_dot_below(weight, italic):
    names = [n for n, *_ in shape(weight, italic, "ị́", {"ss03": True})]
    assert names[0] == "idotbelow.dotless.ss03"


def test_nothing_in_the_precomposed_letters_changed():
    assert unicodedata.normalize("NFC", "ị") == "ị"
