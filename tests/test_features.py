"""ss01 swaps g only, ss02 swaps l only, salt swaps both."""
import pytest
import uharfbuzz as hb

from conftest import static_path


def glyphs(path, text, features):
    blob = hb.Blob.from_file_path(str(path))
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_stylistic_sets_split(italic):
    path = static_path("Regular", italic)
    assert glyphs(path, "gl", {"ss01": True}) == ["g.ss01", "l"]
    assert glyphs(path, "gl", {"ss02": True}) == ["g", "l.ss02"]
    assert glyphs(path, "gl", {"salt": True}) == ["g.ss01", "l.ss02"]
    assert glyphs(path, "gl", {}) == ["g", "l"]


TAILED_L = {"l", "fl", "ldot", "ldot.ss03"}
STRAIGHT_L = {"l.ss02", "fl.ss02", "ldot.ss02", "ldot.ss02.ss03"}
L_FEATURES = [{"ss02": True}, {"salt": True}, {"ss02": True, "ss03": True}]
L_IDS = ["ss02", "salt", "ss02+ss03"]


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Bold", "Black"])
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("features", L_FEATURES, ids=L_IDS)
def test_ligature_and_catalan_l_follow_the_straight_l(weight, italic, features):
    """`fl` and the Catalan `ŀ` take the straight `l` with `ss02` and `salt`, so a word never shows both forms."""
    path = static_path(weight, italic)
    for text in ("fl", "\ufb02", "flag"):
        got = glyphs(path, text, features)
        assert not set(got) & TAILED_L, (text, got)
        assert got[0] == "fl.ss02", (text, got)
    got = shaped_catalan(path, features)
    assert not set(got) & TAILED_L, got
    assert got[2] == ("ldot.ss02.ss03" if features.get("ss03") else "ldot.ss02") and got[3] == "l.ss02", got


def shaped_catalan(path, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str("col·legi")
    buf.language = "ca"
    buf.script = "Latn"
    buf.direction = "ltr"
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_ligature_and_catalan_l_are_unchanged_without_ss02(italic):
    path = static_path("Regular", italic)
    assert glyphs(path, "fl", {}) == ["fl"]
    assert glyphs(path, "fl", {"ss01": True}) == ["fl"]
    assert shaped_catalan(path, {})[2:4] == ["ldot", "l"]
    assert shaped_catalan(path, {"ss03": True})[2:4] == ["ldot.ss03", "l"]
