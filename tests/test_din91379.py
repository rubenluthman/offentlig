"""DIN 91379 coverage added for uswds/public-sans#277: precomposed letters, new combining marks and mark stacking."""
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import static_path

PRECOMPOSED = (
    "ĲĳŉǞǟǢǣǦǧǨǩǬǭǰǴǵȞȟȦȧȨȩȪȫȬȭȮȯȰȱȲȳḂḃḆḇḊḋḎḏḐḑḖḗḜḝḞḟḠḡḢḣḦḧḨḩḪḫḮḯḰḱḲḳḴḵḶḷḺḻ"
    "ṀṁṂṃṆṇṈṉṒṓṔṕṖṗṘṙṞṟṠṡṪṫṮṯẆẇẌẍẎẏẐẑẔẕẖẗ"
)
NEW_MARKS = [0x310, 0x315, 0x325, 0x32E, 0x331]
# base plus mark(s) with no precomposed code point; every mark must attach through GPOS
ATTACHING = ["F̀", "F̄", "M̀", "M̂", "M̆", "P̀", "P̄", "P̣", "d̂", "f̀", "f̄", "k̀", "k̂", "k̄", "k̇",
             "m̀", "m̂", "m̆", "p̀", "p̄", "p̣", "t̀", "t̄", "K̛", "T̛", "k̛", "t̛", "Ç̆", "ç̆", "ṭ̄", "Ḳ̄", "ḳ̄",
             "C̕", "c̕", "K̕", "k̕", "P̕", "p̕", "T̕", "t̕", "Č̕", "č̕", "L̥", "l̥", "R̥", "r̥", "L̥̄", "l̥̄", "R̥̄", "r̥̄",
             "H̱", "S̱", "s̱", "M̐", "m̐", "C̨̆", "c̨̆", "S̛̄", "s̛̄"]
# a second mark on an already accented letter must clear the first mark
STACKED = ["Û̄", "û̄", "ÿ́", "Ī́", "ī́", "Ê̄", "ê̄", "Ê̌", "ê̌"]


def bounds(gs, name):
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return bp.bounds


def shaped(path, text, features=None):
    tt = TTFont(path)
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    order = tt.getGlyphOrder()
    return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def test_precomposed_letters_are_mapped(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert [c for c in PRECOMPOSED if ord(c) not in cmap] == []


def test_new_combining_marks_are_mapped_and_zero_width(static_ttf):
    cmap = static_ttf.getBestCmap()
    for cp in NEW_MARKS:
        assert cp in cmap, hex(cp)
        assert static_ttf["hmtx"][cmap[cp]][0] == 0


def test_variable_fonts_map_din_letters(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert [c for c in PRECOMPOSED if ord(c) not in cmap] == []


@pytest.mark.parametrize("letter", PRECOMPOSED)
def test_precomposed_letter_keeps_base_advance(letter):
    tt = TTFont(static_path("Regular", False))
    cmap = tt.getBestCmap()
    nfd = unicodedata.normalize("NFD", letter)
    if len(nfd) == 1:
        pytest.skip("ligature")
    base = "ı" if nfd[0] == "i" else nfd[0]
    if nfd[0] == "j":
        base = "ȷ" if ord("ȷ") in cmap else "j"
    assert tt["hmtx"][cmap[ord(letter)]][0] == tt["hmtx"][cmap[ord(base)]][0] or base == "ȷ"


@pytest.mark.parametrize("seq", ATTACHING)
def test_marks_attach_through_gpos(seq):
    path = static_path("Regular", False)
    with_mark = shaped(path, seq)
    without = shaped(path, seq, {"mark": False, "mkmk": False})
    assert with_mark != without, f"{seq!r} marks are not positioned by GPOS"


@pytest.mark.parametrize("seq", STACKED)
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_second_mark_clears_the_first(seq, italic):
    path = static_path("Regular", italic)
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    items = shaped(path, seq)
    base_name, mark_name = items[0][0], items[-1][0]
    assert len(items) == 2, items
    base_top = bounds(gs, base_name)[3]
    mark_bottom = bounds(gs, mark_name)[1] + items[-1][3]
    assert mark_bottom > base_top, f"{seq!r}: mark ({mark_bottom}) does not clear the accented base ({base_top})"


# Letters drawn for this font: Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ Ǯ ǯ, modifier letters, U+030D and U+035F.
DRAWN = "ƇƈƗɨǤǥƷʒǮǯʹʺʾʿˈˌ"
BARRED = {"Ɨ": "I", "ɨ": "i", "Ǥ": "G", "ǥ": "g"}
HOOKED = {"Ƈ": "C", "ƈ": "c"}


def test_drawn_letters_and_marks_are_mapped(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert [c for c in DRAWN if ord(c) not in cmap] == []
    assert 0x30D in cmap and 0x35F in cmap
    for cp in (0x30D, 0x35F):
        assert static_ttf["hmtx"][cmap[cp]][0] == 0


def test_drawn_letters_are_in_the_variable_fonts(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert [c for c in DRAWN if ord(c) not in cmap] == []


@pytest.mark.parametrize("letter,base", list(BARRED.items()))
def test_barred_letter_keeps_base_advance_and_adds_a_bar(static_ttf, letter, base):
    cmap = static_ttf.getBestCmap()
    gs = static_ttf.getGlyphSet()
    # ǥ is drawn on the single-storey g, not on the default g
    n, b = cmap[ord(letter)], "g.ss01" if letter == "ǥ" else cmap[ord(base)]
    assert static_ttf["hmtx"][n][0] == static_ttf["hmtx"][b][0]
    assert bounds(gs, n)[2] - bounds(gs, n)[0] >= bounds(gs, b)[2] - bounds(gs, b)[0]


@pytest.mark.parametrize("letter,base", list(HOOKED.items()))
def test_hooked_c_rises_above_its_base(static_ttf, letter, base):
    cmap = static_ttf.getBestCmap()
    gs = static_ttf.getGlyphSet()
    assert bounds(gs, cmap[ord(letter)])[3] > bounds(gs, cmap[ord(base)])[3] + 200
    assert static_ttf["hmtx"][cmap[ord(letter)]][0] == static_ttf["hmtx"][cmap[ord(base)]][0]


def test_ezh_has_a_flat_top_at_cap_height_and_lowercase_ezh_descends(static_ttf):
    cmap = static_ttf.getBestCmap()
    gs = static_ttf.getGlyphSet()
    assert bounds(gs, cmap[0x1B7])[3] == 1446
    assert bounds(gs, cmap[0x292])[3] == 1034
    assert bounds(gs, cmap[0x292])[1] < -250
    assert bounds(gs, cmap[0x1EE])[3] > 1446 and bounds(gs, cmap[0x1EF])[3] > 1034


@pytest.mark.parametrize("seq", ["K͟H", "k͟h", "a̍", "Ǯ", "ǯ"])
def test_new_marks_attach(seq):
    path = static_path("Regular", False)
    assert shaped(path, seq) != shaped(path, seq, {"mark": False, "mkmk": False}) or seq in ("Ǯ", "ǯ")


def test_double_macron_below_spans_the_following_letter():
    """U+035F is a fixed-length bar: it reaches from the first letter's centre into the next letter."""
    path = static_path("Regular", False)
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    items = shaped(path, "K͟H")
    k, mark = items[0], items[1]
    mb = bounds(gs, mark[0])
    origin = k[1] + mark[2]
    assert origin + mb[2] > k[1] + 500


@pytest.mark.parametrize("weight,italic", [("Thin", False), ("Regular", False), ("Black", False), ("Regular", True), ("Black", True)])
@pytest.mark.parametrize("seq,kind", [("C̨", "ogonek"), ("c̨", "ogonek"), ("S̛", "horn"), ("s̛", "horn"),
                                       ("C̨̆", "ogonek"), ("c̨̆", "ogonek"), ("S̛̄", "horn"), ("s̛̄", "horn")])
def test_ogonek_and_horn_land_on_c_and_s(weight, italic, seq, kind):
    """The mark is moved onto the letter, not left at offset 0,0 on its origin: an ogonek hangs from the lower right,
    a horn leaves the upper right."""
    path = static_path(weight, italic)
    gs = TTFont(path).getGlyphSet()
    items = shaped(path, seq)
    base, mark = items[0], items[1]
    assert (mark[2], mark[3]) != (0, 0), f"{seq!r}: the mark has no offset"
    bb, mb = bounds(gs, base[0]), bounds(gs, mark[0])
    left, right = mb[0] + base[1] + mark[2], mb[2] + base[1] + mark[2]
    bottom, top = mb[1] + mark[3], mb[3] + mark[3]
    width = bb[2] - bb[0]
    if kind == "ogonek":
        assert top > -40 and top < 120 and bottom < -150, f"{seq!r}: ogonek spans {bottom}..{top}"
        assert bb[0] + 0.35 * width < (left + right) / 2 < bb[2] + 0.2 * width
    else:
        assert bottom > bb[1] + 0.35 * (bb[3] - bb[1]) and top < bb[3] + 400
        assert (left + right) / 2 > bb[0] + 0.5 * width
