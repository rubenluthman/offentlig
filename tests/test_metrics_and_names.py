"""Vertical metrics match ARCHITECTURE.md; names never use Public Sans; coverage; variable default."""
import plistlib
import re

import pytest
from fontTools.ttLib import TTFont

from conftest import BUILD, ROOT, WEIGHTS, static_path

SWEDISH = "ÅÄÖåäöÉé"


def recorded_metrics():
    text = (ROOT / "ARCHITECTURE.md").read_text()
    rows = re.findall(r"^\|\s*`(\w+)`\s*\|\s*(-?\d+)\s*\|", text, re.M)
    values = {k: int(v) for k, v in rows}
    assert values, "no metrics table found in ARCHITECTURE.md"
    return values


def actual_metrics(font):
    return {
        "unitsPerEm": font["head"].unitsPerEm,
        "typoAscender": font["OS/2"].sTypoAscender,
        "typoDescender": font["OS/2"].sTypoDescender,
        "typoLineGap": font["OS/2"].sTypoLineGap,
        "winAscent": font["OS/2"].usWinAscent,
        "winDescent": font["OS/2"].usWinDescent,
        "hheaAscender": font["hhea"].ascent,
        "hheaDescender": font["hhea"].descent,
        "hheaLineGap": font["hhea"].lineGap,
    }


def test_vertical_metrics_static(static_ttf):
    expected = recorded_metrics()
    actual = actual_metrics(static_ttf)
    assert {k: actual[k] for k in expected} == expected
    assert static_ttf["OS/2"].fsSelection & (1 << 7), "USE_TYPO_METRICS must be set"


def test_vertical_metrics_variable(variable_ttf):
    expected = recorded_metrics()
    actual = actual_metrics(variable_ttf)
    assert {k: actual[k] for k in expected} == expected


NAME_IDS = (1, 2, 3, 4, 6, 16, 17, 21, 22, 25)


def test_names_use_offentlig_sans(static_ttf):
    for rec in static_ttf["name"].names:
        text = rec.toUnicode()
        if rec.nameID in NAME_IDS:
            assert "Public" not in text, (rec.nameID, text)
    family = static_ttf["name"].getBestFamilyName()
    assert family == "Offentlig Sans"
    assert static_ttf["name"].getName(6, 3, 1, 0x409).toUnicode().startswith("OffentligSans-")


def test_names_variable(variable_ttf):
    for rec in variable_ttf["name"].names:
        if rec.nameID in NAME_IDS:
            assert "Public" not in rec.toUnicode(), (rec.nameID, rec.toUnicode())
    assert variable_ttf["name"].getBestFamilyName() == "Offentlig Sans"


def test_upstream_copyright_kept(static_ttf):
    copyright_ = static_ttf["name"].getName(0, 3, 1, 0x409).toUnicode()
    assert "The Public Sans Project Authors" in copyright_
    assert "The Offentlig Project Authors" in copyright_


def test_swedish_letters_present(static_ttf):
    cmap = static_ttf.getBestCmap()
    assert [c for c in SWEDISH if ord(c) not in cmap] == []


def test_swedish_letters_present_variable(variable_ttf):
    cmap = variable_ttf.getBestCmap()
    assert [c for c in SWEDISH if ord(c) not in cmap] == []


def test_variable_default_is_regular(variable_ttf):
    axis = next(a for a in variable_ttf["fvar"].axes if a.axisTag == "wght")
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100, 400, 900)
    assert variable_ttf["OS/2"].usWeightClass == 400


def test_variable_default_matches_regular_static(variable_path):
    """The variable default master is Regular: same advances and bounds within quadratic-conversion tolerance."""
    from fontTools.pens.boundsPen import BoundsPen
    italic = "Italic" in variable_path.name
    vf = TTFont(variable_path)
    st = TTFont(static_path("Regular", italic))
    for name in ("a", "aring", "g", "l", "H", "endash", "space"):
        assert vf["hmtx"][name][0] == st["hmtx"][name][0], name
        bounds = []
        for f in (vf, st):
            gs = f.getGlyphSet()
            bp = BoundsPen(gs)
            gs[name].draw(bp)
            bounds.append(bp.bounds)
        if bounds[0] is not None:
            assert all(abs(x - y) <= 1 for x, y in zip(bounds[0], bounds[1])), (name, bounds)


def test_static_weight_classes():
    expected = dict(zip(WEIGHTS, range(100, 1000, 100)))
    for weight, cls in expected.items():
        for italic in (False, True):
            f = TTFont(static_path(weight, italic))
            assert f["OS/2"].usWeightClass == cls, (weight, italic)


def source_numbers():
    """`(versionMajor, versionMinor)` from the six masters, which must agree with each other."""
    versions = set()
    for ufo in sorted((ROOT / "sources").glob("OffentligSans*.ufo")):
        with open(ufo / "fontinfo.plist", "rb") as f:
            info = plistlib.load(f)
        versions.add((info["versionMajor"], info["versionMinor"]))
    assert len(versions) == 1, f"the masters carry different versions: {sorted(versions)}"
    return versions.pop()


def source_version():
    major, minor = source_numbers()
    return f"Version {major}.{minor}"


def assert_revision_matches_the_sources(font):
    """`head.fontRevision` is `versionMajor.versionMinor` (a 16.16 fixed-point number, so within 0.001)."""
    major, minor = source_numbers()
    assert font["head"].fontRevision == pytest.approx(float(f"{major}.{minor}"), abs=0.001)


def test_version_matches_the_sources(static_ttf):
    assert static_ttf["name"].getName(5, 3, 1, 0x409).toUnicode() == source_version()
    assert_revision_matches_the_sources(static_ttf)


def test_variable_version_matches_the_sources(variable_ttf):
    assert variable_ttf["name"].getName(5, 3, 1, 0x409).toUnicode() == source_version()
    assert_revision_matches_the_sources(variable_ttf)


def test_proof_text_is_covered():
    """Every character of the Allemansrätten tester text exists in the upright and italic variable fonts."""
    text = (ROOT / "docs" / "proof" / "allemansratten.txt").read_text(encoding="utf-8")
    for name in ("OffentligSans[wght].ttf", "OffentligSans-Italic[wght].ttf"):
        cmap = TTFont(BUILD / "variable" / name).getBestCmap()
        missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
        assert missing == [], (name, missing)


def test_variable_default_instance_names_match_name_table(variable_ttf):
    """The default named instance and the font's own PostScript name agree (Fontspector valid_default_instance_nameids)."""
    name = variable_ttf["name"]
    ps = name.getName(6, 3, 1, 0x409).toUnicode()
    default = [i for i in variable_ttf["fvar"].instances if i.coordinates["wght"] == 400]
    assert default and name.getDebugName(default[0].postscriptNameID) == ps
