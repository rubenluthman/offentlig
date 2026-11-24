"""One shape of `î` in every word: the narrow circumflex (`circumflexcomb.narrow`) on `î` and on typed `i`/`ı` + U+0302.

At the heavy weights the full circumflex overhangs the stem and came within 22 – 39 units of its neighbors. A contextual helper form
would show two shapes of `î` in one text, so every `î` uses the narrow accent, drawn at 92 % of the width in the two Black masters
(Thin and Regular are exact copies of `circumflexcomb`). Stacked marks (`ấ`-style ligatures) keep the wide accent.
"""
import pytest
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from conftest import static_path
from test_spacing import ALL_FONTS, ALL_IDS


def outlines(weight, italic, text, features=None):
    """(advance, offset) and the contours of the shaped text, marks placed, as rounded point lists."""
    path = static_path(weight, italic)
    font = TTFont(path)
    glyphs, order = font.getGlyphSet(), font.getGlyphOrder()
    face = hb.Font(hb.Face(path.read_bytes()))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(face, buf, dict(features or {}))
    x, out = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = DecomposingRecordingPen(glyphs)
        glyphs[order[info.codepoint]].draw(pen)
        dx = x + pos.x_offset
        for op, args in pen.value:
            out.append((op, tuple((round(a + dx), round(b + pos.y_offset)) for a, b in args)))
        x += pos.x_advance
    return x, out


@pytest.mark.parametrize("features", [None, {"ss03": True}], ids=["default", "ss03"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_typed_i_and_dotless_i_with_a_circumflex_draw_like_the_precomposed_letter(weight, italic, features):
    ref = outlines(weight, italic, "î", features)
    for typed in ("i\u0302", "\u0131\u0302"):
        adv, got = outlines(weight, italic, typed, features)
        assert adv == ref[0] and len(got) == len(ref[1]), typed
        # a mark's anchor offset rounds to a unit differently from a composed glyph's
        worst = max(abs(a - c) for (o1, p1), (o2, p2) in zip(got, ref[1]) for q, r in zip(p1, p2) for a, c in zip(q, r))
        assert worst <= 1 and [g[0] for g in got] == [g[0] for g in ref[1]], (typed, worst)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_a_stacked_circumflex_keeps_the_wide_accent(weight, italic):
    path = static_path(weight, italic)
    order = TTFont(path).getGlyphOrder()
    face = hb.Font(hb.Face(path.read_bytes()))
    buf = hb.Buffer()
    buf.add_str("\u0131\u0302\u0301")
    buf.guess_segment_properties()
    hb.shape(face, buf, {})
    names = [order[i.codepoint] for i in buf.glyph_infos]
    assert "uni03020301" in names and "circumflexcomb.narrow" not in names, names


@pytest.mark.parametrize("weight,italic", [("Thin", False), ("Thin", True), ("Regular", False), ("Regular", True)], ids=str)
def test_the_light_weights_keep_the_full_circumflex_on_i(weight, italic):
    """Thin and Regular did not change: their narrow accent is an exact copy."""
    path = static_path(weight, italic)
    gs = TTFont(path).getGlyphSet()
    a, b = DecomposingRecordingPen(gs), DecomposingRecordingPen(gs)
    gs["uni0302"].draw(a)
    gs["circumflexcomb.narrow"].draw(b)
    assert a.value == b.value


@pytest.mark.parametrize("weight,italic", [("Black", False), ("Black", True)], ids=str)
def test_the_black_narrow_circumflex_is_92_percent_wide_with_the_same_stroke(weight, italic):
    gs = TTFont(static_path(weight, italic)).getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    w = {}
    for n in ("uni0302", "circumflexcomb.narrow"):
        p = BoundsPen(gs)
        gs[n].draw(p)
        w[n] = p.bounds[2] - p.bounds[0]
    assert w["circumflexcomb.narrow"] / w["uni0302"] == pytest.approx(0.92, abs=0.005)
    # the two flat ends (the stroke width) are as wide as before
    def top_flat(n):
        pen = DecomposingRecordingPen(gs)
        gs[n].draw(pen)
        pts = [a for op, args in pen.value for a in args]
        ymax = max(y for _, y in pts)
        xs = [x for x, y in pts if y == ymax]
        return max(xs) - min(xs)
    assert top_flat("circumflexcomb.narrow") == top_flat("uni0302")
