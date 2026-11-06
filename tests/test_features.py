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
