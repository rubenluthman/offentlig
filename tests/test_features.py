"""ss01 swaps g only, ss02 swaps l only, salt swaps both, ss04 swaps d, q and their composites."""
import pytest
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw

from conftest import STATICS, STATIC_IDS, static_path


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


SS04_BASES = ["d", "q", "dcaron", "dcroat", "ddotbelow"]
# Mirror-mismatch floor for b|d and p|q with ss04 on, as a share of the larger letter's ink (approved 2026-11-07).
SS04_MIN_MISMATCH = 0.045
SCALE, CANVAS, ORIGIN = 0.25, (560, 512), (110, 402)


@pytest.mark.parametrize(("weight", "italic"), STATICS, ids=STATIC_IDS)
def test_ss04_glyphs_exist(weight, italic):
    order = set(TTFont(static_path(weight, italic)).getGlyphOrder())
    assert {f"{name}.ss04" for name in SS04_BASES} <= order


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_ss04_maps_only_d_q_and_composites(italic):
    path = static_path("Regular", italic)
    text = "dq\u010f\u0111\u1e0d"
    assert glyphs(path, text, {"ss04": True}) == [f"{name}.ss04" for name in SS04_BASES]
    assert glyphs(path, text, {}) == ["d", "q", "dcaron", "dcroat", "uni1E0D"]
    assert glyphs(path, "bpgl", {"ss04": True}) == ["b", "p", "g", "l"]
    assert glyphs(path, "bpgl", {"salt": True}) == ["b", "p", "g.ss01", "l.ss02"]


class FlatPen(BasePen):
    """Collects contours as polylines, flattening curves."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours, self._current = [], []

    def _moveTo(self, pt):
        self._current = [pt]

    def _lineTo(self, pt):
        self._current.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, 17):
            t = i / 16
            u = 1 - t
            self._current.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                                  u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _closePath(self):
        self.contours.append(self._current)
        self._current = []

    _endPath = _closePath


def mask(font, name, mirror=False, flip=False):
    """Rasterise a glyph; contours combine with XOR, so counters stay open."""
    pen = FlatPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    out = Image.new("1", CANVAS, 0)
    for contour in pen.contours:
        layer = Image.new("1", CANVAS, 0)
        pts = [(ORIGIN[0] + (-x if mirror else x) * SCALE + (CANVAS[0] - 2 * ORIGIN[0] if mirror else 0),
                ORIGIN[1] + (y if flip else -y) * SCALE) for x, y in contour]
        ImageDraw.Draw(layer).polygon(pts, fill=1)
        out = ImageChops.logical_xor(out, layer)
    return out


def ink(img):
    return img.histogram()[-1]


def mismatch(font, left, right):
    """Smallest share of the larger letter's ink that differs once `right` is mirrored and best aligned."""
    a, b = mask(font, left), mask(font, right, mirror=True)
    best = min(ink(ImageChops.logical_xor(a, ImageChops.offset(b, dx, dy)))
               for dx in range(-90, 91, 3) for dy in range(-6, 7, 3))
    return best / max(ink(a), ink(b))


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
@pytest.mark.parametrize(("left", "right"), [("b", "d.ss04"), ("p", "q.ss04")])
def test_ss04_breaks_mirror_symmetry(weight, left, right):
    font = TTFont(static_path(weight, False))
    assert mismatch(font, left, right) >= SS04_MIN_MISMATCH
