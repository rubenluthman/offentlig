"""Accents typed after T V W Y (and the other capitals of their kern1 groups) stay clear of the capital.

A capital followed by a lowercase base and a grave, macron, tilde, breve or caron with no precomposed form is swapped, in
`rclt`, for a helper capital that draws the same and has its own kerning (ARCHITECTURE.md, "Typed-accent kerning").
The scope is the lowercase sequences of the DIN 91379 combining list in `test_din91379.py`, Yoruba, Igbo and
Lithuanian (docs/design-decisions.md, K19); other typed marks keep the spacing of 0.4.0.
"""
import functools
import io
import plistlib
from pathlib import Path
import re

import pytest
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from conftest import STATICS, STATIC_IDS, static_path
from ink import Polyline, outline_distance
from test_spacing import Shaper

FLOOR = 28  # 30 units in K19, 28 in the row tests (4-unit rows)
FEATURES = {"default": {}, "all": {"cv04": True, "ss03": True, "ss01": True, "ss02": True}}

CAPS = "TŤŦŢȚṪṬṮYÝŶŸẎỴỲỶȲỸVWẂŴẄẆẀ"
DIN = ["k̀", "k̂", "k̄", "k̇", "t̀", "t̄", "ç̆", "ṭ̄", "ḳ̄", "c̨̆", "s̛̄", "l̥̄", "r̥̄", "d̂", "f̀", "f̄", "m̀", "m̂", "m̆",
       "p̀", "p̄", "k̛", "t̛", "c̕", "k̕", "t̕", "p̕", "č̕", "l̥", "r̥", "m̐", "s̱", "p̣", "û̄", "ê̄", "ê̌", "ī́", "ÿ́"]
YORUBA = [b + m for b in "ẹọṣ" for m in "\u0300\u0301\u0304"] + ["m̀", "m̄"]
IGBO = [b + m for b in "ịọụ" for m in "\u0300\u0301\u0304"]
LITHUANIAN = [b + m for b in "ąęįų" for m in "\u0300\u0301\u0303\u0304"] + [b + m for b in "ė" for m in "\u0301\u0303\u0304"]
SCOPE = DIN + YORUBA + IGBO + LITHUANIAN
# U+0300 grave, U+0304 macron, U+0303 tilde, U+0306 breve, U+030C caron: the marks that have helpers
SWAPPED = ("\u0300", "\u0304", "\u0303", "\u0306", "\u030c")
SEQUENCES = [(c, s, f) for s in SCOPE for c in CAPS for f in FEATURES]
SOURCES = Path(__file__).resolve().parent.parent / "sources"
VARIANT = re.compile(r"\.tk\d\d$")


@functools.lru_cache(maxsize=None)
def _font(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    return tt, tt.getGlyphSet(), tt.getGlyphOrder(), Shaper(path)


def _shape(sh, text, features):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(sh.font, buf, dict(features, kern=True))
    x, out = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((info.codepoint, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    return out


def _rows(sh, gid, dx, dy, side):
    rows = {}
    for y, (lo, hi) in sh.spans(gid).items():
        rows[y + dy] = lo + dx if side == "lo" else hi + dx
    return rows


def _gap_and_distance(weight, italic, char, seq, features):
    tt, gs, order, sh = _font(weight, italic)
    glyphs = _shape(sh, char + seq, features)
    cap, mark = glyphs[0], glyphs[-1]
    cap_rows = _rows(sh, cap[0], cap[1], 0, "hi")
    mark_rows = _rows(sh, mark[0], mark[1], mark[2], "lo")
    shared = [y for y in cap_rows if y in mark_rows]
    gap = min((mark_rows[y] - cap_rows[y] for y in shared), default=None)
    distance = None
    if gap is None or gap < 80:
        def contours(g):
            poly = Polyline(gs)
            gs[order[g[0]]].draw(TransformPen(poly, (1, 0, 0, 1, g[1], g[2] if g is mark else 0)))
            return poly.contours

        distance = outline_distance(contours(cap), contours(mark))
    return gap, distance


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_typed_accent_clears_the_capital(weight, italic):
    """Row gap and outline distance between the capital and the last mark are at least 28 units (30 in K19)."""
    tight = []
    for char, seq, features in SEQUENCES:
        shaped = _shape(_font(weight, italic)[3], char + seq, FEATURES[features])
        if len(shaped) < 3:
            continue  # composed into one glyph by this font
        gap, distance = _gap_and_distance(weight, italic, char, seq, FEATURES[features])
        if (gap is not None and gap < FLOOR) or (distance is not None and distance < FLOOR):
            tight.append((char + seq, features, None if gap is None else round(gap), None if distance is None else round(distance)))
    assert tight == []


def _variants(tt):
    return [name for name in tt.getGlyphOrder() if VARIANT.search(name)]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_helper_capitals_draw_exactly_like_their_capital(weight, italic):
    tt, gs, _, _ = _font(weight, italic)
    variants = _variants(tt)
    production = plistlib.loads(SOURCES.joinpath("OffentligSans-Regular.ufo", "lib.plist").read_bytes())["public.postscriptNames"]
    assert len(variants) > 90
    different = []
    for name in variants:
        base = VARIANT.sub("", name)
        base = production.get(base, base)
        a, b = DecomposingRecordingPen(gs), DecomposingRecordingPen(gs)
        gs[name].draw(a)
        gs[base].draw(b)
        if a.value != b.value or gs[name].width != gs[base].width:
            different.append(name)
    assert different == []


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_helper_capitals_are_reachable_only_through_the_swap(italic):
    """Not in cmap, and no feature other than `rclt` mentions one, so copied text holds the plain capitals."""
    tt = TTFont(static_path("Regular", italic))
    variants = set(_variants(tt))
    assert not variants & set(tt.getBestCmap().values())
    gsub = tt["GSUB"].table
    rclt = {i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == "rclt" for i in fr.Feature.LookupListIndex}
    others = {i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag != "rclt" for i in fr.Feature.LookupListIndex}
    assert not (others & rclt)
    for i in sorted(others):
        buf = io.StringIO()
        gsub.LookupList.Lookup[i].toXML(XMLWriter(buf), tt)
        mentioned = {m for m in re.findall(r'"([^"]+\.tk\d\d)"', buf.getvalue())}
        assert not mentioned & variants, (i, sorted(mentioned)[:3])


MASTERS = [(w, i) for i in (False, True) for w in ("Thin", "Regular", "Black")]
MASTER_IDS = [f"{w}{'-italic' if i else ''}" for w, i in MASTERS]


def _names(weight, italic, text, features, language=None):
    tt, _, order, sh = _font(weight, italic)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if language:
        buf.language = language
    hb.shape(sh.font, buf, dict(features, kern=True))
    return [order[i.codepoint] for i in buf.glyph_infos]


def _swapped(weight, italic, seq, features=None, language=None, capital="T"):
    names = _names(weight, italic, capital + seq, features or {}, language)
    return names if len(names) >= 3 and VARIANT.search(names[0]) else None


@pytest.mark.parametrize("feature,marker", [("ss03", ".ss03"), ("cv04", ".cv04")])
def test_the_helper_keeps_the_alternate_forms(feature, marker):
    """With `ss03` or `cv04` on, a swapped sequence keeps the alternate's shape: the helper is the helper of that form.

    No covered sequence has a `g` or an `l` that collides, so `ss01` and `ss02` have no swapped sequence; the clearance
    test runs them with every alternate on.
    """
    seen = 0
    for weight, italic in MASTERS:
        for seq in SCOPE:
            names = _swapped(weight, italic, seq, {feature: True})
            if names and any(marker in n for n in names[1:]):
                seen += 1
    assert seen, feature


@pytest.mark.parametrize("weight,italic", MASTERS, ids=MASTER_IDS)
def test_the_helper_keeps_the_romanian_comma_form(weight, italic):
    """`Ţ` (T with cedilla) becomes the comma form under the Romanian language, and the helper follows it."""
    found = 0
    for seq in SCOPE:
        if not _swapped(weight, italic, seq):
            continue
        names = _swapped(weight, italic, seq, language="ro", capital="Ţ")
        assert names and re.match(r"(Tcommaaccent|uni021A)\.tk\d\d$", names[0]), (seq, names)
        found += 1
    assert found
