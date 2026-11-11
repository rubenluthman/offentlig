"""cv01, cv03, cv04 and cv05: wider J, round G, single-storey a, I with serifs (cv02 is unused).

Each feature maps exactly its letters (with every accented form), no feature changes default shaping,
and `salt` still swaps only g and l.
"""
import unicodedata

import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from conftest import static_path

# tag -> (base letter, glyphs ending in the tag, encoded letters the feature changes)
# cv01 and cv05 also reach the ligature letter IJ (U+0132); IJ.cv01.cv05 is the glyph for both features on.
FEATURES = {
    "cv01": ("J", 3, 3),
    "cv03": ("G", 5, 5),
    "cv04": ("a", 25, 25),
    "cv05": ("I", 16, 15),
}
LIGATURE = "\u0132"
SHAPED = [("Thin", False), ("Regular", False), ("Black", False), ("Thin", True), ("Regular", True), ("Black", True)]
IDS = [f"{w}{'-italic' if i else ''}" for w, i in SHAPED]


def shape(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def alternates(ttf, tag):
    suffix = "." + tag
    return sorted(n for n in ttf.getGlyphOrder() if n.endswith(suffix))


def test_every_alternate_exists_in_every_font(static_ttf):
    for tag, (_, count, _swapped) in FEATURES.items():
        assert len(alternates(static_ttf, tag)) == count, tag


def test_every_alternate_exists_in_the_variable_fonts(variable_ttf):
    for tag, (_, count, _swapped) in FEATURES.items():
        assert len(alternates(variable_ttf, tag)) == count, tag


def test_alternates_keep_their_base_forms_in_the_default_cmap(static_ttf):
    cmap = static_ttf.getBestCmap()
    for tag in FEATURES:
        for name in alternates(static_ttf, tag):
            assert name not in cmap.values(), f"{name} must be reached through {tag} only"


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
@pytest.mark.parametrize("tag", FEATURES)
def test_feature_maps_exactly_its_letters(tag, weight, italic):
    path = static_path(weight, italic)
    ttf = TTFont(path)
    suffix = "." + tag
    letter, _glyphs, count = FEATURES[tag]
    swapped = set()
    for cp, name in ttf.getBestCmap().items():
        if not (0x41 <= cp <= 0x24F or 0x1E00 <= cp <= 0x1EFF or cp in (0xAA, 0xBA)):
            continue
        off = shape(path, chr(cp), {})
        on = shape(path, chr(cp), {tag: True})
        if on != off:
            # production names can differ from source names (uni0201 vs adblgrave), so compare by suffix
            assert len(on) == 1 and on[0].endswith(suffix), (tag, hex(cp), off, on)
            swapped.add(cp)
    assert swapped, tag
    # only the feature's own letter, with any accent, changes
    bases = {unicodedata.normalize("NFD", chr(cp))[0] for cp in swapped}
    assert bases == ({letter, LIGATURE} if tag in ("cv01", "cv05") else {letter}), tag
    # every alternate glyph is reachable from an encoded letter
    assert len(swapped) == count, (tag, len(swapped))


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_defaults_and_salt_use_no_new_glyph(weight, italic):
    path = static_path(weight, italic)
    ttf = TTFont(path)
    text = "".join(chr(cp) for cp in sorted(ttf.getBestCmap()) if 0x20 < cp < 0x250 or 0x1E00 <= cp <= 0x1EFF)
    for features in ({}, {"salt": True}, {"ss01": True, "ss02": True}):
        names = shape(path, text, features)
        assert not any(".cv0" in n for n in names), features
    assert shape(path, "Jgl", {"salt": True}) == ["J", "g.ss01", "l.ss02"]


def test_wider_j_is_wider_than_j(static_ttf):
    hmtx = static_ttf["hmtx"]
    assert hmtx["J.cv01"][0] > hmtx["J"][0] + 80


def test_features_have_names_and_cv_parameters(static_ttf):
    gsub = static_ttf["GSUB"].table
    tags = {fr.FeatureTag: fr.Feature for fr in gsub.FeatureList.FeatureRecord}
    for tag in FEATURES:
        params = tags[tag].FeatureParams
        assert params is not None, tag
        assert params.FeatUILabelNameID, tag
        assert static_ttf["name"].getName(params.FeatUILabelNameID, 3, 1, 0x409), tag


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_ij_follows_the_j_and_i_features(weight, italic):
    path = static_path(weight, italic)
    assert shape(path, LIGATURE, {}) == ["uni0132"]
    assert shape(path, LIGATURE, {"cv01": True}) == ["uni0132.cv01"]
    assert shape(path, LIGATURE, {"cv05": True}) == ["uni0132.cv05"]
    # either order of lookups gives the same combined glyph
    assert shape(path, LIGATURE, {"cv01": True, "cv05": True}) == ["uni0132.cv01.cv05"]
    # each form is built from the I and J that the single features give, with extra space where serifs crowd the J
    hmtx = TTFont(path)["hmtx"]
    assert hmtx["uni0132.cv01"][0] >= hmtx["I"][0] + hmtx["J.cv01"][0] - 1
    assert hmtx["uni0132.cv05"][0] >= hmtx["I.cv05"][0] + hmtx["J"][0] - 1
    assert hmtx["uni0132.cv01.cv05"][0] >= hmtx["I.cv05"][0] + hmtx["J.cv01"][0] - 1


@pytest.mark.parametrize("ufo", ["Thin", "Regular", "Black"])
def test_italic_cv04_marks_sit_on_the_single_storey_a_anchors(ufo):
    """Each mark of an italic .cv04 composite lands on its anchor of a.cv04, within 10 units."""
    import ufoLib2
    from pathlib import Path

    font = ufoLib2.Font.open(Path(__file__).resolve().parent.parent / "sources" / f"OffentligSans-{ufo}Italic.ufo")

    def anchors(name):
        return {a.name: (a.x, a.y) for a in font[name].anchors}

    bad = []
    for glyph in font:
        if not glyph.name.endswith(".cv04") or len(glyph.components) < 2 or glyph.contours:
            continue
        base = glyph.components[0]
        base_anchors = anchors(base.baseGlyph)
        for comp in glyph.components[1:]:
            mark_anchors = anchors(comp.baseGlyph)
            attach = [k for k in mark_anchors if k.startswith("_")]
            if not attach or attach[0][1:] not in base_anchors:
                continue
            bx, by = base_anchors[attach[0][1:]]
            mx, my = mark_anchors[attach[0]]
            dx = comp.transformation[4] - (bx + base.transformation[4] - mx)
            dy = comp.transformation[5] - (by + base.transformation[5] - my)
            if abs(dx) > 10 or abs(dy) > 10:
                bad.append((glyph.name, comp.baseGlyph, round(dx), round(dy)))
    assert not bad, bad


# --- spacing of the serifed I (cv05) ------------------------------------------------------------------

INK_ROW = 2  # font units (per 1000 em) per raster row


def _ink_rows(ttf, name, cache):
    """Left and right ink edge per raster row of a glyph, in units per 1000 em (None for an empty row)."""
    if (id(ttf), name) in cache:
        return cache[(id(ttf), name)]
    from fontTools.pens.basePen import BasePen
    from PIL import Image, ImageChops, ImageDraw

    class Flatten(BasePen):
        def __init__(self, glyph_set):
            super().__init__(glyph_set)
            self.contours, self.cur = [], []

        def _moveTo(self, pt):
            self.cur = [pt]

        def _lineTo(self, pt):
            self.cur.append(pt)

        def _curveToOne(self, a, b, c):
            p0 = self._getCurrentPoint()
            for i in range(1, 9):
                t = i / 8
                u = 1 - t
                self.cur.append(tuple(u**3 * p0[k] + 3 * u * u * t * a[k] + 3 * u * t * t * b[k] + t**3 * c[k] for k in (0, 1)))

        def _qCurveToOne(self, a, b):
            p0 = self._getCurrentPoint()
            for i in range(1, 9):
                t = i / 8
                u = 1 - t
                self.cur.append(tuple(u * u * p0[k] + 2 * u * t * a[k] + t * t * b[k] for k in (0, 1)))

        def _closePath(self):
            if len(self.cur) > 2:
                self.contours.append(self.cur)
            self.cur = []

    glyph_set = ttf.getGlyphSet()
    pen = Flatten(glyph_set)
    glyph_set[name].draw(pen)
    scale = 1000 / ttf["head"].unitsPerEm
    lo, hi, left = -300, 1100, 500
    width, height = int(3000 / INK_ROW), int((hi - lo) / INK_ROW)
    mask = Image.new("1", (width, height), 0)
    for contour in pen.contours:  # contours do not overlap, so XOR gives the nonzero fill
        layer = Image.new("1", (width, height), 0)
        ImageDraw.Draw(layer).polygon(
            [((x * scale + left) / INK_ROW, (hi - y * scale) / INK_ROW) for x, y in contour], fill=1)
        mask = ImageChops.logical_xor(mask, layer)
    data = mask.convert("L").tobytes()
    rows = []
    for r in range(height):
        row = data[r * width:(r + 1) * width]
        first = row.find(b"\xff")
        rows.append((first * INK_ROW - left, (row.rfind(b"\xff") + 1) * INK_ROW - left) if first >= 0 else None)
    cache[(id(ttf), name)] = rows
    return rows


def _pair_gap(path, ttf, text, features, cache):
    """Closest horizontal distance between the ink of two shaped letters, kerning applied, per 1000 em."""
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    (a, b), pos = buf.glyph_infos, buf.glyph_positions
    scale = 1000 / ttf["head"].unitsPerEm
    left = _ink_rows(ttf, font.glyph_to_string(a.codepoint), cache)
    right = _ink_rows(ttf, font.glyph_to_string(b.codepoint), cache)
    gaps = [pos[0].x_advance * scale + r[0] - l[1] for l, r in zip(left, right) if l and r]
    return min(gaps)


@pytest.mark.parametrize("weight,italic", SHAPED, ids=IDS)
def test_cv05_i_never_touches_a_neighbour_or_sits_tighter_than_the_plain_i(weight, italic):
    """A serifed I next to any letter is never tighter than the plain I there by more than 30 units, and never touches."""
    import string

    path = static_path(weight, italic)
    ttf = TTFont(path)
    cache = {}
    bad = []
    for letter in string.ascii_uppercase + string.ascii_lowercase:
        for text in ("I" + letter, letter + "I"):
            plain = _pair_gap(path, ttf, text, {}, cache)
            serifed = _pair_gap(path, ttf, text, {"cv05": True}, cache)
            if serifed <= 0 or serifed < plain - 30:
                bad.append((text, round(plain), round(serifed)))
    assert not bad, bad
