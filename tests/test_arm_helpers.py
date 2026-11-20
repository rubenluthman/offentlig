"""Shorter-arm capitals (`T.arm`, `Y.arm`) in front of a letter with a tall mark.

`calt` swaps `T` and `Y` (and the capitals built on them) for a copy with a shorter right arm in front of the letters
named below, so the pair can be kerned like the plain pair (`Tö` like `To`) and still keep 30 units from the mark
(ARCHITECTURE.md, "Shorter-arm capitals"; docs/design-decisions.md, K20). Every static, with the alternate forms on and
off.
"""
import io
import plistlib
import re
from functools import lru_cache
from pathlib import Path

import pytest
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTFont

from conftest import STATICS, STATIC_IDS, static_path
from test_spacing import Shaper

FLOOR = 28  # 30 units, less the 4-unit row step of `Shaper.gap`
LOOSER = 70  # the most the arm kerning may be looser than the plain pair, in units (Y before ë ö ō in Black)
ARM = re.compile(r"\.arm$")
SOURCES = Path(__file__).resolve().parent.parent / "sources"
FEATURES = {"default": {}, "all": {"cv04": True, "ss03": True, "ss01": True, "ss02": True}}
# The letters of the `calt` rules: the round letters whose mark the arm of the capital overhangs.
T_LETTERS = "ëöÿŝšȫ"
Y_LETTERS = "àäëöùüÿčēĕěğōŏšžǎǒǖǘǚǜǟǧǭȫḗḝṓỡừỳ"
LETTERS = {"T": T_LETTERS, "Y": Y_LETTERS}
# Letters in front of which the capital keeps its 0.5.0 form (the italics and Black need a larger cut than the rule allows).
UNCOVERED = {"T": "äàèòùỳ", "Y": "èòờ"}


def _helpers(tt):
    """Every `.arm` glyph of the font as (helper, capital glyph, typed character, family, from an `ss03` copy). The characters
    come from the font's cmap, so a helper added later is covered without touching this file."""
    production = plistlib.loads(SOURCES.joinpath("OffentligSans-Regular.ufo", "lib.plist").read_bytes())["public.postscriptNames"]
    by_name = {}
    for code, name in tt.getBestCmap().items():
        by_name.setdefault(name, chr(code))
    out = []
    for helper in tt.getGlyphOrder():
        if not ARM.search(helper):
            continue
        base = ARM.sub("", helper)
        ss03 = base.endswith(".ss03")
        plain = base[: -len(".ss03")] if ss03 else base
        char = by_name.get(production.get(plain, plain))
        assert char is not None, helper
        out.append((helper, production.get(base, base), char, plain[0], ss03))
    return out


@lru_cache(maxsize=None)
def _font(weight, italic):
    path = static_path(weight, italic)
    tt = TTFont(path)
    return tt, tt.getGlyphOrder(), Shaper(path)


def _glyphs(weight, italic, text, features):
    _, order, sh = _font(weight, italic)
    return [order[gid] for gid, _ in sh.shape(text, features)]


def _plain(char, letter):
    import unicodedata

    return char + unicodedata.normalize("NFD", letter)[0]


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_arm_capitals_are_reachable_only_through_calt(italic):
    """Not in cmap, and no feature other than `calt` mentions one, so copied text holds the plain capitals."""
    tt = TTFont(static_path("Regular", italic))
    helpers = {n for n in tt.getGlyphOrder() if ARM.search(n)}
    assert len(helpers) >= 20
    assert {h for h, *_ in _helpers(tt)} == helpers
    assert not helpers & set(tt.getBestCmap().values())
    gsub = tt["GSUB"].table
    calt = {i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == "calt" for i in fr.Feature.LookupListIndex}
    others = {i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag != "calt" for i in fr.Feature.LookupListIndex}
    assert calt and not (others & calt)
    for i in sorted(others):
        buf = io.StringIO()
        gsub.LookupList.Lookup[i].toXML(XMLWriter(buf), tt)
        mentioned = {m for m in re.findall(r'"([^"]+\.arm)"', buf.getvalue())}
        assert not mentioned & helpers, (i, sorted(mentioned)[:3])


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_arm_capitals_keep_the_advance_and_the_marks_of_their_capital(weight, italic):
    tt, _, _ = _font(weight, italic)
    hmtx, glyf = tt["hmtx"], tt["glyf"]
    helpers = [n for n in tt.getGlyphOrder() if ARM.search(n)]
    production = plistlib.loads(SOURCES.joinpath("OffentligSans-Regular.ufo", "lib.plist").read_bytes())["public.postscriptNames"]
    wrong = []
    for name in helpers:
        base = ARM.sub("", name)
        base = production.get(base, base)
        if hmtx[name][0] != hmtx[base][0]:
            wrong.append((name, "advance"))
        a, b = glyf[name], glyf[base]
        if a.isComposite():
            parts_a = [(ARM.sub("", c.glyphName), c.x, c.y) for c in a.components]
            parts_b = [(c.glyphName, c.x, c.y) for c in b.components]
            if parts_a != parts_b:
                wrong.append((name, "components"))
        else:
            ca, cb = a.getCoordinates(glyf)[0], b.getCoordinates(glyf)[0]
            moved = [i for i, (p, q) in enumerate(zip(ca, cb)) if p != q]
            # only the two points at the end of the right arm move, to the left (`T`) or down along the arm's edges (`Y`: to the
            # left and down); none at the masters with a cut of 0
            if len(ca) != len(cb) or len(moved) not in (0, 2) or any(ca[i][0] >= cb[i][0] or ca[i][1] > cb[i][1] for i in moved):
                wrong.append((name, "outline"))
    assert wrong == []


@pytest.mark.parametrize("features", FEATURES, ids=list(FEATURES))
@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_covered_pairs_kern_like_the_plain_pair_and_keep_30_units(weight, italic, features):
    _, _, sh = _font(weight, italic)
    tt, _, sh = _font(weight, italic)
    feats = FEATURES[features]
    helpers = _helpers(tt)
    names = {h for h, *_ in helpers}
    bad = []
    seen = set()
    for helper, _, cap, family, ss03 in helpers:
        if ss03 and not feats.get("ss03"):
            continue  # the `ss03` copy is reached only with `ss03` on
        if not ss03 and feats.get("ss03") and helper.replace(".arm", ".ss03.arm") in names:
            continue  # with `ss03` on, the dotted capital is the `ss03` copy, checked on its own row
        # `ss03` is a font-wide feature; a capital without a copy ignores it
        for letter in LETTERS[family]:
            text = cap + letter
            shaped = _glyphs(weight, italic, text, feats)
            if len(shaped) != 2:
                continue  # a feature composed or split the letter
            seen.add(helper)
            plain = _plain(cap, letter)
            if shaped[0] != helper:
                bad.append((text, "not swapped to", helper, shaped[0]))
                continue
            gap = sh.gap(text, feats)
            if gap is not None and gap < FLOOR:
                bad.append((text, "gap", round(gap)))
            # the arm kerns like the plain pair, or looser where the shorter arm alone cannot reach 30 units (at most
            # LOOSER units: the ö of Y in Black, K20); never tighter
            looser = sh.shape(text, feats)[0][1] - sh.shape(plain, feats)[0][1]
            if not 0 <= looser <= LOOSER:
                bad.append((text, "kerning differs from", plain, round(looser)))
    assert bad == []
    # every helper that applies was reached by at least one letter
    expected = {h for h, _, _, _, ss03 in helpers if (not ss03 or feats.get("ss03")) and not (not ss03 and feats.get("ss03") and h.replace(".arm", ".ss03.arm") in names)}
    assert seen == expected, sorted(expected - seen)


@pytest.mark.parametrize("features", FEATURES, ids=list(FEATURES))
@pytest.mark.parametrize("weight,italic", [("Black", False), ("Regular", False), ("Black", True)], ids=["Black", "Regular", "Black-italic"])
def test_calt_off_and_uncovered_letters_keep_the_plain_capital(weight, italic, features):
    tt, _, _ = _font(weight, italic)
    feats = FEATURES[features]
    for _, _, cap, family, _ in _helpers(tt):
        for letter in LETTERS[family]:
            assert not ARM.search(_glyphs(weight, italic, cap + letter, {**feats, "calt": False})[0]), cap + letter
        for letter in UNCOVERED[family] + "oaeuAEO.":
            assert not ARM.search(_glyphs(weight, italic, cap + letter, feats)[0]), cap + letter


@pytest.mark.parametrize("weight,italic", [("Black", False), ("Black", True)], ids=["Black", "Black-italic"])
def test_the_arm_is_shorter_in_the_black_masters(weight, italic):
    """The cut is 0 at Thin and Regular and grows with the weight. `T` moves the end of the bar left by 20 - 40 units; `Y`
    ends its arm 90 - 110 units lower, along the edges of the plain arm, so the angle and the width of the stroke stay."""
    tt, _, _ = _font(weight, italic)
    glyf = tt["glyf"]
    t_arm, t = glyf["T.arm"].getCoordinates(glyf)[0], glyf["T"].getCoordinates(glyf)[0]
    assert 20 <= max(q[0] - p[0] for p, q in zip(t_arm, t)) <= 40
    arm, plain = glyf["Y.arm"].getCoordinates(glyf)[0], glyf["Y"].getCoordinates(glyf)[0]
    moved = [i for i, (p, q) in enumerate(zip(arm, plain)) if p != q]
    assert len(moved) == 2
    assert all(90 <= plain[i][1] - arm[i][1] <= 110 for i in moved)
    assert all(arm[i][1] == arm[moved[0]][1] for i in moved)  # the end of the arm stays flat
    # each edge keeps the direction of the plain arm (within half a degree), so the arm is not steeper or thinner
    import math

    n = len(arm)
    for end in moved:
        foot = next(j for j in ((end - 1) % n, (end + 1) % n) if j not in moved)
        a = math.degrees(math.atan2(arm[end][1] - arm[foot][1], arm[end][0] - arm[foot][0]))
        b = math.degrees(math.atan2(plain[end][1] - plain[foot][1], plain[end][0] - plain[foot][0]))
        assert abs(a - b) < 0.5, (end, a, b)
