"""Four small feature and mark fixes, at all 18 statics.

- `sups` also sets the small letters after a raised + − =.
- Turkish `i` with `ss03` has the dot of `i.ss03`.
- `į` loses its dot under a top mark, like every other Soft_Dotted letter in the font.
- `dotbelowcomb` attaches under `j ı ȷ`.
"""
import functools
import math

import pytest
import uharfbuzz as hb
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path
from ink import Polyline

ALL = pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)

# Soft_Dotted code points (Unicode PropList.txt) that the font's cmap covers.
SOFT_DOTTED = "ijįɨị"
TOP_MARKS = ["́", "̀", "̂", "̃", "̄", "̆", "̈", "̌"]


@functools.lru_cache(maxsize=None)
def _load(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    return tt, tt.getGlyphSet(), tt.getGlyphOrder(), hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))


def shape(weight, italic, text, features=None, language=None):
    _, _, order, font = _load(weight, italic)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if language:
        buf.language = language
    hb.shape(font, buf, features or {})
    return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def names(weight, italic, text, **kw):
    return [g[0] for g in shape(weight, italic, text, **kw)]


def contours(weight, italic, name, dx=0, dy=0):
    _, gs, _, _ = _load(weight, italic)
    poly = Polyline(gs)
    gs[name].draw(TransformPen(poly, (1, 0, 0, 1, dx, dy)))
    return poly.contours


def box(contour):
    xs, ys = [p[0] for p in contour], [p[1] for p in contour]
    return min(xs), min(ys), max(xs), max(ys)


@ALL
@pytest.mark.parametrize("sign", ["+", "−", "="])
def test_sups_sets_a_letter_after_a_raised_sign(weight, italic, sign):
    out = names(weight, italic, f"x(n{sign}t)", features={"sups": True})
    assert out[-2] in ("tmod", "uni1D57"), out
    assert "nsuperior" in out, out


@ALL
@pytest.mark.parametrize("text", ["1er", "Ste", "century"])
def test_sups_keeps_letters_in_words(weight, italic, text):
    out = names(weight, italic, text, features={"sups": True})
    assert not any(n.endswith("mod") or n in ("nsuperior", "uni1D57", "uni1D48", "uni02B0", "uni02B3", "uni02E2") for n in out[1:]), out


@ALL
def test_sups_keeps_a_letter_after_hyphen_minus(weight, italic):
    """A hyphen-minus is not a minus sign."""
    assert names(weight, italic, "x(n-t)", features={"sups": True})[-2] == "t"


@ALL
def test_turkish_round_dot_i_has_the_dot_of_i_ss03(weight, italic):
    tr = names(weight, italic, "i", features={"ss03": True}, language="tr")
    assert tr == ["idotaccent.ss03"], tr
    def dot(name):
        return max((box(c) for c in contours(weight, italic, name)), key=lambda b: b[1])
    a, b = dot("idotaccent.ss03"), dot("i.ss03")
    assert abs((a[2] - a[0]) - (b[2] - b[0])) <= 1 and abs((a[3] - a[1]) - (b[3] - b[1])) <= 1, (a, b)
    assert abs(a[1] - b[1]) <= 1, "same height as the dot of i.ss03"


@ALL
def test_round_dot_letters_keep_the_accent_dot(weight, italic):
    """ċ ė ġ ż İ keep the shared accent dot (smaller than the i dot in every weight, as in the default style)."""
    for ch in "ċėġż":
        out = names(weight, italic, ch, features={"ss03": True})
        assert out[0].endswith(".ss03") and "dotaccent" in out[0], out


@ALL
@pytest.mark.parametrize("mark", TOP_MARKS)
@pytest.mark.parametrize("base", list(SOFT_DOTTED))
def test_soft_dotted_letters_lose_the_dot_under_a_top_mark(weight, italic, base, mark):
    out = shape(weight, italic, base + mark)
    # Either a dotless form, or a precomposed letter without a dot (ì ǰ ĵ and so on).
    plain = shape(weight, italic, base)[0][0]
    assert "dotless" in out[0][0] or out[0][0] == "uni0237" or out[0][0].startswith(("idotbelow_", "istroke_")) or (len(out) == 1 and out[0][0] != plain), out
    if base == "į":
        assert out[0][1] == shape(weight, italic, base)[0][1], "the dotless form keeps the advance"


@ALL
def test_iogonek_keeps_its_dot_alone_and_with_a_typed_dot_above(weight, italic):
    assert names(weight, italic, "į") == ["iogonek"]
    assert names(weight, italic, "į́") == ["iogonek.dotless", "acutecomb"]
    # Lithuanian writes U+0307 when the dot is wanted under the accent.
    assert names(weight, italic, "į̇́")[0] == "iogonek.dotless"


@ALL
@pytest.mark.parametrize("base", ["j", "ı", "ȷ"])
def test_dot_below_attaches_under_j_dotless_i_and_dotless_j(weight, italic, base):
    out = shape(weight, italic, base + "̣")
    assert len(out) == 2 and out[1][2:] != (0, 0), out
    _, gs, _, _ = _load(weight, italic)
    pen_x = out[0][1]
    base_c = contours(weight, italic, out[0][0])
    dot = box(contours(weight, italic, out[1][0], pen_x + out[1][2], out[1][3])[0])
    ink = [p for c in base_c for p in c]
    lowest = min(p[1] for p in ink)
    assert dot[3] <= lowest - 20, f"the dot sits {dot[3] - lowest:.0f} units from the base, it should be below it"
    # Marks below follow the 8 degree slant through their anchor in the italic, so bring the dot back to the anchor height.
    centre = (dot[0] + dot[2]) / 2 - ((dot[1] + dot[3]) / 2 - lowest) * math.tan(math.radians(8 if italic else 0))
    low = [p[0] for p in ink if p[1] <= lowest + 1]
    assert min(low) - 15 <= centre <= max(low) + 15, (centre, min(low), max(low))
    if base == "ı":
        assert abs(centre - (min(low) + max(low)) / 2) <= 15, "centred under the stem"
