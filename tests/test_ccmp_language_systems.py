"""Typed `i̇` + a top mark is one glyph in every language system (0.9.0 review).

`ccmp_latn_2` built the glyph only under `latn` default: with a language tag (`ro ca tr az kk tt`) or under `DFLT`, `i̇́` stayed three glyphs
and the mark overhung the next letter. Every language system of `GSUB` that has `ccmp` must list the lookup, and shaping must agree.
"""
import uharfbuzz as hb
import pytest
from fontTools.ttLib import TTFont

from conftest import static_path
from test_accent_pairs import TOP_MARKS
from test_spacing import ALL_FONTS, ALL_IDS

LANGUAGES = ["ro", "ca", "tr", "az", "kk", "tt", "crh", "mo", "lt", "en", "sv"]  # the declared ones and two that are not
MARKS = TOP_MARKS + "̏"


def ccmp_lookup_sets(path):
    """{(script, language): set of lookup indexes of its `ccmp`} for every language system that has `ccmp`."""
    gsub = TTFont(path)["GSUB"].table
    features = gsub.FeatureList.FeatureRecord
    out = {}
    for sr in gsub.ScriptList.ScriptRecord:
        systems = [("dflt", sr.Script.DefaultLangSys)] + [(r.LangSysTag, r.LangSys) for r in sr.Script.LangSysRecord]
        for tag, ls in systems:
            if ls is None:
                continue
            lookups = set()
            for fi in ls.FeatureIndex:
                if features[fi].FeatureTag == "ccmp":
                    lookups |= set(features[fi].Feature.LookupListIndex)
            out[(sr.ScriptTag, tag)] = lookups
    return out


def lookup_with_glyph(path, glyph):
    """Index of the `GSUB` lookup that substitutes into `glyph` (the typed `i̇` with a mark)."""
    gsub = TTFont(path)["GSUB"].table
    hits = set()
    for index, lookup in enumerate(gsub.LookupList.Lookup):
        for sub in lookup.SubTable:
            sub = getattr(sub, "ExtSubTable", sub)
            for table in (getattr(sub, "ligatures", None) or {}).values():
                if any(lig.LigGlyph == glyph for lig in table):
                    hits.add(index)
    return hits


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_every_language_system_builds_the_typed_dotted_i_forms(weight, italic):
    path = static_path(weight, italic)
    wanted = lookup_with_glyph(path, "idotless_dotaccentcomb_acutecomb")
    assert wanted, "no lookup builds idotless_dotaccentcomb_acutecomb"
    systems = ccmp_lookup_sets(path)
    assert ("DFLT", "dflt") in systems and ("latn", "dflt") in systems
    missing = [system for system, lookups in systems.items() if not wanted <= lookups]
    assert missing == []


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_typed_dotted_i_with_a_mark_shapes_to_one_glyph_in_every_language(weight, italic):
    path = static_path(weight, italic)
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    many = []
    for language in [None] + LANGUAGES:
        for mark in MARKS:
            buf = hb.Buffer()
            buf.add_str("i̇" + mark)
            buf.script = "Latn"
            buf.direction = "ltr"
            if language:
                buf.language = language
            hb.shape(font, buf, {})
            if len(buf.glyph_infos) != 1:
                many.append((language, f"U+{ord(mark):04X}", len(buf.glyph_infos)))
    assert many == []
