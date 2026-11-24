"""`ink.fast_distance` gives the numbers of `ink.outline_distance`, which the pair-floor test relies on for speed."""
import random
import unicodedata

import numpy as np
import pytest
import uharfbuzz as hb
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import static_path
from ink import Polyline, fast_distance, outline_distance

CHARS = [c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZåäöéïîôçñ0123456789.,:;!?'\"‘’“”()[]{}-–/&"]


def shaped_contours(tt, gs, font, text):
    order = tt.getGlyphOrder()
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {})
    parts, x = {}, 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        poly = Polyline(gs)
        gs[order[info.codepoint]].draw(TransformPen(poly, (1, 0, 0, 1, x + pos.x_offset, pos.y_offset)))
        parts.setdefault(info.cluster, []).extend(poly.contours)
        x += pos.x_advance
    return parts[0], parts[1]


@pytest.mark.parametrize("weight,italic", [("Thin", False), ("Black", True)])
def test_fast_distance_equals_outline_distance(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    rng = random.Random(7)
    for _ in range(150):
        a, b = shaped_contours(tt, gs, font, rng.choice(CHARS) + rng.choice(CHARS))
        assert fast_distance(a, b) == pytest.approx(outline_distance(a, b), abs=1e-6)


def test_fast_distance_contact_and_containment():
    square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    inner = [(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]
    shifted = [(x + 10, y) for x, y in square]  # shares an edge
    apart = [(x + 13, y) for x, y in square]
    assert fast_distance([square], [shifted]) == 0
    assert fast_distance([square], [inner]) == 0
    assert fast_distance([square], [apart]) == pytest.approx(3)
    assert fast_distance([square], [apart], cap=2) == 2
    assert fast_distance([], [square]) == outline_distance([], [square])
