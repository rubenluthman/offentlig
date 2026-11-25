"""The ogonek ends at the `p` descender, fits in `winDescent`, and the `ę` hook ends level with the arm."""
import pytest

from conftest import WEIGHTS

OGONEK_LETTERS = "ąęįųĄĘĮŲǫǭǪǬ̨˛"

# The ogonek ends at the `p` descender (-322) so it clears the ring of `Å` on the next line at the default line spacing: `ą` is drawn at
# -330 in every master. Letters with a lower join (`Į Ų`) and the weights between the masters differ by a few units, and `ę`, whose
# hook is drawn shorter, ends up to 22 units above the descender.
DESCENDER_REACH = 30

# How far the hook of `ę` may end beyond the arm's end, and how far short of it, on-curve points only.
HOOK_OVERSHOOT = 12
HOOK_MIN_REACH = 40


def points(font, name):
    coords, _, flags = font["glyf"][name].getCoordinates(font["glyf"])
    return [(x, y) for (x, y), f in zip(coords, flags) if f & 1]


@pytest.mark.parametrize("char", list(OGONEK_LETTERS))
def test_ogonek_depth(static_ttf, char):
    """Ends at the `p` descender, within 30 units, and inside `winDescent` so line height clips nothing."""
    cmap = static_ttf.getBestCmap()
    low = -min(y for _, y in points(static_ttf, cmap[ord(char)]))
    p_low = -min(y for _, y in points(static_ttf, cmap[ord("p")]))
    assert abs(low - p_low) <= DESCENDER_REACH, f"{char}: {low} against p {p_low}"
    assert low <= static_ttf["OS/2"].usWinDescent


def test_ogonek_ends_at_the_p_descender(static_ttf):
    """`ą` ends within 12 units of -330, 8 below the `p` descender (-322), so its hook does not hang into the ring of `Å` below."""
    cmap = static_ttf.getBestCmap()
    low = min(y for _, y in points(static_ttf, cmap[ord("ą")]))
    assert -330 - 12 <= low <= -330 + 12, low


def test_e_ogonek_hook_ends_at_the_arm(static_ttf):
    """The hook of `ę` hangs under the end of the arm: it does not reach past it, and it is not far short of it."""
    name = static_ttf.getBestCmap()[ord("ę")]
    pts = points(static_ttf, name)
    hook_right = max(x for x, y in pts if y < -45)
    arm_right = max(x for x, y in pts if 0 <= y <= 400)
    assert hook_right <= arm_right + HOOK_OVERSHOOT
    assert hook_right >= arm_right - HOOK_MIN_REACH


ITALIC_HOOK_TOLERANCE = 3


@pytest.mark.parametrize("weight", WEIGHTS)
def test_italic_u_ogonek_hook_is_as_deep_as_the_upright(weight):
    """`Ų` is drawn with its own hook. The italic hook hung 24 units lower than the upright one at Black (8 at Regular), its top edge
    poked out of the bowl, and the `U` `ogonek` anchor sat on the baseline instead of 24 units above it."""
    from conftest import static_path
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.ttLib import TTFont
    low = {}
    for italic in (False, True):
        ttf = TTFont(static_path(weight, italic))
        gs = ttf.getGlyphSet()
        pen = BoundsPen(gs)
        gs[ttf.getBestCmap()[ord("Ų")]].draw(pen)
        low[italic] = pen.bounds[1]
    assert abs(low[True] - low[False]) <= ITALIC_HOOK_TOLERANCE, low


@pytest.mark.parametrize("master", ["Thin", "Regular", "Black"])
def test_italic_u_ogonek_anchor_and_hook_follow_the_upright_in_the_source(master):
    """Along the slant: the hook contour and the `ogonek` anchor of `U` and `Ų` sit at the upright heights (1 unit)."""
    from pathlib import Path
    import ufoLib2
    sources = Path(__file__).resolve().parent.parent / "sources"
    up = ufoLib2.Font.open(sources / f"OffentligSans-{master}.ufo")
    it = ufoLib2.Font.open(sources / f"OffentligSans-{master}Italic.ufo")
    for name in ("U", "Uogonek"):
        a = {x.name: (x.x, x.y) for x in up[name].anchors}["ogonek"]
        b = {x.name: (x.x, x.y) for x in it[name].anchors}["ogonek"]
        assert abs(a[1] - b[1]) <= 1, (name, a, b)
    hook_up, hook_it = up["Uogonek"].contours[0].getBounds(up), it["Uogonek"].contours[0].getBounds(it)
    assert abs(hook_up[1] - hook_it[1]) <= 1 and abs(hook_up[3] - hook_it[3]) <= 1, (hook_up, hook_it)


@pytest.mark.parametrize("master", ["Thin", "Regular", "Black", "ThinItalic", "RegularItalic", "BlackItalic"])
def test_every_u_composite_has_the_ogonek_anchor_of_u(master):
    """A renderer that does not normalize `Ú` + U+0328 attaches the ogonek at the stored anchor of the composite, so it must be where
    `U` has it, in x and in y (1 unit). Regular Italic and Black Italic kept the old anchor on 30 of 31 composites: (745.8, 11.8) and (797, 0)."""
    from pathlib import Path
    import ufoLib2
    font = ufoLib2.Font.open(Path(__file__).resolve().parent.parent / "sources" / f"OffentligSans-{master}.ufo")
    want = {a.name: (a.x, a.y) for a in font["U"].anchors}["ogonek"]
    checked, wrong = 0, []
    for glyph in font:
        if glyph.name == "U" or not glyph.components or glyph.components[0].baseGlyph != "U":
            continue
        have = {a.name: (a.x, a.y) for a in glyph.anchors}.get("ogonek")
        checked += 1
        if have is None or abs(have[0] - want[0]) > 1 or abs(have[1] - want[1]) > 1:
            wrong.append((glyph.name, have, want))
    assert checked >= 25
    assert wrong == []
