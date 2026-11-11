"""The `zero` feature and cv06: the slashed zero and the 1 with a base.

Every digit alternate is opt-in. The default digits, `salt`, `ss01` and `ss02` never reach one. `onum` and a digit
feature work together through the old-style alternates, which sit at x-height like `zero.osf` and `one.osf`. `tnum` and
a digit feature work together on lining tabular figures. With `tnum` and `onum` both on, `tnum` wins: the font has no
tabular old-style (`.tf.osf`) glyphs, so the figures stay lining and tabular.
"""
import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from conftest import static_path

# feature: (digit -> alternate marker, glyph count per master)
FEATURES = {
    "zero": ({"0": "zero.slash"}, 3),
    "cv06": ({"1": "one.cv06"}, 2),
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
    assert len(names) == 5


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


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_digit_features_with_tnum_and_onum_stay_lining_and_tabular(weight, italic):
    path = static_path(weight, italic)
    assert shape(path, "0", {"zero": True, "tnum": True, "onum": True}) == ["zero.slash.tf"]
    assert shape(path, "1", {"cv06": True, "tnum": True, "onum": True}) == ["one.tf"]


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
