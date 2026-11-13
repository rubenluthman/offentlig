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
    Adieresismacron Adotaccent Bdotaccent Ddotaccent Fdotaccent Hdieresis Hdotaccent Idieresisacute Kdotbelow
    Ldotbelow Mdotaccent Mdotbelow Ndotbelow Odieresismacron Odotaccent Odotaccentmacron Pdotaccent Rdotaccent
    Sdotaccent Tdotaccent Udieresisacute Udieresiscaron Udieresisgrave Udieresismacron Wdotaccent Xdieresis
    Ydotaccent adieresismacron adotaccent bdotaccent candrabinducomb commaaboverightcomb ddotaccent fdotaccent
    hdieresis hdotaccent idotlessdieresisacute ij istroke kdotbelow ldotbelow mdotaccent mdotbelow napostrophe
    ndotbelow odieresismacron odotaccent odotaccentmacron pdotaccent rdotaccent sdotaccent tdieresis tdotaccent
    udieresisacute udieresiscaron udieresisgrave udieresismacron wdotaccent xdieresis ydotaccent
""".split()

# Letter alternates that carry a dot: the `cv` and `ss02` features run first, so these need their own round-dot forms.
DOT_ALTERNATES = """
    Gcommaaccent.cv03 Gdotaccent.cv03 Idieresis.cv05 Idieresisacute.cv05 Idotaccent.cv05 Idotbelow.cv05
    abrevedotbelow.cv04 acircumflexdotbelow.cv04 adieresis.cv04 adieresismacron.cv04 adotaccent.cv04
    adotbelow.cv04 ldot.ss02
""".split()
DOT_GLYPHS += DOT_ALTERNATES


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
        if glyph.name == "candrabinducomb.ss03":
            continue  # a dot centred on a breve: it has no anchor to attach to, test_wagner_italic_marks checks its slant
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


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_ss03_does_not_undo_letter_alternates(weight, italic):
    """The `cv` features run before `ss03`, so a letter alternate keeps its shape under `ss03` and swaps to its own round-dot form."""
    path = static_path(weight, italic)
    assert shape(path, "ä", {"ss03": True, "cv04": True})[0] == ["adieresis.cv04.ss03"]
    assert shape(path, "ạ", {"ss03": True, "cv04": True})[0] == ["adotbelow.cv04.ss03"]
    assert shape(path, "Ï", {"ss03": True, "cv05": True})[0] == ["Idieresis.cv05.ss03"]
    assert shape(path, "Ġ", {"ss03": True, "cv03": True})[0] == ["Gdotaccent.cv03.ss03"]
    assert shape(path, "ǟ", {"ss03": True, "cv04": True})[0] == ["adieresismacron.cv04.ss03"]
    assert shape(path, "ȧ", {"ss03": True, "cv04": True})[0] == ["adotaccent.cv04.ss03"]
    assert shape(path, "Ḯ", {"ss03": True, "cv05": True})[0] == ["Idieresisacute.cv05.ss03"]
    # an alternate without a dot keeps its form, and a dotted letter without an alternate gets the plain round dots
    assert shape(path, "á", {"ss03": True, "cv04": True})[0] == ["aacute.cv04"]
    # letters the alternates do not touch still get round dots
    assert shape(path, "öÄ", {"ss03": True, "cv04": True})[0] == ["odieresis.ss03", "Adieresis.ss03"]
    assert shape(path, "1.5", {"ss03": True, "tnum": True})[0] == ["one.tf", "period.tf.ss03", "five.tf"]


def last_mark_offset(path, text, features):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return buf.glyph_positions[-1].y_offset


STACKS = [
    "ä́", "Ä́", "ė́", "ÿ́", "ö́", "ǘ", "ḯ",
    "ö̀", "ǜ", "ï̀", "ȫ", "ǖ", "ï̄", "ǟ",
    "Ġ́", "ż́", "İ́", "Ë̀",
]


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_marks_stacked_on_round_dots_clear_the_dots(weight, italic):
    """A second mark over a letter with a dot or diaeresis sits at least as high with `ss03` as without, so it never lands on the (larger) round dots."""
    path = static_path(weight, italic)
    for text in STACKS:
        off = last_mark_offset(path, text, {})
        on = last_mark_offset(path, text, {"ss03": True})
        # a stack the font composes into one glyph (ü + acute is ǘ) has no second mark to place
        assert on >= off, (text, off, on)
        if text in ("\u00e4\u0301", "\u00c4\u0301", "\u0117\u0301", "\u00ff\u0301", "\u00f6\u0300"):
            assert off > 0, text


ABOVE_DOTS = {"dieresiscomb", "dotaccentcomb"}


def _extent(font, comp):
    xmin, ymin, xmax, ymax = font[comp.baseGlyph].getBounds(font)
    return ymin + comp.transformation[5], ymax + comp.transformation[5]


def _clearances(font, glyph):
    """(dots to the letter below, dots to the mark above or None) for a composite whose first dot mark sits above its base."""
    parts = glyph.components
    index = next((i for i, c in enumerate(parts) if c.baseGlyph.removesuffix(".ss03") in ABOVE_DOTS), None)
    if index is None or index == 0:
        return None
    dot_bottom, dot_top = _extent(font, parts[index])
    below = dot_bottom - max(_extent(font, c)[1] for c in parts[:index])
    above = [_extent(font, c)[0] - dot_top for c in parts[index + 1:] if _extent(font, c)[0] > dot_top - 5]
    return below, (min(above) if above else None)


@pytest.mark.parametrize("weight", ["Thin", "Regular", "Black"])
@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_round_dots_keep_the_clearances_of_the_square_dots(weight, italic):
    """Round dots sit no closer to the letter than square dots; a mark stacked above them is never closer than 2 units less than above square dots."""
    import ufoLib2
    from pathlib import Path

    font = ufoLib2.Font.open(Path(__file__).resolve().parent.parent / "sources" / f"OffentligSans-{weight}{'Italic' if italic else ''}.ufo")
    checked, bad = 0, []
    for glyph in font:
        if not glyph.name.endswith(".ss03") or glyph.contours or glyph.name[:-5] not in font:
            continue
        plain, rounded = _clearances(font, font[glyph.name[:-5]]), _clearances(font, glyph)
        if plain is None or rounded is None:
            continue
        checked += 1
        if rounded[0] < plain[0] - 0.5:
            bad.append((glyph.name, "letter", round(plain[0], 1), round(rounded[0], 1)))
        if plain[1] is not None and rounded[1] < plain[1] - 2:
            bad.append((glyph.name, "mark", round(plain[1], 1), round(rounded[1], 1)))
    assert checked > 80
    assert not bad, bad
