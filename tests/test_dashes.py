"""Em dash spacing: the em dash has the en dash's side bearings, and no feature substitutes it."""
from fontTools.pens.boundsPen import BoundsPen

from test_fixes import shape

EM_DASH = chr(0x2014)


def bearings(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    adv = font["hmtx"][name][0]
    return pen.bounds[0], adv - pen.bounds[2]


def test_em_dash_has_the_en_dash_side_bearings(static_ttf):
    em, en = bearings(static_ttf, "emdash"), bearings(static_ttf, "endash")
    assert all(abs(a - b) <= 1 for a, b in zip(em, en)), (em, en)


def test_em_dash_is_not_substituted(static_ttf):
    assert "emdash.alt" not in static_ttf.getGlyphOrder()
    gsub = static_ttf["GSUB"].table
    assert "calt" not in {r.FeatureTag for r in gsub.FeatureList.FeatureRecord}


def advances(path, text):
    _, buf = shape(path, text)
    return sum(p.x_advance for p in buf.glyph_positions)


def test_em_dash_between_spaces_shapes_the_same_across_run_boundaries(static_ttf):
    """A browser shapes the text before a link as a separate run, so a substitution that needs
    both spaces in one run would change the result."""
    path = static_ttf.reader.file.name
    assert advances(path, f" {EM_DASH} ") == advances(path, f" {EM_DASH}") + advances(path, " ")


MASTER_AM_KERN = {"Thin": -20, "Regular": -26, "Black": -38}
STEM_LETTERS = "mnrphbñńňŕřŗ"


def a_advance(path, following, wght=None):
    _, buf = shape(path, "A" + following, wght=wght)
    return buf.glyph_positions[0].x_advance


def test_a_is_kerned_against_stem_letters_in_masters():
    from conftest import static_path
    for weight, value in MASTER_AM_KERN.items():
        for italic in (False, True):
            path = static_path(weight, italic)
            nominal = a_advance(path, " ")
            for letter in STEM_LETTERS:
                assert a_advance(path, letter) - nominal == value, (weight, italic, letter)


def test_a_n_is_never_tighter_than_a_o():
    """The stem letters have a larger left bearing than o, so the A + n gap is already wider
    than the A + o gap. Kerning n tighter than o would pull them toward the same ink gap."""
    from conftest import static_path
    for weight in MASTER_AM_KERN:
        for italic in (False, True):
            path = static_path(weight, italic)
            for letter in STEM_LETTERS:
                assert a_advance(path, letter) >= a_advance(path, "o"), (weight, italic, letter)


def test_a_n_is_never_tighter_than_a_o_in_variable(variable_path):
    for wght in range(100, 901, 100):
        for letter in STEM_LETTERS:
            assert a_advance(variable_path, letter, wght) >= a_advance(variable_path, "o", wght), (wght, letter)


def test_a_m_is_tighter_than_nominal_in_every_static(static_ttf):
    path = static_ttf.reader.file.name
    assert a_advance(path, "m") < a_advance(path, " ")
    assert a_advance(path, "m") == a_advance(path, "n")


def test_a_m_is_tighter_than_nominal_in_variable(variable_path):
    for wght in (100, 400, 900):
        assert a_advance(variable_path, "m", wght) < a_advance(variable_path, " ", wght)
