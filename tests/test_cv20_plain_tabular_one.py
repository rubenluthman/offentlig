"""cv20 swaps the footed tabular 1 for a plain one, and only when tnum is on."""
import pytest
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen

from conftest import static_path


def shaped(path, text, features, wght=None):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    if wght is not None:
        font.set_variations({"wght": wght})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    names = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    return names, [p.x_advance for p in buf.glyph_positions]


def points(font, name):
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    return [pt for _, args in pen.value for pt in args]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_cv20_replaces_only_the_tabular_one(italic):
    path = static_path("Regular", italic)
    names, _ = shaped(path, "1234", {"tnum": True, "cv20": True})
    assert names[0] == "one.tf.cv20" and names[1:] == ["two.tf", "three.tf", "four.tf"]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_cv20_alone_changes_nothing(italic):
    path = static_path("Regular", italic)
    assert shaped(path, "0123456789 1", {"cv20": True}) == shaped(path, "0123456789 1", {})


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_cv20_keeps_the_tabular_advance(italic):
    path = static_path("Regular", italic)
    _, plain = shaped(path, "1111", {"tnum": True})
    _, alt = shaped(path, "1111", {"tnum": True, "cv20": True})
    assert plain == alt


def test_cv20_keeps_the_tabular_advance_variable(variable_path):
    for wght in (100, 400, 900):
        _, plain = shaped(variable_path, "1234", {"tnum": True}, wght)
        _, alt = shaped(variable_path, "1234", {"tnum": True, "cv20": True}, wght)
        assert plain == alt and len(set(alt)) == 1


def test_cv20_is_the_lining_one_shifted(static_ttf):
    lining = points(static_ttf, "one")
    plain = points(static_ttf, "one.tf.cv20")
    assert len(lining) == len(plain)
    shifts = {round(p[0] - l[0], 3) for l, p in zip(lining, plain)}
    assert len(shifts) == 1 and shifts.pop() > 0
    assert [p[1] for p in plain] == [l[1] for l in lining]
    assert static_ttf["hmtx"]["one.tf.cv20"][0] == static_ttf["hmtx"]["one.tf"][0]


def test_cv20_ink_is_centred_in_the_cell(static_ttf):
    """Public Sans PR 194 placed the stem, not the ink, at the cell centre, which left a wide gap after the 1."""
    from fontTools.pens.boundsPen import BoundsPen
    gs = static_ttf.getGlyphSet()
    bp = BoundsPen(gs)
    gs["one.tf.cv20"].draw(bp)
    x0, _, x1, _ = bp.bounds
    adv = static_ttf["hmtx"]["one.tf.cv20"][0]
    assert abs(x0 - (adv - x1)) <= 25
