"""The ogonek reaches the depth of the deepest comparison fonts, fits in `winDescent`, and the `ę` hook ends level with the arm."""
import pytest

OGONEK_LETTERS = "ąęįųĄĘĮŲǫǭǪǬ̨˛"

# Lowest point of the ogonek, in units of 2000 per em. Thin, Regular and Black are drawn at -405, -415 and -425 on `ą`;
# letters with the lowest join (`Į Ų`) and the weights between them add a few units.
MIN_DEPTH = 395
MAX_DEPTH = 460

# How far the hook of `ę` may end beyond the arm's end, and how far short of it, on-curve points only.
HOOK_OVERSHOOT = 12
HOOK_MIN_REACH = 40


def points(font, name):
    coords, _, flags = font["glyf"][name].getCoordinates(font["glyf"])
    return [(x, y) for (x, y), f in zip(coords, flags) if f & 1]


@pytest.mark.parametrize("char", list(OGONEK_LETTERS))
def test_ogonek_depth(static_ttf, char):
    """Deep enough to read as an ogonek next to the descenders, and inside `winDescent` so line height clips nothing."""
    name = static_ttf.getBestCmap()[ord(char)]
    low = -min(y for _, y in points(static_ttf, name))
    assert MIN_DEPTH <= low <= MAX_DEPTH, f"{char}: {low}"
    assert low <= static_ttf["OS/2"].usWinDescent


def test_ogonek_reaches_below_the_descenders(static_ttf):
    """The ogonek is longer than `j`'s hook, not a stub beside it."""
    cmap = static_ttf.getBestCmap()
    j_low = -min(y for _, y in points(static_ttf, cmap[ord("j")]))
    for char in "ąę":
        low = -min(y for _, y in points(static_ttf, cmap[ord(char)]))
        assert low > j_low + 30, char


def test_e_ogonek_hook_ends_at_the_arm(static_ttf):
    """The hook of `ę` hangs under the end of the arm: it does not reach past it, and it is not far short of it."""
    name = static_ttf.getBestCmap()[ord("ę")]
    pts = points(static_ttf, name)
    hook_right = max(x for x, y in pts if y < -45)
    arm_right = max(x for x, y in pts if 0 <= y <= 400)
    assert hook_right <= arm_right + HOOK_OVERSHOOT
    assert hook_right >= arm_right - HOOK_MIN_REACH
