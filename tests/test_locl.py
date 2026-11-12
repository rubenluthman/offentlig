"""`locl` reaches every language it names, not only the last one listed in its lookup."""
import pytest
import uharfbuzz as hb

from conftest import static_path

TURKIC = ["tr", "az", "kk", "tt", "crh"]
ROMANIAN = ["ro", "mo"]


def shape(path, text, language=None):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.script = "Latn"
    if language:
        buf.language = language
    buf.direction = "ltr"
    hb.shape(font, buf, {})
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
class TestLocl:
    @pytest.mark.parametrize("language", TURKIC)
    def test_turkic_languages_get_the_dotted_i(self, weight, italic, language):
        assert shape(static_path(weight, italic), "i", language) == ["i.loclTRK"]

    @pytest.mark.parametrize("language", ROMANIAN)
    def test_romanian_and_moldovan_get_the_comma_letters(self, weight, italic, language):
        path = static_path(weight, italic)
        got = shape(path, "ŞŢşţ", language)
        assert got == shape(path, "ȘȚșț") and got != shape(path, "ŞŢşţ")

    def test_catalan_gets_the_l_dot(self, weight, italic):
        assert shape(static_path(weight, italic), "l·l", "ca")[0] == "ldot"

    @pytest.mark.parametrize("language", [None, "en", "de", "sv"])
    def test_other_languages_are_unchanged(self, weight, italic, language):
        path = static_path(weight, italic)
        assert shape(path, "i", language) == ["i"]
        assert shape(path, "ŞŢşţ", language) != shape(path, "ȘȚșț")
        assert shape(path, "l·l", language) == ["l", "periodcentered", "l"]
