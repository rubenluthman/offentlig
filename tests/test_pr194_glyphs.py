"""Glyphs ported from public-sans pull request #194: capital sharp s and Black 5; tabular 1 stays as drawn."""
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen

from conftest import static_path


def decomposed_points(font, glyph_name):
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[glyph_name].draw(pen)
    return [pt for _, args in pen.value for pt in args]


def advances(path, text, features, wght=None):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    if wght is not None:
        font.set_variations({"wght": wght})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [p.x_advance for p in buf.glyph_positions]


def test_capital_sharp_s_is_mapped_and_about_as_wide_as_h(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert cmap[0xDF] == "germandbls"
    hmtx = static_ttf["hmtx"]
    ratio = hmtx[cmap[0x1E9E]][0] / hmtx["H"][0]
    assert 0.95 <= ratio <= 1.06, ratio


def test_capital_sharp_s_is_one_drawn_outline_with_the_stem_of_h(static_ttf):
    """Not two S glyphs: a single outline whose stem starts where the stem of H starts and rises to the cap height."""
    from fontTools.pens.boundsPen import BoundsPen
    name = static_ttf.getBestCmap()[0x1E9E]
    assert not static_ttf["glyf"][name].isComposite()
    assert static_ttf["glyf"][name].numberOfContours == 1
    gs = static_ttf.getGlyphSet()
    sharp, h = BoundsPen(gs), BoundsPen(gs)
    gs[name].draw(sharp)
    gs["H"].draw(h)
    assert sharp.bounds[3] >= h.bounds[3]
    assert sharp.bounds[3] <= h.bounds[3] + 40
    assert sharp.bounds[1] <= 0 and sharp.bounds[1] >= -40


def test_capital_sharp_s_is_mapped_in_variable(variable_ttf):
    assert 0x1E9E in variable_ttf.getBestCmap()


def test_tabular_digits_share_one_advance_static(static_ttf):
    hmtx = static_ttf["hmtx"]
    names = "zero one two three four five six seven eight nine".split()
    assert len({hmtx[f"{n}.tf"][0] for n in names}) == 1


def test_tabular_digits_share_one_advance_variable(variable_path):
    for wght in (100, 400, 900):
        adv = advances(variable_path, "0123456789", {"tnum": True}, wght)
        assert len(set(adv)) == 1, (wght, adv)


def test_black_five_has_no_notch_curve():
    """Black 5 joined its diagonal to the bowl through a tiny smooth curve that rendered as a glitch."""
    from fontTools.ttLib import TTFont
    for italic in (False, True):
        font = TTFont(static_path("Black", italic))
        pts = {tuple(round(v) for v in p) for p in decomposed_points(font, "five")}
        assert (440, 586) not in pts and (449, 586) not in pts
