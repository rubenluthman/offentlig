"""`tnum` and `onum` together give oldstyle figures on the tabular advance (register F14, F26).

Each `.tf.osf` glyph is the matching `.osf` outline, placed so its ink centre is where the `.tf` figure's ink centre is. The tabular 1 keeps its base
(`one.tf`), so the tabular oldstyle 1 is the oldstyle 1 with a base (`one.cv06.osf`).
"""
import itertools

import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from conftest import static_path

NAMES = "zero one two three four five six seven eight nine".split()
DIGITS = "0123456789"
CELL = 1400
SHAPED = [("Thin", False), ("Regular", False), ("Black", False), ("Thin", True), ("Regular", True), ("Black", True)]
IDS = [f"{w}{'-italic' if i else ''}" for w, i in SHAPED]
# the outline each tabular oldstyle glyph is built from
SOURCE = {f"{n}.tf.osf": f"{n}.osf" for n in NAMES}
SOURCE["one.tf.osf"] = "one.cv06.osf"
SOURCE["zero.slash.tf.osf"] = "zero.slash.osf"


def shape_run(path, text, features, wght=None):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    if wght is not None:
        font.set_variations({"wght": wght})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    names = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    return names, [p.x_advance for p in buf.glyph_positions]


def _ink(tt, name):
    pen = BoundsPen(tt.getGlyphSet())
    tt.getGlyphSet()[name].draw(pen)
    return pen.bounds


def test_tabular_oldstyle_glyphs_share_the_tabular_advance(static_ttf):
    hmtx = static_ttf["hmtx"]
    for name in SOURCE:
        assert hmtx[name][0] == CELL == hmtx["zero.tf"][0], name


def test_tabular_oldstyle_glyphs_keep_the_oldstyle_outline_and_sit_where_the_lining_tabular_figure_sits(static_ttf):
    """The lining `.tf` figures are not centred on the cell (`five.tf` sits 24 units right of centre at Regular):
    upstream placed each one on purpose. `onum` therefore moves no figure sideways: each `.tf.osf` ink has the same
    centre as its `.tf`, and where the two drawings have the same ink width (every figure but 1 and 7, and 0 and 2 in
    the italics) the same left side bearing.

    Measured 2026-11-18: the six masters are within 0.65 units of the `.tf` ink centre (whole-unit offsets plus curve
    conversion). Interpolated statics drift further because offsets and outlines interpolate linearly while the ink
    bounds of a round figure do not; 2 units is 0.14 % of the cell.
    """
    for new, src in SOURCE.items():
        tf = new.replace(".osf", "")
        a, b, t = _ink(static_ttf, new), _ink(static_ttf, src), _ink(static_ttf, tf)
        assert (a[1], a[3]) == (b[1], b[3]), f"{new} moved vertically"
        assert a[2] - a[0] == pytest.approx(b[2] - b[0], abs=1), f"{new} changed width"
        assert (a[0] + a[2]) / 2 == pytest.approx((t[0] + t[2]) / 2, abs=2), new
        if abs((t[2] - t[0]) - (a[2] - a[0])) <= 2:
            assert a[0] == pytest.approx(t[0], abs=2), f"{new} sits {a[0] - t[0]:.1f} units from {tf}"


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
@pytest.mark.parametrize("order", ["tnum onum", "onum tnum"])
def test_tnum_and_onum_in_either_order_give_tabular_oldstyle(weight, italic, order):
    path = static_path(weight, italic)
    features = {tag: True for tag in order.split()}
    names, advances = shape_run(path, DIGITS, features)
    expected = [f"{n}.tf.osf" for n in NAMES]
    assert names == expected
    assert set(advances) == {CELL}


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_shaping_matrix_over_tnum_onum_zero_cv06(weight, italic):
    path = static_path(weight, italic)
    for tnum, onum, zero, cv06 in itertools.product([False, True], repeat=4):
        features = {"tnum": tnum, "onum": onum, "zero": zero, "cv06": cv06}
        names, advances = shape_run(path, "01", features)
        suffix = (".tf" if tnum else "") + (".osf" if onum else "")
        if tnum and onum:
            zero_name = "zero.slash.tf.osf" if zero else "zero.tf.osf"
            one_name = "one.tf.osf"  # the tabular 1 always has its base
        elif tnum:
            zero_name = "zero.slash.tf" if zero else "zero.tf"
            one_name = "one.tf"
        elif onum:
            zero_name = "zero.slash.osf" if zero else "zero.osf"
            one_name = "one.cv06.osf" if cv06 else "one.osf"
        else:
            zero_name = "zero.slash" if zero else "zero"
            one_name = "one.cv06" if cv06 else "one"
        assert names == [zero_name, one_name], (features, names, suffix)
        if tnum:
            assert set(advances) == {CELL}, features


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_other_features_leave_tabular_oldstyle_alone(weight, italic):
    path = static_path(weight, italic)
    base = shape_run(path, "2026", {"tnum": True, "onum": True})[0]
    for tag in ("liga", "kern", "salt", "ss01", "ss02", "ss03"):
        assert shape_run(path, "2026", {"tnum": True, "onum": True, tag: True})[0] == base, tag
    assert shape_run(path, "2026", {"tnum": True, "onum": True, "pnum": False})[0] == base


@pytest.mark.parametrize("wght", [100, 250, 400, 700, 900])
@pytest.mark.parametrize("zero", [False, True])
def test_tabular_oldstyle_advance_is_shared_in_the_variable_fonts(variable_path, wght, zero):
    _, advances = shape_run(variable_path, DIGITS, {"tnum": True, "onum": True, "zero": zero}, wght)
    assert advances == [CELL] * 10, (wght, advances)
