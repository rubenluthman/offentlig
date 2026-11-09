"""ss03 swaps every glyph that carries a dot for its round-dot form and changes nothing when it is off."""
import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from conftest import STATICS, STATIC_IDS, static_path

# Every glyph whose outline or components contain a dot: i j and the dot accents, the punctuation dots and
# comma heads, and every composite built from them.
DOT_GLYPHS = """
    Abrevedotbelow Acircumflexdotbelow Adieresis Adotbelow Cdotaccent Ddotbelow
    Ecircumflexdotbelow Edieresis Edotaccent Edotbelow Gcommaaccent Gdotaccent Hdotbelow
    Idieresis Idotaccent Idotbelow Kcommaaccent Lcommaaccent Ldot Ncommaaccent Ndotaccent
    Ocircumflexdotbelow Odieresis Odotbelow Ohorndotbelow Rcommaaccent Rdotbelow Scommaaccent
    Sdotbelow Tcommaaccent Tdotbelow Udieresis Udotbelow Uhorndotbelow Wdieresis Ydieresis
    Ydotbelow Zdotaccent Zdotbelow abrevedotbelow acircumflexdotbelow adieresis adotbelow
    cdotaccent colon comma comma.tf commaaccentcomb commaturnedabovecomb ddotbelow dieresis
    dieresiscomb divide dotaccent dotaccentcomb dotbelowcomb ecircumflexdotbelow edieresis
    edotaccent edotbelow ellipsis exclam exclamdown fi gcommaaccent gdotaccent hdotbelow i
    idieresis idotaccent idotbelow iogonek j kcommaaccent lcommaaccent ldot ncommaaccent
    ndotaccent ocircumflexdotbelow odieresis odotbelow ohorndotbelow period period.tf
    periodcentered question questiondown quotedblbase quotedblleft quotedblright quoteleft
    quoteright quotesinglbase rcommaaccent rdotbelow scommaaccent sdotbelow semicolon
    tcommaaccent tdotbelow udieresis udotbelow uhorndotbelow wdieresis ydieresis ydotbelow
    zdotaccent zdotbelow
""".split()


def shape(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos], [p.x_advance for p in buf.glyph_positions]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_every_dot_glyph_has_an_ss03_form(weight, italic):
    order = set(TTFont(static_path(weight, italic)).getGlyphOrder())
    missing = [g for g in DOT_GLYPHS if g + ".ss03" not in order]
    assert not missing


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_ss03_substitutes_every_dot_glyph(weight, italic):
    font = TTFont(static_path(weight, italic))
    gsub = font["GSUB"].table
    mapped = {}
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag != "ss03":
            continue
        for index in record.Feature.LookupListIndex:
            for sub in gsub.LookupList.Lookup[index].SubTable:
                sub = getattr(sub, "ExtSubTable", sub)
                mapped.update(sub.mapping)
    # keys can carry production names (uniXXXX), the .ss03 targets are never renamed
    assert sorted(mapped.values()) == sorted(g + ".ss03" for g in DOT_GLYPHS)
    assert len(mapped) == len(DOT_GLYPHS)


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_ss03_shapes_text_with_round_dots(italic):
    path = static_path("Regular", italic)
    text = "\u00e4\u00f6\u00ef\u0130ij.,:;!?\u00bf\u00a1\u2026\u00f7"
    off, _ = shape(path, text, {})
    on, _ = shape(path, text, {"ss03": True})
    assert not any(g.endswith(".ss03") for g in off)
    assert len(on) == len(text) and all(g.endswith(".ss03") for g in on)
    assert shape(path, "fi", {"ss03": True})[0] == ["fi.ss03"]
    # a decomposed diaeresis is composed first, then swapped
    assert shape(path, "a\u0308", {"ss03": True})[0] == ["adieresis.ss03"]
    # letters without a dot stay as they are
    assert shape(path, "abc", {"ss03": True})[0] == shape(path, "abc", {})[0]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_ss03_off_matches_default_shaping(weight, italic):
    path = static_path(weight, italic)
    text = "Hej, vad g\u00f6r du i kv\u00e4ll? Jag \u00e4r p\u00e5 v\u00e4g! fi Ti: a;b \u0130"
    assert shape(path, text, {"ss03": False}) == shape(path, text, {})
    assert not any(g.endswith(".ss03") for g in shape(path, text, {})[0])


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_ss03_keeps_the_layout(italic):
    path = static_path("Regular", italic)
    text = "Hej, vad g\u00f6r du i kv\u00e4ll? Jag \u00e4r p\u00e5 v\u00e4g!"
    assert shape(path, text, {"ss03": True})[1] == shape(path, text, {})[1]


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
def test_italic_ss03_marks_sit_on_their_anchors(weight):
    """Each mark of an italic `.ss03` composite puts its `_top` or `_bottom` anchor on the anchor of the preceding component that carries that name (within 10 units)."""
    import ufoLib2
    from pathlib import Path

    font = ufoLib2.Font.open(Path(__file__).resolve().parent.parent / "sources" / f"OffentligSans-{weight}Italic.ufo")
    anchors = lambda name: {a.name: (a.x, a.y) for a in font[name].anchors}
    bad = []
    for glyph in font:
        if not glyph.name.endswith(".ss03") or glyph.contours or len(glyph.components) < 2:
            continue
        for index, comp in enumerate(glyph.components[1:], start=1):
            mark = anchors(comp.baseGlyph)
            attach = [k for k in mark if k.startswith("_")]
            if not attach:
                continue
            name = attach[0][1:]
            target = next((c for c in reversed(glyph.components[:index]) if name in anchors(c.baseGlyph)), None)
            if target is None:
                continue
            tx, ty = anchors(target.baseGlyph)[name]
            dx = comp.transformation[4] - (tx + target.transformation[4] - mark[attach[0]][0])
            dy = comp.transformation[5] - (ty + target.transformation[5] - mark[attach[0]][1])
            if abs(dx) > 10 or abs(dy) > 10:
                bad.append((glyph.name, comp.baseGlyph, round(dx), round(dy)))
    assert not bad, bad
