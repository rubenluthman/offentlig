"""Arrow glyphs ported from uswds/public-sans pull request #252 (Wayne Shih)."""
from fontTools.pens.boundsPen import BoundsPen

ARROWS = {
    0x2190: "leftArrow", 0x2191: "upArrow", 0x2192: "rightArrow", 0x2193: "downArrow",
    0x2196: "northWestArrow", 0x2197: "northEastArrow", 0x2198: "southEastArrow", 0x2199: "southWestArrow",
}
AXIS = (0x2190, 0x2191, 0x2192, 0x2193)
# Vertical centre of the bounding box against `plus`, in font units (2000 per em). The axis
# arrows are drawn on the plus centre line; a diagonal arrow's box centre sits lower in the
# heavy weights because its head is smaller than its tail is long.
AXIS_TOLERANCE = 12
DIAGONAL_TOLERANCE = 70


def bounds(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def centre_y(font, name):
    _, y0, _, y1 = bounds(font, name)
    return (y0 + y1) / 2


def test_arrows_are_mapped(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert {cp: cmap.get(cp) for cp in ARROWS} == ARROWS


def test_arrows_are_mapped_in_variable(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert all(cp in cmap for cp in ARROWS)


def test_arrows_have_outlines_and_advance(static_ttf):
    for name in ARROWS.values():
        assert bounds(static_ttf, name) is not None, name
        assert static_ttf["hmtx"][name][0] == 1446, name


def test_arrows_share_the_plus_centre_line(static_ttf):
    plus = centre_y(static_ttf, "plus")
    for cp, name in ARROWS.items():
        tolerance = AXIS_TOLERANCE if cp in AXIS else DIAGONAL_TOLERANCE
        assert abs(centre_y(static_ttf, name) - plus) <= tolerance, name


def test_horizontal_arrows_mirror_each_other(static_ttf):
    # Same stroke, so the boxes match in height; the shaft and the head swap sides.
    left, right = bounds(static_ttf, "leftArrow"), bounds(static_ttf, "rightArrow")
    assert left[1] == right[1] and left[3] == right[3]
