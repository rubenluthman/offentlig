"""The dotless ı has the stem and advance of i, and the typed ɨ ị + accent glyphs the advance of the letter they copy."""
import pytest

from conftest import WEIGHTS, static_path
from test_spacing import Shaper

ALL = [(w, i) for i in (False, True) for w in WEIGHTS]
IDS = [f"{w}{'-italic' if i else ''}" for w, i in ALL]
MARKS = {"́": "í", "̀": "ì", "̄": "ī", "̃": "ĩ", "̂": "î", "̆": "ĭ", "̈": "ï", "̌": "ǐ"}


def stem(s, ch):
    gid = s.font.get_nominal_glyph(ord(ch))
    lo, hi = s.spans(gid)[500]
    return hi - lo


def advance(s, text, features=None):
    glyphs = s.shape(text, features, kern=False)
    assert len(glyphs) == 1, text
    return glyphs[0][1]


@pytest.mark.parametrize("weight,italic", ALL, ids=IDS)
def test_dotless_i_matches_i(weight, italic):
    s = Shaper(static_path(weight, italic))
    assert abs(stem(s, "ı") - stem(s, "i")) <= 6  # Regular Italic is 5.5 apart in its own master
    # The light upright and Thin to ExtraLight italic masters space ı narrower than i on purpose (up to 17 units).
    if (italic and WEIGHTS.index(weight) >= WEIGHTS.index("Regular")) or weight in ("ExtraBold", "Black"):
        assert abs(advance(s, "ı") - advance(s, "i")) <= 5


@pytest.mark.parametrize("weight,italic", ALL, ids=IDS)
@pytest.mark.parametrize("features", [None, {"ss03": True}], ids=["default", "ss03"])
def test_typed_accent_ligatures_have_the_precomposed_advance(weight, italic, features):
    s = Shaper(static_path(weight, italic))
    for mark, precomposed in MARKS.items():
        expected = advance(s, precomposed, features)
        for base in "ɨị":
            assert abs(advance(s, base + mark, features) - expected) <= 1, (base, mark)
