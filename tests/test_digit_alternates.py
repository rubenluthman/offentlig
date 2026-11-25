"""The `zero` feature and cv06: the slashed zero and the 1 with a base.

Every digit alternate is opt-in. The default digits, `salt`, `ss01` and `ss02` never reach one. `onum` and a digit
feature work together through the old-style alternates, which sit at x-height like `zero.osf` and `one.osf`. `tnum` and
a digit feature work together on lining tabular figures. With `tnum` and `onum` both on the figures are tabular
old-style (`.tf.osf`); `tests/test_tabular_oldstyle.py` covers those.
"""
import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from conftest import static_path

# feature: (digit -> alternate marker, glyph count per master)
FEATURES = {
    "zero": ({"0": "zero.slash"}, 8),  # lining, tabular, oldstyle, tabular oldstyle, superior, subscript, numerator, denominator
    "cv06": ({"1": "one.cv06"}, 10),  # lining, oldstyle, superior, subscript, numerator, denominator, and the four fractions with a 1
}
ALT_MARKERS = (".cv06", ".slash")
SHAPED = [("Thin", False), ("Regular", False), ("Black", False), ("Thin", True), ("Regular", True), ("Black", True)]
IDS = [f"{w}{'-italic' if i else ''}" for w, i in SHAPED]
DIGITS = "0123456789"


def shape(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def alt_glyphs(ttf):
    return sorted(n for n in ttf.getGlyphOrder() if any(m in n for m in ALT_MARKERS) and n[0] in "oz")


def test_every_alternate_exists_in_every_font(static_ttf):
    names = alt_glyphs(static_ttf)
    for tag, (_, count) in FEATURES.items():
        if count is None:
            continue
        marker = ".slash" if tag == "zero" else "." + tag
        assert len([n for n in names if marker in n]) == count, tag


def test_every_alternate_exists_in_the_variable_fonts(variable_ttf):
    names = alt_glyphs(variable_ttf)
    assert len(names) == 18


def test_alternates_are_not_in_the_default_cmap(static_ttf):
    cmap = set(static_ttf.getBestCmap().values())
    for name in alt_glyphs(static_ttf):
        assert name not in cmap, name


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
@pytest.mark.parametrize("tag", FEATURES)
def test_feature_maps_exactly_its_digits(tag, weight, italic):
    path = static_path(weight, italic)
    mapping, _ = FEATURES[tag]
    for digit in DIGITS:
        off = shape(path, digit, {})
        on = shape(path, digit, {tag: True})
        if digit in mapping:
            assert on == [mapping[digit]], (tag, digit, on)
        else:
            assert on == off, (tag, digit)


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_oldstyle_and_tabular_forms_follow_the_feature(weight, italic):
    path = static_path(weight, italic)
    assert shape(path, "0", {"zero": True, "tnum": True}) == ["zero.slash.tf"]
    assert shape(path, "1", {"cv06": True, "onum": True}) == ["one.cv06.osf"]
    # the tabular 1 already has its own base
    assert shape(path, "1", {"cv06": True, "tnum": True}) == ["one.tf"]


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_defaults_salt_and_stylistic_sets_use_no_digit_alternate(weight, italic):
    path = static_path(weight, italic)
    for features in ({}, {"salt": True}, {"ss01": True, "ss02": True}, {"onum": True}, {"tnum": True}):
        names = shape(path, DIGITS, features)
        assert not any(m in n for n in names for m in ALT_MARKERS), features


def test_one_with_base_is_wider_and_the_zero_keeps_its_width(static_ttf):
    hmtx = static_ttf["hmtx"]
    assert hmtx["one.cv06"][0] > hmtx["one"][0] + 60
    assert hmtx["zero.slash"][0] == hmtx["zero"][0]


def test_features_have_names(static_ttf):
    gsub = static_ttf["GSUB"].table
    tags = {fr.FeatureTag: fr.Feature for fr in gsub.FeatureList.FeatureRecord}
    for tag in ("cv06",):
        params = tags[tag].FeatureParams
        assert params is not None, tag
        assert static_ttf["name"].getName(params.FeatUILabelNameID, 3, 1, 0x409), tag
    assert "zero" in tags


def _bounds(ttf, name):
    glyph = ttf["glyf"][name]
    glyph.recalcBounds(ttf["glyf"])
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def test_zero_slash_osf_sits_at_x_height_like_zero_osf(static_ttf):
    ring = _bounds(static_ttf, "zero.osf")
    slashed = _bounds(static_ttf, "zero.slash.osf")
    lining = _bounds(static_ttf, "zero.slash")
    assert slashed[1] == ring[1] and slashed[3] == ring[3]
    assert slashed[3] < lining[3] * 0.8, "the old-style slashed zero must be an x-height form, not the lining form"
    assert static_ttf["hmtx"]["zero.slash.osf"][0] == static_ttf["hmtx"]["zero.osf"][0]


def test_one_with_base_osf_sits_at_x_height_like_one_osf(static_ttf):
    plain = _bounds(static_ttf, "one.osf")
    based = _bounds(static_ttf, "one.cv06.osf")
    lining = _bounds(static_ttf, "one.cv06")
    assert based[3] == plain[3] and based[1] == 0
    assert based[3] < lining[3] * 0.8, "the old-style 1 with base must be an x-height form, not the lining form"
    assert based[2] - based[0] > plain[2] - plain[0] + 60


def test_old_style_alternates_are_built_on_the_old_style_figures(static_ttf):
    # one.cv06.osf must not be a component of the lining one.cv06
    for name in ("zero.slash.osf", "one.cv06.osf"):
        glyph = static_ttf["glyf"][name]
        assert glyph.numberOfContours != -1, f"{name} is a composite"


# The small figures follow `zero` and `cv06`, so text with either on never mixes two forms of the 0 or the 1 (F-series: the
# superscript and subscript figures, the `frac` numerators and denominators, and the fractions ½ ¼ ⅛ ⅓ that hold a 1).
SMALL = {
    "sups": ("zerosuperior.slash", "onesuperior.cv06"),
    "subs": ("zero.slash.subs", "one.cv06.subs"),
    "sinf": ("zero.slash.subs", "one.cv06.subs"),
    "numr": ("zero.slash.numr", "one.cv06.numr"),
    "dnom": ("zero.slash.dnom", "one.cv06.dnom"),
}
FRACTIONS = {"½": "onehalf", "¼": "onequarter", "⅛": "oneeighth", "⅓": "onethird"}


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
@pytest.mark.parametrize("form", SMALL)
def test_small_figures_follow_zero_and_cv06(form, weight, italic):
    path = static_path(weight, italic)
    zero, one = SMALL[form]
    plain = shape(path, "01", {form: True})
    assert shape(path, "0", {form: True, "zero": True}) == [zero]
    assert shape(path, "1", {form: True, "cv06": True}) == [one]
    # each feature leaves the other figure alone, and each form alone changes nothing without its feature
    assert shape(path, "01", {form: True, "zero": True})[1] == plain[1]
    assert shape(path, "01", {form: True, "cv06": True})[0] == plain[0]
    on = shape(path, "0123456789", {form: True, "zero": True, "cv06": True})
    assert on[0] == zero and on[1] == one and len(on) == 10


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_frac_numerators_and_denominators_follow_zero_and_cv06(weight, italic):
    path = static_path(weight, italic)
    assert shape(path, "10/10", {"frac": True, "zero": True, "cv06": True}) == [
        "one.cv06.numr", "zero.slash.numr", "fraction", "one.cv06.dnom", "zero.slash.dnom"]
    assert shape(path, "10/10", {"frac": True}) == ["one.numr", "zero.numr", "fraction", "one.dnom", "zero.dnom"]


# The built font names the encoded glyphs by code (`uni2153`); the alternates are not encoded and keep their source names.
FRACTION_CODES = {"½": 0xBD, "¼": 0xBC, "⅛": 0x215B, "⅓": 0x2153}


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_precomposed_fractions_follow_cv06_and_leave_the_others(weight, italic):
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    for char, source in FRACTIONS.items():
        plain = cmap[ord(char)]
        assert shape(path, char, {}) == [plain]
        assert shape(path, char, {"cv06": True}) == [source + ".cv06"], char
        assert shape(path, char, {"zero": True}) == [plain], char  # no 0 in these fractions
    for char in "¾⅔⅜⅝⅞":
        assert shape(path, char, {"cv06": True, "zero": True}) == shape(path, char, {}), char


def test_small_one_with_base_is_wider_and_the_slashed_zero_keeps_its_width(static_ttf):
    hmtx, cmap = static_ttf["hmtx"], static_ttf.getBestCmap()
    sup1, sub1, sup0, sub0 = (cmap[c] for c in (0xB9, 0x2081, 0x2070, 0x2080))
    for plain, alt in (("one.numr", "one.cv06.numr"), ("one.dnom", "one.cv06.dnom"), (sub1, "one.cv06.subs"), (sup1, "onesuperior.cv06")):
        assert hmtx[alt][0] > hmtx[plain][0] + 40, alt
    for plain, alt in (("zero.numr", "zero.slash.numr"), ("zero.dnom", "zero.slash.dnom"), (sub0, "zero.slash.subs"), (sup0, "zerosuperior.slash")):
        assert hmtx[alt][0] == pytest.approx(hmtx[plain][0], abs=1), alt  # rounding of interpolated widths
    # a fraction with the new numerator is as much wider as the numerator
    for char, source in FRACTIONS.items():
        plain = cmap[ord(char)]
        assert hmtx[source + ".cv06"][0] - hmtx[plain][0] == pytest.approx(hmtx["one.cv06.numr"][0] - hmtx["one.numr"][0], abs=2), source
