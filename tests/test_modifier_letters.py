"""Prime marks U+2032 – 2034 and the DIN 91379 small letters ʰ ʳ ˢ ᵈ ᵗ ⁿ.

The primes are copies of `primemod`. The letters are drawn small at the size of `ª º` and the superior figures, with stems
as heavy as the stems of `ª`, and the `sups` feature maps h r s d t n to them.
"""
import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path
from ink import Polyline

PRIMES = [(0x2032, "minute", "primemod", 1), (0x2033, "second", "dblprimemod", None), (0x2034, "tripleprime", "primemod", 3)]
LETTERS = [("h", 0x02B0, "hmod"), ("r", 0x02B3, "rmod"), ("s", 0x02E2, "smod"),
           ("d", 0x1D48, "dmod"), ("t", 0x1D57, "tmod"), ("n", 0x207F, "nsuperior")]
SIZE_TOLERANCE = 20      # font units, against the height of ª
STEM_TOLERANCE = 0.10    # share of the stem of ª


def bounds(gs, name):
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def crossings(gs, name, y):
    pl = Polyline(gs)
    gs[name].draw(pl)
    xs = []
    for contour in pl.contours:
        for a, b in zip(contour, contour[1:]):
            if (a[1] - y) * (b[1] - y) < 0:
                xs.append(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
    return sorted(xs)


def shaped(path, text):
    hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"sups": True})
    order = TTFont(path).getGlyphOrder()
    return [order[i.codepoint] for i in buf.glyph_infos]


def test_primes_and_letters_are_mapped_in_every_font(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert [hex(cp) for cp in [p[0] for p in PRIMES] + [l[1] for l in LETTERS] if cp not in cmap] == []


def test_variable_fonts_map_them(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert [hex(cp) for cp in [p[0] for p in PRIMES] + [l[1] for l in LETTERS] if cp not in cmap] == []


def test_primes_are_made_of_the_wedge_of_primemod(static_ttf):
    gs = static_ttf.getGlyphSet()
    cmap = static_ttf.getBestCmap()
    wedge = bounds(gs, cmap[0x2B9])
    for cp, _, base, count in PRIMES:
        name = cmap[cp]
        box = bounds(gs, name)
        assert (box[1], box[3]) == pytest.approx((wedge[1], wedge[3]), abs=1.5), name
        assert box[0] == pytest.approx(wedge[0], abs=1.5), name
    primemod, dblprimemod = cmap[0x2B9], cmap[0x2BA]
    assert gs[cmap[0x2033]].width == gs[dblprimemod].width
    assert bounds(gs, cmap[0x2033]) == pytest.approx(bounds(gs, dblprimemod), abs=1.5)
    assert gs[cmap[0x2032]].width == gs[primemod].width
    # three wedges at the pitch of the two of the double prime
    pitch = bounds(gs, dblprimemod)[2] - wedge[2]
    assert bounds(gs, cmap[0x2034])[2] == pytest.approx(wedge[2] + 2 * pitch, abs=1)


@pytest.mark.parametrize("letter,cp,name", LETTERS, ids=[l[0] for l in LETTERS])
def test_letter_height_matches_the_ordinals(static_ttf, letter, cp, name):
    gs = static_ttf.getGlyphSet()
    ordinal = bounds(gs, "ordfeminine")
    box = bounds(gs, static_ttf.getBestCmap()[cp])
    if letter in "hdt":
        # the ascender of a small ascender letter rises above the ordinals, but its body stands on them
        assert box[3] > ordinal[3] + 100
    else:
        assert box[3] == pytest.approx(ordinal[3], abs=SIZE_TOLERANCE)
    assert box[1] == pytest.approx(ordinal[1], abs=SIZE_TOLERANCE + 12)


@pytest.mark.parametrize("letter,cp,name", [l for l in LETTERS if l[0] in "hndrt"], ids=list("hndrt"))
def test_letter_stem_matches_the_stem_of_the_ordinal(static_ttf, letter, cp, name):
    gs = static_ttf.getGlyphSet()
    xs = crossings(gs, "ordfeminine", 1060)
    reference = xs[-1] - xs[-2]
    # the left stem, below the arch or the crossbar
    # d is measured on its ascender, above the bowl
    ys = crossings(gs, static_ttf.getBestCmap()[cp], 1500 if letter == "d" else 1000)
    stem = ys[1] - ys[0]
    assert stem == pytest.approx(reference, rel=STEM_TOLERANCE), (letter, stem, reference)


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_sups_sets_ordinal_suffixes_and_x_n(weight, italic):
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    smod, tmod, dmod, rmod, hmod, nmod = (cmap[l[1]] for l in [LETTERS[2], LETTERS[4], LETTERS[3], LETTERS[1], LETTERS[0], LETTERS[5]])
    assert shaped(path, "1st") == [cmap[0xB9], smod, tmod]
    assert shaped(path, "2nd") == [cmap[0xB2], nmod, dmod]
    assert shaped(path, "3rd") == [cmap[0xB3], rmod, dmod]
    assert shaped(path, "4th") == [cmap[0x2074], tmod, hmod]
    assert shaped(path, "x(n)")[2] == nmod
