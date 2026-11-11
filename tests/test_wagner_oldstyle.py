"""onum draws the figures as oldstyle figures with their own outlines, not as the lining figures."""
import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import static_path

OVERSHOOT_TOP = 1054  # top of a round lowercase such as o
SMALL = "012"  # sit between the baseline and x-height
DESCENDING = "34579"  # hang below the baseline from x-height
ASCENDING = "68"  # keep the full figure height
# p, q and y bottom out at -322 to -330; the round bottoms of 3 5 9 overshoot by 20 more.
FLAT_DEPTH = -332  # 4 and 7 end in a flat foot
ROUND_DEPTH = -352  # 3, 5 and 9 end in a curve
ROUND_FEET = "359"


def _shape(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def _bounds(tt, name):
    pen = BoundsPen(tt.getGlyphSet())
    tt.getGlyphSet()[name].draw(pen)
    return pen.bounds


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_oldstyle_heights(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    for digits in (SMALL, DESCENDING, ASCENDING):
        osf = _shape(path, digits, {"onum": True})
        lining = _shape(path, digits, {})
        for d, o, l in zip(digits, osf, lining):
            assert o != l, f"onum leaves {d} unchanged"
            _, ymin, _, ymax = _bounds(tt, o)
            if digits == ASCENDING:
                assert ymax > 1400, f"{o} should ascend, tops at {ymax}"
            else:
                assert ymax <= OVERSHOOT_TOP + 1, f"{o} reaches {ymax}, above x-height"
            if digits == DESCENDING:
                assert ymin < -300, f"{o} should hang below the baseline, bottoms at {ymin}"
                limit = ROUND_DEPTH if d in ROUND_FEET else FLAT_DEPTH
                assert ymin >= limit - 1, f"{o} hangs deeper than p q y, bottoms at {ymin}"
            if digits == SMALL:
                assert ymin >= -25, f"{o} should stay on the baseline, bottoms at {ymin}"


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_oldstyle_four_crossbar_sits_above_the_baseline(weight, italic):
    tt = TTFont(static_path(weight, italic))
    glyph = tt["glyf"]["four.osf"]
    heights = sorted({y for _, y in glyph.getCoordinates(tt["glyf"])[0]})
    assert heights[0] < -300, heights  # the stem foot
    assert heights[1] >= 0, f"the crossbar of four.osf bottoms at {heights[1]}, below the baseline"


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_oldstyle_descent_is_no_deeper_than_p_q_y_in_the_same_font(weight, italic):
    """Measured against the font's own `p q y`: flat feet (4, 7) go no deeper, round feet (3, 5, 9) no more than 25 units deeper (overshoot)."""
    path = static_path(weight, italic)
    tt = TTFont(path)
    pqy = min(_bounds(tt, n)[1] for n in ("p", "q", "y"))
    for d, o in zip(DESCENDING, _shape(path, DESCENDING, {"onum": True})):
        ymin = _bounds(tt, o)[1]
        allowance = 25 if d in ROUND_FEET else 1
        assert ymin >= pqy - allowance, f"{o} bottoms at {ymin}, p q y at {pqy}"
