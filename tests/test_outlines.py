"""Outline sanity: no glyph reaches beyond the win metrics, and no outline doubles back on itself.

A glyph beyond winAscent or winDescent is clipped on Windows and in some browsers. An on-curve point where the path turns by
more than 170 degrees is a spike: the outline runs out and back along nearly the same line (a point dragged past its neighbour).
"""
import math

import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPointPen
from fontTools.ttLib import TTFont
from fontTools.ufoLib.glifLib import GlyphSet

from conftest import ROOT, STATICS, STATIC_IDS, static_path

MAX_TURN = 170
UFOS = sorted((ROOT / "sources").glob("*.ufo"))


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_every_glyph_stays_within_the_win_metrics(weight, italic):
    font = TTFont(static_path(weight, italic))
    os2 = font["OS/2"]
    glyphs = font.getGlyphSet()
    outside = []
    for name in font.getGlyphOrder():
        pen = BoundsPen(glyphs)
        glyphs[name].draw(pen)
        if pen.bounds is None:
            continue
        _, y_min, _, y_max = pen.bounds
        if y_max > os2.usWinAscent or y_min < -os2.usWinDescent:
            outside.append(f"{name} ({y_min:g} to {y_max:g})")
    assert not outside, f"beyond winAscent {os2.usWinAscent} or winDescent {os2.usWinDescent}: {outside}"


def contours(glyph_set, name):
    pen = RecordingPointPen()
    glyph_set.readGlyph(name, None, pen)
    result, current = [], None
    for op, args, _ in pen.value:
        if op == "beginPath":
            current = []
        elif op == "addPoint":
            (x, y), kind = args[0], args[1]
            current.append((x, y, kind))
        elif op == "endPath":
            result.append(current)
    return result


def sharp_turns(points):
    """On-curve points of a closed contour where the path turns by more than MAX_TURN degrees. Zero-length handles are skipped."""
    n = len(points)
    found = []
    for i, (x, y, kind) in enumerate(points):
        if kind is None:
            continue
        incoming = outgoing = None
        for k in range(1, n):
            px, py, _ = points[(i - k) % n]
            if (px, py) != (x, y):
                incoming = (x - px, y - py)
                break
        for k in range(1, n):
            qx, qy, _ = points[(i + k) % n]
            if (qx, qy) != (x, y):
                outgoing = (qx - x, qy - y)
                break
        if incoming is None or outgoing is None:
            continue
        cos = (incoming[0] * outgoing[0] + incoming[1] * outgoing[1]) / (math.hypot(*incoming) * math.hypot(*outgoing))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        if angle > MAX_TURN:
            found.append(f"point {i} at ({x:g}, {y:g}) turns {angle:.0f} degrees")
    return found


@pytest.mark.parametrize("ufo", UFOS, ids=[u.stem for u in UFOS])
def test_no_on_curve_point_doubles_back(ufo):
    glyph_set = GlyphSet(str(ufo / "glyphs"))
    problems = []
    for name in sorted(glyph_set.keys()):
        for contour in contours(glyph_set, name):
            if not contour or contour[0][2] == "move":  # an open contour has no turn at its ends
                continue
            problems += [f"{name}: {turn}" for turn in sharp_turns(contour)]
    assert not problems, problems
