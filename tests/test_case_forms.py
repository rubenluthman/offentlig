"""Case-sensitive punctuation: `.case` forms and the `case` and `calt` rules that swap them in.

The hyphen, en and em dash, `( ) [ ] { }`, `« » ‹ ›`, `¡ ¿` (also with `ss03`), the slash, `@` and the colon (also the round-dot colon) have a `.case` form moved so that its ink
centre sits on the capital centre; the advance is unchanged. `case` swaps every one of them; `calt` swaps the hyphen, the dashes
and the colon only where the neighbours are capitals or figures, and `@` before a capital. Parentheses, square brackets,
braces, guillemets, `¡ ¿` and the slash rise in `case` only: raised by their neighbours, one of a pair could rise and the other
not (`«Hej»`), `¿` would sit on the baseline in nearly every Spanish sentence and the slash would be clipped in `24/7`
(docs/design-decisions.md, F4 and F18). The bullet needs none: its centre is within 12 units of the capital centre.
"""
import pytest
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen

from conftest import STATIC_IDS, STATICS, static_path

INVERTED = {"exclamdown", "questiondown", "exclamdown.ss03", "questiondown.ss03"}
CASE_BASES = {
    "-": "hyphen", "–": "endash", "—": "emdash", "(": "parenleft", ")": "parenright", "[": "bracketleft",
    "]": "bracketright", "{": "braceleft", "}": "braceright", "@": "at", ":": "colon", "«": "guillemetleft", "»": "guillemetright",
    "‹": "guilsinglleft", "›": "guilsinglright", "¡": "exclamdown", "¿": "questiondown", "/": "slash",
}

# `^` marks the character that `calt` raises. Everything else stays at its default height, brackets included.
CONTEXTS = [
    # times, dates, ranges
    "12^:30", "ISO 2026^-11^-18", "A^–Ö", "Ö^–Å", "ABC^-123", "A^—B", "1^–2", "A^:B", "A1^:B2",
    # the stricter rule: a lowercase neighbour keeps the low form
    "E-post", "T-shirt", "12-tal", "x-y", "KL:s", "1:a", "Hej: ", "a - B", "A - 1", "-1", "A-",
    # brackets are never raised by `calt`, whatever stands inside them
    "(HEJ)", "(1)", "[1]", "[TEXT]", "{AB}", "(A1)", "(ÅÄ)", "((HEJ))", "(Stockholm)", "(Hej)", "[x]", "(1", "(9^:00)", "(född 1984)",
    "(2026 års utgåva)", "(A^-12)", "(12^-A)", "(1]", "(1^-2)", "(Hej) 12-tal",
    # @ before a capital
    "H^@G", "^@HEJ", "^@Hej", "user@host", "x@1",
    # accented capitals count as capitals
    "ÅÄÖ^-ÅÄÖ",
    # guillemets, inverted marks and the slash are never raised by `calt`
    "«HEJ»", "«Hej»", "‹A›", "¿QUÉ?", "¡HOLA!", "¿Qué?", "A/B", "24/7", "22/11", "a/b",
]


def font_of(path):
    return hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))


def shape(font, text, features):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def split(marked):
    text, raised, _ = "", set(), 0
    for ch in marked:
        if ch == "^":
            raised.add(len(text))
        else:
            text += ch
    return text, raised


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_calt_raises_punctuation_between_capitals_and_figures_only(weight, italic):
    font = font_of(static_path(weight, italic))
    for marked in CONTEXTS:
        text, raised = split(marked)
        got = shape(font, text, {})
        assert len(got) == len(text), (text, got)
        found = {i for i, g in enumerate(got) if g.endswith(".case")}
        assert found == raised, (text, got)


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_calt_off_raises_nothing_and_case_raises_everything(weight, italic):
    font = font_of(static_path(weight, italic))
    for marked in CONTEXTS:
        text, raised = split(marked)
        assert not [g for g in shape(font, text, {"calt": False}) if g.endswith(".case")], text
        got = shape(font, text, {"calt": False, "case": True})
        want = {i for i, ch in enumerate(text) if ch in CASE_BASES}
        assert {i for i, g in enumerate(got) if g.endswith(".case")} == want, (text, got)


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_brackets_rise_under_case_only(weight, italic):
    """No parenthesis, square bracket or brace changes under the default features (or `calt` alone); all of them rise under `case`."""
    font = font_of(static_path(weight, italic))
    text = "(HEJ) [1] {AB} (9:00) (född 1984) ((A1)) (1] [A-1}"
    brackets = {i for i, ch in enumerate(text) if ch in "()[]{}"}
    for features in ({}, {"calt": True}):
        assert not [g for g in shape(font, text, features) if g.split(".")[0] in {CASE_BASES[c] for c in "()[]{}"} and g.endswith(".case")]
    got = shape(font, text, {"case": True})
    assert {i for i, g in enumerate(got) if g.endswith(".case")} >= brackets


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_round_dot_colon_and_oldstyle_figures(italic):
    font = font_of(static_path("Regular", italic))
    assert shape(font, "12:30", {"ss03": True}) == ["one", "two", "colon.ss03.case", "three", "zero"]
    assert shape(font, "12:30", {"ss03": True, "calt": False, "case": True})[2] == "colon.ss03.case"
    assert shape(font, "12:30", {"ss03": True, "calt": False})[2] == "colon.ss03"
    assert shape(font, "¡¿", {"ss03": True, "case": True}) == ["exclamdown.ss03.case", "questiondown.ss03.case"]
    assert shape(font, "¡¿", {"ss03": True}) == ["exclamdown.ss03", "questiondown.ss03"]
    # oldstyle figures sit at lowercase height: nothing is raised next to them
    assert not [g for g in shape(font, "2026-11-18 12:30 (12)", {"onum": True}) if g.endswith(".case")]
    # tabular figures and the slashed zero are figures
    assert shape(font, "10:30", {"tnum": True})[2] == "colon.case"
    assert "colon.case" in shape(font, "0:0", {"zero": True})


@pytest.mark.parametrize("weight,italic", STATICS, ids=STATIC_IDS)
def test_case_forms_are_centred_on_the_capitals_and_keep_their_width(weight, italic):
    from fontTools.ttLib import TTFont
    ttf = TTFont(static_path(weight, italic))
    gs, cmap, hmtx = ttf.getGlyphSet(), ttf.getBestCmap(), ttf["hmtx"]

    def centre(name):
        pen = BoundsPen(gs)
        gs[name].draw(pen)
        return (pen.bounds[1] + pen.bounds[3]) / 2

    cap = centre("H")
    # The compiled font names U+00AB and U+00BB `guillemotleft` and `guillemotright`; the case forms keep the source name.
    bases = {name: cmap[ord(ch)] for ch, name in CASE_BASES.items()}
    bases.update({"colon.ss03": "colon.ss03", "exclamdown.ss03": "exclamdown.ss03", "questiondown.ss03": "questiondown.ss03"})
    for source_name, name in bases.items():
        case = source_name + ".case"
        assert case in ttf.getGlyphOrder(), case
        assert hmtx[case][0] == hmtx[name][0], case
        assert case not in cmap.values(), case
        if source_name in INVERTED:  # the lowest point sits on the baseline instead of the centre on the capital centre
            pen = BoundsPen(gs)
            gs[case].draw(pen)
            assert abs(pen.bounds[1]) <= 1, (case, pen.bounds)
            continue
        if source_name == "slash":  # runs from the baseline to the cap height
            pen = BoundsPen(gs)
            gs[case].draw(pen)
            assert abs(pen.bounds[1]) <= 1 and abs(pen.bounds[3] - 1446) <= 1, (case, pen.bounds)
            continue
        assert abs(centre(case) - cap) <= 2, (case, centre(case), cap)
        assert abs(centre(name) - cap) > 20, (name, "was not low")


@pytest.mark.parametrize("weight,italic", [("Regular", False), ("Regular", True)], ids=["roman", "italic"])
def test_case_and_calt_are_in_the_font(weight, italic):
    from fontTools.ttLib import TTFont
    ttf = TTFont(static_path(weight, italic))
    tags = {r.FeatureTag for r in ttf["GSUB"].table.FeatureList.FeatureRecord}
    assert {"case", "calt"} <= tags
