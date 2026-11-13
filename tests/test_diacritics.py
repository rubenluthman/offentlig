"""Swedish diacritics: ring weight against the `o`, ring roundness, and italic dot pitch against the upright."""
import pytest
import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from conftest import ROOT, WEIGHTS, static_path


def contour_bounds(font, glyph_name):
    """Bounds (xMin, yMin, xMax, yMax) of every contour of the decomposed glyph."""
    gs = font.getGlyphSet()
    rec = DecomposingRecordingPen(gs)
    gs[glyph_name].draw(rec)
    out, current = [], []
    for op, args in rec.value:
        current.append((op, args))
        if op in ("closePath", "endPath"):
            pen = BoundsPen(gs)
            for o, a in current:
                getattr(pen, o)(*a)
            out.append(pen.bounds)
            current = []
    return out


def ring_and_o(font):
    rings = sorted(contour_bounds(font, "ring"), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    o = sorted(contour_bounds(font, "o"), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    assert len(rings) == 2 and len(o) == 2
    return rings, o


def test_ring_stroke_keeps_pace_with_the_o(static_ttf):
    """The ring stroke stays at least 40 % of the `o` stroke at every weight (0.43 at Black, 0.99 at Thin)."""
    (r_in, r_out), (o_in, o_out) = ring_and_o(static_ttf)
    ring_stroke = ((r_out[2] - r_out[0]) - (r_in[2] - r_in[0])) / 2
    o_stroke = ((o_out[2] - o_out[0]) - (o_in[2] - o_in[0])) / 2
    assert ring_stroke / o_stroke >= 0.40


def test_ring_hole_stays_open(static_ttf):
    """The ring hole is at least as wide as the ring stroke (1.2 times at Black), so the opening does not close at heavy weights."""
    (r_in, r_out), _ = ring_and_o(static_ttf)
    hole = r_in[2] - r_in[0]
    stroke = ((r_out[2] - r_out[0]) - hole) / 2
    assert hole >= 1.0 * stroke


def test_ring_is_round(static_ttf):
    """Outer ring width to height stays between 0.93 and 1.03 (italic is slightly narrower at light weights)."""
    _, (r_out) = ring_and_o(static_ttf)[0]
    ratio = (r_out[2] - r_out[0]) / (r_out[3] - r_out[1])
    assert 0.93 <= ratio <= 1.03


def dot_pitch(font):
    dots = sorted(contour_bounds(font, "dieresis"), key=lambda b: b[0])
    assert len(dots) == 2
    return ((dots[1][0] + dots[1][2]) - (dots[0][0] + dots[0][2])) / 2


@pytest.mark.parametrize("weight", WEIGHTS)
def test_italic_dot_pitch_matches_upright(weight):
    """Centre-to-centre distance of the diaeresis dots is the same in the italic and the upright (within 3 units at 1000 em)."""
    upright = TTFont(static_path(weight, False))
    italic = TTFont(static_path(weight, True))
    scale = 1000 / upright["head"].unitsPerEm
    assert abs(dot_pitch(upright) - dot_pitch(italic)) * scale <= 3


MASTER_WEIGHTS = ["Thin", "Regular", "Black"]


def source_ring_acute(weight, italic):
    """Outer and inner ring contour bounds of `_ringacute` in the source master. The built fonts do not ship the
    helper glyph: it is decomposed into `ǻ` and `Ǻ`, where its outer contour merges with the letter."""
    font = ufoLib2.Font.open(ROOT / "sources" / f"OffentligSans-{weight}{'Italic' if italic else ''}.ufo")
    bounds = sorted((c.bounds for c in font["_ringacute"].contours), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    assert len(bounds) == 2
    return bounds


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", MASTER_WEIGHTS)
def test_ring_with_acute_matches_the_plain_ring(weight, italic):
    """`ǻ` and `Ǻ` draw their ring as part of `_ringacute`; its stroke share of the ring width follows the plain ring's (within 0.04)."""
    font = TTFont(static_path(weight, italic))
    (r_in, r_out), _ = ring_and_o(font)
    plain = 1 - (r_in[2] - r_in[0]) / (r_out[2] - r_out[0])
    bounds = source_ring_acute(weight, italic)
    acute = 1 - (bounds[0][2] - bounds[0][0]) / (bounds[1][2] - bounds[1][0])
    assert abs(plain - acute) <= 0.04
    # Its ring is a little smaller than the plain ring, so its stroke only has to reach 42 % of the `o` stroke (0.45 at Black).
    _, (o_in, o_out) = ring_and_o(font)
    o_stroke = ((o_out[2] - o_out[0]) - (o_in[2] - o_in[0])) / 2
    acute_stroke = ((bounds[1][2] - bounds[1][0]) - (bounds[0][2] - bounds[0][0])) / 2
    assert acute_stroke / o_stroke >= 0.42


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_black_ring_hole_is_at_least_1_2_times_the_stroke(italic):
    """In Black the hole of `_ringacute` is at least 1.2 times the ring stroke, so the opening stays visible at text sizes."""
    bounds = source_ring_acute("Black", italic)
    hole = bounds[0][2] - bounds[0][0]
    stroke = ((bounds[1][2] - bounds[1][0]) - hole) / 2
    assert hole >= 1.2 * stroke
    font = TTFont(static_path("Black", italic))
    ring = sorted(contour_bounds(font, "uni030A"), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    assert len(ring) == 2
    ring_hole = ring[0][2] - ring[0][0]
    assert ring_hole >= 1.2 * (((ring[1][2] - ring[1][0]) - ring_hole) / 2)
