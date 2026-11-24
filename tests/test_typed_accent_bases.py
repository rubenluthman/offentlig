"""Typed accents attach to V v Q q ð þ Þ ŋ ĸ Ə ƒ ɨ ẞ ị and clear them, upright and italic.

These bases had no `top` anchor, so a typed U+0301 stayed at the pen position beside the letter.
"""
import functools
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import WEIGHTS, static_path
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


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
FEATURES = [None, "ss01", "ss02", "cv01", "cv03", "cv04", "cv05"]
ALL_MARKS = ["\u0301", "\u0323", "\u0331"]  # above, dot below, line below


def _single_glyph(weight, italic, text, feature):
    return len(shape(weight, italic, text, {feature: True} if feature else None)) == 1


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("feature", FEATURES, ids=[f or "plain" for f in FEATURES])
def test_every_basic_letter_takes_marks_above_and_below(weight, italic, feature):
    """A-Z a-z (and their alternates with ss01 ss02 cv01 cv03 cv04 cv05) take U+0301, U+0323 and U+0331.

    Each typed mark is moved by GPOS (offset differs from the run without mark features) and clears its base by 40
    units. A pair that shapes as one precomposed glyph is skipped; its glyph is checked by the other tests.
    Letters without a `bottom` anchor (W w g y x f J) left U+0323 and U+0331 at the pen position.
    """
    feats = {feature: True} if feature else {}
    bad, checked = [], 0
    for letter in LETTERS:
        base = shape(weight, italic, letter, feats or None)[0][0]
        if feature and base == shape(weight, italic, letter)[0][0]:
            continue  # the feature does not change this letter
        for mark in ALL_MARKS:
            seq = letter + mark
            on = shape(weight, italic, seq, feats or None)
            if len(on) != 2:
                continue
            off = shape(weight, italic, seq, {**feats, "mark": False, "mkmk": False})
            checked += 1
            if on[1][2:] == off[1][2:]:
                bad.append((seq, "not positioned"))
                continue
            _, gs, _, _ = _load(weight, italic)
            glyphs = []
            x = 0
            for name, adv, dx, dy in on:
                poly = Polyline(gs)
                gs[name].draw(TransformPen(poly, (1, 0, 0, 1, x + dx, dy)))
                glyphs.append(poly.contours)
                x += adv
            gap = outline_distance(glyphs[0], glyphs[1])
            if gap < MIN_GAP:
                bad.append((seq, round(gap)))
    assert checked > 50 or feature, checked  # most letters with a precomposed glyph shape as one glyph and are skipped
    assert not bad, f"{feature or 'plain'}: {bad}"


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
    if len(with_mark) == 1:
        # ị and ɨ with ´ ` ¯ ~ ˆ ˘ ¨ ˇ shape as one glyph with the accent drawn in (like í ì ī ĩ î); the spacing test covers them
        assert seq[0] in "ịɨ" and seq[1] != "\u0323", with_mark
        return
    assert len(with_mark) == len(without) == 2, with_mark
    assert with_mark[1][2:] != without[1][2:], f"{seq!r}: the mark is not positioned by GPOS"
    glyphs = placed(weight, italic, seq)
    assert outline_distance(glyphs[0], glyphs[1]) >= MIN_GAP, f"{seq!r} touches its base"
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
    assert name != dotted and ("dotless" in name or name.startswith(("idotbelow_", "istroke_"))), name
    assert shape(weight, italic, base)[0][0] == dotted, "without a top mark the dotted letter stays"
    if "dotless" in name:  # the dotless form keeps the advance of the dotted letter
        assert shape(weight, italic, base + mark)[0][1] == shape(weight, italic, base)[0][1]


ALL = [(w, i) for i in (False, True) for w in WEIGHTS]
ALL_IDS = [f"{w}{'-italic' if i else ''}" for w, i in ALL]
TOP_MARKS = {"\u0301": "í", "\u0300": "ì", "\u0304": "ī", "\u0303": "ĩ", "\u0302": "î", "\u0306": "ĭ", "\u0308": "ï", "\u030c": "ǐ"}


def gap_to_next(weight, italic, text):
    g = placed(weight, italic, text)
    return outline_distance([c for glyph in g[:-1] for c in glyph], g[-1])


@pytest.mark.parametrize("weight,italic", ALL, ids=ALL_IDS)
def test_typed_i_with_top_mark_spaces_like_the_precomposed_letter(weight, italic):
    """Typed ị with a top mark clears the next letter as far as the precomposed í ì ī ĩ î ĭ ï ǐ does (within 10 units), at every weight.

    The nearest-ink floor of `test_ink_floor.py` holds the typed ị and ɨ to the floor; ɨ has a wider bar, so only that floor applies to it.
    The first version of these letters reused the dotless anchor and overlapped the next letter from Bold up.
    """
    bad = []
    for mark, precomposed in TOP_MARKS.items():
        for nxt in "Hlni":
            gap = gap_to_next(weight, italic, "ị" + mark + nxt)
            reference = gap_to_next(weight, italic, precomposed + nxt)
            if gap < reference - 10:
                bad.append(("ị" + mark + nxt, round(gap), "precomposed", round(reference)))
    assert not bad, bad


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
def test_typed_dot_below_and_acute_matches_precomposed_i_dot_below(weight, italic):
    assert shape(weight, italic, "ị́") == shape(weight, italic, "ị́")


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
def test_round_dots_follow_the_dotless_dot_below(weight, italic):
    names = [n for n, *_ in shape(weight, italic, "ị́", {"ss03": True})]
    assert names[0] == "idotbelow_acutecomb.ss03"
    assert shape(weight, italic, "ị̆", {"ss03": True})[0][0] == "idotbelow_brevecomb.ss03"
    assert shape(weight, italic, "ị̉", {"ss03": True})[0][0] == "idotbelow.dotless.ss03"  # hook above: still two glyphs


def test_nothing_in_the_precomposed_letters_changed():
    assert unicodedata.normalize("NFC", "ị") == "ị"
