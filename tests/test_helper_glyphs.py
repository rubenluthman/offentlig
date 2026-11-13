"""Drawing helpers used as components in the sources are not shipped: no built font contains them."""
import pytest
from fontTools.ttLib import TTFont

from conftest import BUILD

# Source names of the helpers; the built fonts would name the `_j-hook` helper `_jhook`.
HELPERS = {"__horn", "espaciador", "_ringacute", "_jhook", "_j-hook", "_dot", "_emdash", "_hook.C", "_hook.c"}
FILES = sorted(p for kind in ("ttf", "otf", "variable", "webfonts") for p in (BUILD / kind).iterdir() if p.suffix in (".ttf", ".otf", ".woff2"))


def test_the_build_has_every_kind_of_font():
    assert {p.parent.name for p in FILES} == {"ttf", "otf", "variable", "webfonts"}


@pytest.mark.parametrize("path", FILES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_no_helper_glyph_is_in_a_built_font(path):
    assert HELPERS & set(TTFont(path).getGlyphOrder()) == set()
