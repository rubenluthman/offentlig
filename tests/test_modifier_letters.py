"""Prime marks U+2032 – 2034 and the DIN 91379 small letters ʰ ʳ ˢ ᵈ ᵗ ⁿ.

The primes are copies of `primemod`. The letters are drawn small at the size of `ª º`, with stems as heavy as the stems
of `ª`. They stand on the baseline of the superior figures and have their side bearings in proportion, and the `sups`
feature maps h r s d t n to them only after a superior figure, a superior parenthesis or another small letter.
"""
import math

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import STATIC_IDS, STATICS, static_path
from ink import Polyline

PRIMES = [(0x2032, "minute", "primemod", 1), (0x2033, "second", "dblprimemod", None), (0x2034, "tripleprime", "primemod", 3)]
LETTERS = [("h", 0x02B0, "hmod"), ("r", 0x02B3, "rmod"), ("s", 0x02E2, "smod"),
           ("d", 0x1D48, "dmod"), ("t", 0x1D57, "tmod"), ("n", 0x207F, "nsuperior")]
BASELINE_TOLERANCE = 20  # font units, against the bottom of `onesuperior`
BEARING_RATIO = (0.5, 0.85)  # side bearing of a small letter over that of the full-size letter; the superior figures use 0.49 – 0.74
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
    cmap = static_ttf.getBestCmap()
    ordinal = bounds(gs, "ordfeminine")
    box = bounds(gs, cmap[cp])
    height, reference = box[3] - box[1], ordinal[3] - ordinal[1]
    if letter in "hdt":
        # the ascender of a small ascender letter rises above the ordinals, but its body has their height
        assert height > reference + 100
    else:
        assert height == pytest.approx(reference, abs=SIZE_TOLERANCE + 12)
    figure = bounds(gs, cmap[0xB9])
    assert box[1] == pytest.approx(figure[1], abs=BASELINE_TOLERANCE), "bottom edge against the superior figures"


@pytest.mark.parametrize("letter,cp,name", LETTERS, ids=[l[0] for l in LETTERS])
def test_letter_side_bearings_follow_the_superior_figures(static_ttf, letter, cp, name):
    gs = static_ttf.getGlyphSet()
    cmap = static_ttf.getBestCmap()
    # italic outlines are brought back along the slant, so upright and italic are measured alike
    shear = math.tan(math.radians(-static_ttf["post"].italicAngle))
    shift = static_ttf["OS/2"].sxHeight / 2 * shear

    def bearings(glyph):
        pen = BoundsPen(gs)
        gs[glyph].draw(TransformPen(pen, (1, 0, -shear, 1, shift, 0)))
        return pen.bounds[0], gs[glyph].width - pen.bounds[2]

    small, full = bearings(cmap[cp]), bearings(cmap[ord(letter)])
    for side, (s, f) in zip("lr", zip(small, full)):
        if letter == "t" and side == "l":
            # the bar of t leans out to the left, where the figure before it ends: it keeps at least 40 units
            assert s >= 0.3 * f and s >= 40, (letter, side, s, f)
        elif f >= 40:  # a full-size bearing under 40 (r on the right) says nothing about the ratio
            assert BEARING_RATIO[0] <= s / f <= BEARING_RATIO[1], (letter, side, s, f)


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


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_sups_leaves_ordinary_words_alone(weight, italic):
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    small = {cmap[l[1]] for l in LETTERS}
    for text in ("1er", "Ste", "Mme", "century", "21st century"):
        out = shaped(path, text)
        letters = [g for g in out if g in small]
        # only the st after 21 is set
        assert len(letters) == (2 if text == "21st century" else 0), (text, out)
