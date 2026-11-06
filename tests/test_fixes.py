"""The three upstream bug fixes, checked on every static and on the variable fonts."""
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen

from conftest import STATICS, WEIGHTS, static_path

SUBSCRIPTS = range(0x2080, 0x208A)


def outline(font, glyph_name):
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[glyph_name].draw(pen)
    return pen.value


def test_aring_differs_from_aringacute(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert cmap[0xE5] == "aring" and cmap[0x1FB] == "aringacute"
    assert outline(static_ttf, "aring") != outline(static_ttf, "aringacute")


def test_subscript_digits_are_mapped(static_ttf):
    cmap = static_ttf.getBestCmap()
    names = "zero one two three four five six seven eight nine".split()
    for cp, digit in zip(SUBSCRIPTS, names):
        assert cmap.get(cp) == f"{digit}.subs", hex(cp)


def test_subscript_digits_are_mapped_in_variable(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert all(cp in cmap for cp in SUBSCRIPTS)


def shape(path, text, features=None, wght=None):
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    font = hb.Font(face)
    if wght is not None:
        font.set_variations({"wght": wght})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return face, buf


def test_spaced_en_dash_keeps_both_spaces_static(static_ttf):
    path = static_ttf.reader.file.name if hasattr(static_ttf.reader.file, "name") else None
    assert path
    face, buf = shape(path, " – ")
    adv = [p.x_advance for p in buf.glyph_positions]
    hmtx = static_ttf["hmtx"]
    nominal = [hmtx[static_ttf.getGlyphName(i.codepoint)][0] for i in buf.glyph_infos]
    assert adv == nominal


def test_spaced_en_dash_keeps_both_spaces_variable(variable_path):
    for wght in (100, 400, 900):
        face, buf = shape(variable_path, " – ", wght=wght)
        _, nominal_buf = shape(variable_path, " – ", features={"kern": False}, wght=wght)
        assert [p.x_advance for p in buf.glyph_positions] == [p.x_advance for p in nominal_buf.glyph_positions]
