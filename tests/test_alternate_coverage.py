"""Every accented letter has its cv03, cv04, cv05, ss01, ss02 and ss03 form, and every dotted letter alternate its round-dot form.

The letter alternates (`cv03` G, `cv04` single-storey a, `cv05` serifed I, `ss01` g, `ss02` l) and `ss03` (square dots) are separate
features, and the `cv` features run first. A letter that has a dot and an alternate therefore needs a third glyph,
`<name>.cvNN.ss03`, otherwise `ss03` would leave it with square dots or undo the alternate.
"""
import re
import unicodedata
from pathlib import Path

import pytest
import ufoLib2
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from conftest import STATICS, STATIC_IDS, static_path

SOURCES = Path(__file__).resolve().parent.parent / "sources"
MASTERS = ["Thin", "Regular", "Black", "ThinItalic", "RegularItalic", "BlackItalic"]
LETTER_FEATURES = {"cv03": "G", "cv04": "a", "cv05": "I", "ss01": "g", "ss02": "l"}
# Letters drawn with a bar, not built from the base by a combining mark: they have their own alternate too.
# (`ǥ` is built on `g.ss01` by design, so `ss01` leaves it as it is.)
DRAWN = {"cv03": [0x01E4], "cv05": [0x0197], "ss02": [0x0142]}
SQUARE_DOT_PARTS = ["i", "j", "dieresiscomb", "dotaccentcomb", "dotbelowcomb"]
LATIN = [*range(0x41, 0x250), *range(0x1E00, 0x1F00)]


def shape(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def ss03_rules(ttf):
    """Source glyph name (or production name) to `.ss03` glyph, as the `ss03` feature substitutes them."""
    gsub = ttf["GSUB"].table
    mapped = {}
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag == "ss03":
            for index in record.Feature.LookupListIndex:
                for sub in gsub.LookupList.Lookup[index].SubTable:
                    mapped.update(getattr(sub, "ExtSubTable", sub).mapping)
    return mapped


def has_square_dot(font, name):
    """True if a component of the glyph (at any depth) has a round-dot form: the glyph then carries a square dot or comma head."""
    return any(c.baseGlyph + ".ss03" in font or has_square_dot(font, c.baseGlyph) for c in font[name].components)


@pytest.fixture(scope="module")
def regular_source():
    return ufoLib2.Font.open(SOURCES / "OffentligSans-Regular.ufo")


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
@pytest.mark.parametrize("tag,base", LETTER_FEATURES.items())
def test_every_encoded_letter_on_the_base_has_its_alternate(tag, base, weight, italic):
    """Each encoded letter whose decomposition starts with the base letter shapes to one `.cvNN` glyph with the feature on."""
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    missing = []
    for cp in LATIN:
        if cp not in cmap or (unicodedata.normalize("NFD", chr(cp))[0] != base and cp not in DRAWN.get(tag, [])):
            continue
        if cp == 0x01E5:
            continue
        shaped = shape(path, chr(cp), {tag: True})
        if len(shaped) != 1 or not shaped[0].endswith("." + tag):
            missing.append((hex(cp), shaped))
    assert not missing


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_salt_follows_ss01_and_ss02(weight, italic):
    """`salt` is `ss01` and `ss02` together, for the plain letters, the accented ones, `fl`, `ŀ` and `ł`."""
    path = static_path(weight, italic)
    cmap = TTFont(path).getBestCmap()
    text = "".join(chr(cp) for cp in [*LATIN, 0xFB02] if cp in cmap and (
        unicodedata.normalize("NFD", chr(cp))[0] in "gl" or cp in (0x0140, 0x0142, 0xFB02)))
    for char in text:
        assert shape(path, char, {"salt": True}) == shape(path, char, {"ss01": True, "ss02": True}), char
    assert shape(path, "ĝľł", {"salt": True}) == ["gcircumflex.ss01", "lcaron.ss02", "lslash.ss02"]


@pytest.mark.parametrize("master", MASTERS)
def test_every_alternate_is_built_from_the_alternate_base(master):
    """Each `.cvNN`, `.ss01` or `.ss02` accented letter is the alternate base plus the marks of its default letter, in the same order."""
    font = ufoLib2.Font.open(SOURCES / f"OffentligSans-{master}.ufo")
    bad = []
    for name in font.keys():
        match = re.fullmatch(r"(.+)\.(cv0[345]|ss0[12])", name)
        if not match or "IJ" in name or name.startswith("fl.") or not font[name].components:
            continue
        plain, tag = match.groups()
        base = LETTER_FEATURES[tag] + "." + tag
        parts = [c.baseGlyph for c in font[name].components]
        want = [base] + [c.baseGlyph for c in font[plain].components[1:]]
        if parts != want:
            bad.append((name, parts, want))
    assert not bad


def test_every_square_dot_glyph_has_an_ss03_form(regular_source):
    names = set(regular_source.keys())
    assert all(part + ".ss03" in names for part in SQUARE_DOT_PARTS)
    encoded = [n for n in regular_source.keys() if regular_source[n].unicodes and not n.endswith(".ss03")]
    dotted = [n for n in encoded if has_square_dot(regular_source, n)]
    assert len(dotted) > 100
    missing = [n for n in dotted if n + ".ss03" not in names]
    assert not missing


def test_every_dotted_alternate_has_a_round_dot_form(regular_source):
    names = set(regular_source.keys())
    alternates = [n for n in names if re.search(r"\.(cv0[345]|ss0[12])$", n) and has_square_dot(regular_source, n)]
    assert len(alternates) >= 11
    missing = [n for n in alternates if n + ".ss03" not in names]
    assert not missing


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_ss03_has_a_rule_for_every_dotted_glyph_and_alternate(weight, italic, regular_source):
    ttf = TTFont(static_path(weight, italic))
    targets = set(ss03_rules(ttf).values())
    order = set(ttf.getGlyphOrder())
    # The hidden helper capitals (`.tk01` to `.tk03`, `.arm`) of dotted capitals are reached through the `.ss03.tkNN` and `.ss03.arm` helpers.
    dotted = {n for n in regular_source.keys()
              if not n.endswith(".ss03") and not n.startswith("_") and ".tk" not in n and not n.endswith(".arm") and has_square_dot(regular_source, n)}
    assert dotted
    assert not [n for n in dotted if n + ".ss03" not in targets or n + ".ss03" not in order]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_cv_and_ss03_together_give_the_round_dot_alternate(weight, italic):
    path = static_path(weight, italic)
    both = lambda text, tag: shape(path, text, {tag: True, "ss03": True})
    assert both("ä", "cv04") == ["adieresis.cv04.ss03"]
    assert both("ǟ", "cv04") == ["adieresismacron.cv04.ss03"]
    assert both("ȧ", "cv04") == ["adotaccent.cv04.ss03"]
    assert both("Ġ", "cv03") == ["Gdotaccent.cv03.ss03"]
    assert both("Ï", "cv05") == ["Idieresis.cv05.ss03"]
    assert both("ġ", "ss01") == ["gdotaccent.ss01.ss03"]
    assert both("ģ", "ss01") == ["gcommaaccent.ss01.ss03"]
    assert both("ḷ", "ss02") == ["ldotbelow.ss02.ss03"]
    assert both("ļ", "ss02") == ["lcommaaccent.ss02.ss03"]
    assert both("Ḯ", "cv05") == ["Idieresisacute.cv05.ss03"]
    # an alternate with no dot is unchanged by ss03, and with ss03 alone the plain round-dot letter is used
    assert both("ǎ", "cv04") == ["acaron.cv04"]
    assert shape(path, "ǟ", {"ss03": True}) == ["adieresismacron.ss03"]
    # neither feature on: default shaping
    assert not any(".ss03" in g or ".cv0" in g for g in shape(path, "äǟȧĠÏḮǎ", {}))
