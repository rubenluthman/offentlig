"""Superscript and subscript signs + - = ( ) (U+207A to U+207E, U+208A to U+208E).

Each is the base sign as a component scaled like the figures (0.629) and raised like them: the superscript sits at the height of a
superscript figure, the subscript at the height of a subscript figure.
"""
import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path

SCALE = 0.629
# The subscript parentheses are lifted by this much above the figure drop, so that Black stays inside winDescent.
PAREN_LIFT = 55
SIGNS = [("+", "plus", 0x207A, 0x208A, "plussuperior"),
         ("−", "minus", 0x207B, 0x208B, "minussuperior"),
         ("=", "equal", 0x207C, 0x208C, "equalsuperior"),
         ("(", "parenleft", 0x207D, 0x208D, "parenleftsuperior"),
         (")", "parenright", 0x207E, 0x208E, "parenrightsuperior")]
IDS = [s[1] for s in SIGNS]


def bounds(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def shaped(path, text, feature):
    hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {feature: True} if feature else {})
    order = TTFont(path).getGlyphOrder()
    return [order[i.codepoint] for i in buf.glyph_infos]


@pytest.mark.parametrize("char,base,usup,usub,supname", SIGNS, ids=IDS)
@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_unicode_and_features_map_to_the_signs(weight, italic, char, base, usup, usub, supname):
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    assert cmap[usup] == supname
    assert cmap[usub] == base + ".subs"
    assert shaped(path, char, "sups") == [supname]
    assert shaped(path, char, "subs") == [base + ".subs"]
    assert shaped(path, char, "sinf") == [base + ".subs"]


@pytest.mark.parametrize("char,base,usup,usub,supname", SIGNS, ids=IDS)
@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_signs_are_scaled_and_raised_like_the_figures(weight, italic, char, base, usup, usub, supname):
    font = TTFont(static_path(weight, italic))
    cmap = font.getBestCmap()
    rise_sup = bounds(font, cmap[0xB9])[1]           # 'one' has a flat foot on the baseline, so this is the raise of a superior figure
    rise_sub = bounds(font, cmap[0x2081])[1]
    ref = bounds(font, base)
    lift = PAREN_LIFT if base.startswith("paren") else 0
    for name, rise in ((supname, rise_sup), (base + ".subs", rise_sub + lift)):
        b = bounds(font, name)
        assert b[1] == pytest.approx(SCALE * ref[1] + rise, abs=3), name
        assert b[3] == pytest.approx(SCALE * ref[3] + rise, abs=3), name
        assert (b[2] - b[0]) == pytest.approx(SCALE * (ref[2] - ref[0]), abs=3), name


@pytest.mark.parametrize("char,base,usup,usub,supname", SIGNS, ids=IDS)
@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_sign_advance_is_narrower_than_the_sign_and_sits_like_a_figure(weight, italic, char, base, usup, usub, supname):
    """Superior and inferior of one sign share an advance, narrower than the sign; the ink sits in it the way the ink of a figure does."""
    font = TTFont(static_path(weight, italic))
    hmtx = font["hmtx"]; cmap = font.getBestCmap()
    assert hmtx[supname][0] == hmtx[base + ".subs"][0]
    assert 0 < hmtx[supname][0] < hmtx[base][0]

    def offset(name):
        xmin, _, xmax, _ = bounds(font, name)
        return (xmin + xmax) / 2 - hmtx[name][0] / 2

    # a raised italic figure leans right of the centre of its advance by about its rise times tan 8 degrees: the sign must lean alike
    assert offset(supname) == pytest.approx(offset(cmap[0xB2]), abs=35)
    assert offset(base + ".subs") == pytest.approx(offset(cmap[0x2082]), abs=35)


@pytest.mark.parametrize("name", ["parenleft.subs", "parenright.subs"])
@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_subscript_parentheses_stay_inside_win_descent(weight, italic, name):
    font = TTFont(static_path(weight, italic))
    assert bounds(font, name)[1] >= -font["OS/2"].usWinDescent
    assert bounds(font, name)[1] >= -480
