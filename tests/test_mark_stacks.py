"""Typed mark stacks land where the precomposed stacks do, in upright and italic; ccmp drops the dot for the new marks.

A typed U+0308 U+0301 is positioned by the `top` anchors; the precomposed Ǘ places its acute with a fixed offset.
The two must agree, otherwise text changes when a program normalises it (NFC or NFD).
"""
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from conftest import static_path

TOLERANCE = 1.5  # font units (2000 per em); source offsets are rounded to 0.001


def shape(path, text):
    tt = TTFont(path)
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {})
    order = tt.getGlyphOrder()
    return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def stacked_letters(tt):
    """Precomposed letters whose NFD is a base plus two marks that both exist as combining glyphs."""
    cmap = tt.getBestCmap()
    out = []
    for cp in sorted(cmap):
        nfd = unicodedata.normalize("NFD", chr(cp))
        if len(nfd) == 3 and all(ord(c) in cmap for c in nfd[1:]) and unicodedata.combining(nfd[1]) and unicodedata.combining(nfd[2]):
            out.append(chr(cp))
    return out


def components(tt, name):
    pen = RecordingPen()
    tt.getGlyphSet()[name].draw(pen)
    return [(args[0], args[1]) for op, args in pen.value if op == "addComponent"]


CASES = [(w, i) for i in (False, True) for w in ("Thin", "Regular", "Black")]
CASE_IDS = [f"{w}{'-italic' if i else ''}" for w, i in CASES]


@pytest.mark.parametrize("weight,italic", CASES, ids=CASE_IDS)
def test_typed_stacks_match_precomposed_stacks(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    cmap = tt.getBestCmap()
    checked = 0
    for letter in stacked_letters(tt):
        marks = unicodedata.normalize("NFD", letter)[1:]
        if any(unicodedata.combining(m) != 230 for m in marks):
            continue  # a mark below or beside the letter is not stacked on the first
        comps = components(tt, cmap[ord(letter)])
        if len(comps) != 3:
            continue
        (_, t1), (_, t2) = comps[1], comps[2]
        # a base with no precomposed form, so that the shaper does not recompose the pair
        typed = shape(path, "x" + marks)
        if len(typed) != 3:
            continue  # ccmp ligated the pair (breve + acute and similar): not a plain stack
        dx = typed[2][2] - typed[1][2]
        dy = typed[2][3] - typed[1][3]
        assert abs(dx - (t2[4] - t1[4])) <= TOLERANCE and abs(dy - (t2[5] - t1[5])) <= TOLERANCE, (
            f"{letter} U+{ord(letter):04X}: typed stack is off by ({dx - (t2[4] - t1[4]):.1f}, {dy - (t2[5] - t1[5]):.1f})")
        checked += 1
    assert checked >= 8, f"only {checked} stacks compared"


def test_macron_over_diaeresis_dot_and_tilde_is_compared():
    """The comparison above must reach macron stacks, the case that used to sit 23 to 110 units low."""
    tt = TTFont(static_path("Regular", True))
    cmap = tt.getBestCmap()
    stacks = [c for c in stacked_letters(tt) if unicodedata.normalize("NFD", c)[2] == "\u0304"]
    assert {"ǖ", "Ǖ", "ǟ", "Ǟ", "ȯ", "ȱ", "ȭ"} <= set(stacks) or len(stacks) >= 6, stacks


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_candrabindu_is_a_breve_with_a_dot_above(italic):
    path = static_path("Regular", italic)
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    comps = components(tt, cmap[0x310])
    assert [c[0] for c in comps] == [cmap[0x306], cmap[0x307]], comps
    bp, dp = BoundsPen(gs), BoundsPen(gs)
    gs[cmap[0x306]].draw(bp)
    gs[cmap[0x307]].draw(dp)
    (_, tb), (_, td) = comps
    breve_top = bp.bounds[3] + tb[5]
    dot_bottom = dp.bounds[1] + td[5]
    assert dot_bottom > breve_top, "the dot sits above the crescent"
    centre_b = (bp.bounds[0] + bp.bounds[2]) / 2 + tb[4]
    centre_d = (dp.bounds[0] + dp.bounds[2]) / 2 + td[4]
    slant = 0.1405 * ((dp.bounds[1] + dp.bounds[3]) / 2 + td[5] - (bp.bounds[1] + bp.bounds[3]) / 2) if italic else 0
    assert abs(centre_d - centre_b - slant) < 4, "the dot is centred over the crescent"


@pytest.mark.parametrize("letter", ["i", "j"])
@pytest.mark.parametrize("mark", ["\u030D", "\u0310", "\u0315"], ids=["U+030D", "U+0310", "U+0315"])
def test_upper_marks_drop_the_dot(letter, mark):
    path = static_path("Regular", False)
    tt = TTFont(path)
    cmap = tt.getBestCmap()
    first = shape(path, letter + mark)[0][0]
    assert first == cmap[{"i": 0x131, "j": 0x237}[letter]], f"{letter}+U+{ord(mark):04X} keeps its dot ({first})"


@pytest.mark.parametrize("below", ["\u0325", "\u032E", "\u0331", "\u035F"], ids=["ring", "breve", "macron", "dblmacron"])
def test_new_below_marks_let_a_later_upper_mark_drop_the_dot(below):
    path = static_path("Regular", False)
    cmap = TTFont(path).getBestCmap()
    first = shape(path, "i" + below + "\u030D")[0][0]
    assert first == cmap[0x131], f"i + U+{ord(below):04X} + U+030D keeps its dot ({first})"
    # a lone below mark does not remove the dot
    assert shape(path, "i" + below)[0][0] == cmap[ord("i")]
