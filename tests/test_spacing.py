"""Kerning groups and spacing of the glyphs and alternates added since Public Sans.

Every letter and every letter alternate belongs to a kerning group on both sides (or is named in `EXEMPT` with a
reason), and the pairs that were fixed keep their targets: the right side of ẞ follows B and its left side H, Ĳ ĳ ŉ
follow the letters they are made of, `G.cv03` closes like O, the old-style 7 clears a colon, the hook of ƈ clears the
bar of T, and the marks of ǐ ǰ ḯ ǒ ě ḻ ṟ ṯ (and the diaeresis of ï ő) keep a gap to their neighbours. Accented lowercase letters clear the arm of T V W Y.
"""
import unicodedata
from functools import lru_cache
from pathlib import Path

import pytest
import ufoLib2
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen

from conftest import WEIGHTS, static_path

SOURCES = Path(__file__).resolve().parent.parent / "sources"
MASTERS = ["Thin", "Regular", "Black", "ThinItalic", "RegularItalic", "BlackItalic"]
MASTER_FONTS = [("Thin", False), ("Regular", False), ("Black", False), ("Thin", True), ("Regular", True), ("Black", True)]
MASTER_IDS = [f"{w}{'-italic' if i else ''}" for w, i in MASTER_FONTS]
ALL_FONTS = [(w, i) for i in (False, True) for w in WEIGHTS]
ALL_IDS = [f"{w}{'-italic' if i else ''}" for w, i in ALL_FONTS]

# Letters (and letter alternates) that are deliberately left without a kerning group.
EXEMPT = {
    "Ezh": "rare Latin letter, no kerning group upstream; spacing is by side bearings",
    "Ezhcaron": "rare Latin letter, no kerning group upstream; spacing is by side bearings",
    "ezh": "rare Latin letter, no kerning group upstream; spacing is by side bearings",
    "ezhcaron": "rare Latin letter, no kerning group upstream; spacing is by side bearings",
    "Ohm": "unit sign, not a letter of running text",
    "pi": "Greek letter used as a maths symbol",
    "florin": "currency sign",
    "literSign": "unit sign",
    "dcroat": "inherited from Public Sans without a right-hand group",
    "Ldot": "inherited from Public Sans: the italic masters have no right-hand group",
    "Ldot.ss03": "inherited from Public Sans: the italic masters have no right-hand group",
    "ldot": "inherited from Public Sans: the italic masters have no right-hand group",
    "ldot.ss03": "inherited from Public Sans: the italic masters have no right-hand group",
    "ldot.ss02": "follows ldot: the italic masters have no right-hand group",
    "ldot.ss02.ss03": "follows ldot: the italic masters have no right-hand group",
}


@lru_cache(maxsize=None)
def source(master):
    return ufoLib2.Font.open(SOURCES / f"OffentligSans-{master}.ufo")


def kerned_letters(font):
    """Encoded letters, and the cv / ss alternates of a letter."""
    letters = set()
    for glyph in font:
        if glyph.unicodes and unicodedata.category(chr(glyph.unicodes[0])) in ("Lu", "Ll"):
            letters.add(glyph.name)
    alternates = {
        n for n in font.keys() if (".cv" in n or ".ss" in n) and n.split(".")[0] in letters
    }
    return letters | alternates


@pytest.mark.parametrize("master", MASTERS)
def test_every_letter_and_letter_alternate_is_in_a_kern1_and_a_kern2_group(master):
    font = source(master)
    kern1 = {g for name, members in font.groups.items() if name.startswith("public.kern1.") for g in members}
    kern2 = {g for name, members in font.groups.items() if name.startswith("public.kern2.") for g in members}
    missing = sorted(n for n in kerned_letters(font) if (n not in kern1 or n not in kern2) and n not in EXEMPT)
    assert missing == []


def test_the_exempt_letters_all_exist():
    names = set(source("Regular").keys())
    assert [n for n in EXEMPT if n not in names] == []


@pytest.mark.parametrize("master", MASTERS)
def test_new_groups_hold_what_they_should(master):
    font = source(master)
    groups = font.groups
    assert "G.cv03" not in groups["public.kern1.G"]
    assert "G.cv03" in groups["public.kern1.Gcv03"] and "G.cv03" in groups["public.kern2.O"]
    assert "seven.osf" not in groups["public.kern2.seven"]
    assert groups["public.kern2.sevenosf"] == ["seven.osf"]
    assert "Germandbls" in groups["public.kern1.B"] and "Germandbls" in groups["public.kern2.N"]


class Shaper:
    """HarfBuzz at one font file: kerning values and the horizontal ink gap between the two glyphs of a pair."""

    STEP = 4

    def __init__(self, path):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.rows = {}

    def shape(self, text, features=None, kern=True):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, dict(features or {}, kern=kern))
        return [(i.codepoint, p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def kern(self, text, features=None):
        with_kern = self.shape(text, features)
        without = self.shape(text, features, kern=False)
        assert len(with_kern) == len(without) == 2, text
        return with_kern[0][1] - without[0][1]

    def spans(self, gid):
        if gid not in self.rows:
            points = []

            class Pen(BasePen):
                def _moveTo(self, p):
                    points.append([p])

                def _lineTo(self, p):
                    points[-1].append(p)

                def _curveToOne(self, a, b, c):
                    x0, y0 = points[-1][-1]
                    for i in range(1, 9):
                        t = i / 8
                        u = 1 - t
                        points[-1].append(
                            (
                                u**3 * x0 + 3 * u * u * t * a[0] + 3 * u * t * t * b[0] + t**3 * c[0],
                                u**3 * y0 + 3 * u * u * t * a[1] + 3 * u * t * t * b[1] + t**3 * c[1],
                            )
                        )

                def _qCurveToOne(self, a, c):
                    x0, y0 = points[-1][-1]
                    for i in range(1, 9):
                        t = i / 8
                        u = 1 - t
                        points[-1].append(
                            (u * u * x0 + 2 * u * t * a[0] + t * t * c[0], u * u * y0 + 2 * u * t * a[1] + t * t * c[1])
                        )

                def _closePath(self):
                    pass

            self.font.draw_glyph_with_pen(gid, Pen(None))
            low, high, step = -500, 2400, self.STEP
            rows = {}
            for contour in points:
                for k, (x0, y0) in enumerate(contour):
                    x1, y1 = contour[(k + 1) % len(contour)]
                    if y0 == y1:
                        continue
                    lo, hi = (y0, y1) if y0 < y1 else (y1, y0)
                    # rows y with lo <= y < hi, on the grid low + n * step
                    first = max(0, -((low - lo) // step) if lo > low else 0)
                    y = low + first * step
                    while y < hi and y < high:
                        if y >= lo:
                            x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                            span = rows.get(y)
                            rows[y] = (x, x) if span is None else (min(span[0], x), max(span[1], x))
                        y += step
            self.rows[gid] = rows
        return self.rows[gid]

    def gap(self, text, features=None):
        """Smallest horizontal distance between the ink of the first and the second glyph, over the rows both occupy."""
        (g1, advance), (g2, _) = self.shape(text, features)
        left, right = self.spans(g1), self.spans(g2)
        gaps = [advance + right[y][0] - left[y][1] for y in left if y in right]
        return min(gaps) if gaps else None


@lru_cache(maxsize=None)
def shaper(weight, italic):
    return Shaper(static_path(weight, italic))


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_eszett_kerns_like_b_on_the_right_and_like_h_on_the_left(weight, italic):
    s = shaper(weight, italic)
    for right in "TVYA":
        assert s.kern("ẞ" + right) == s.kern("B" + right)
    assert s.kern("ẞT") < 0 and s.kern("ẞY") < 0
    for left in "TVYAL":
        assert s.kern(left + "ẞ") == s.kern(left + "H")


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_ij_ligatures_kern_like_the_letters_they_are_made_of(weight, italic):
    s = shaper(weight, italic)
    for right in "AOTVYaoy.":
        assert s.kern("Ĳ" + right) == s.kern("J" + right)
        assert s.kern("ĳ" + right) == s.kern("j" + right)
        assert s.kern("ŉ" + right) == s.kern("n" + right)
    for left in "AOTVYaoy.":
        assert s.kern(left + "Ĳ") == s.kern(left + "I")
        assert s.kern(left + "ĳ") == s.kern(left + "i")
        assert s.kern(left + "ŉ") == s.kern(left + "’")
    assert s.kern("ĲA") < 0


@pytest.mark.parametrize("weight,italic", MASTER_FONTS, ids=MASTER_IDS)
def test_round_g_closes_like_o_next_to_a_period_and_an_a(weight, italic):
    s = shaper(weight, italic)
    for right in ".A":
        assert abs(s.gap("G" + right, {"cv03": True}) - s.gap("O" + right)) <= 25


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_oldstyle_seven_clears_a_colon(weight, italic):
    s = shaper(weight, italic)
    assert s.gap(":7", {"onum": True}) >= 30
    assert s.gap(":7", {"onum": True, "ss03": True}) >= 30


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_lining_seven_keeps_its_colon_kerning(weight, italic):
    """The lining 7 and the old-style 7 start from the same pairs; only the colon differs."""
    s = shaper(weight, italic)
    assert s.kern(".7") == s.kern(".7", {"onum": True})
    assert s.kern(":7", {"onum": True}) >= s.kern(":7")


@pytest.mark.parametrize("weight,italic", MASTER_FONTS, ids=MASTER_IDS)
def test_hook_of_c_hook_clears_the_bar_of_t_as_the_f_does(weight, italic):
    s = shaper(weight, italic)
    assert s.gap("ƈT") >= s.gap("fT") - 5
    assert s.gap("ƈY") >= 30


# (floor, neighbours) per character; both sides unless noted.
CLEARANCE = {
    "ǐ": (30, "bdfhijkqBEFHJKTVWXYZ7!'’\"()[]{}/\\|"),
    "ǰ": (30, "bdfhijkqBEFHJKTVWXYZ7!'’\"()[]{}/\\|"),
    "ḯ": (30, "bdfhijkqBCEFHJKOPSTVWXYZ0236789!?'’\"()[]{}/\\|*$<>%"),
    "ḻ": (30, "([{)]}jQq_|"),
    "ṟ": (30, "([{)]}jQq_|"),
    "ṯ": (30, "([{)]}jQq_|"),
    "ï": (8, "bdfhijkqBEFHJKTVWXYZ7!'’\"()[]{}/\\|"),
    "ő": (8, "bhklBEFHKPRTVWXY7!'’\"()[]{}\\"),
}
ARM_ONLY = {"ǒ": (30, "TYVW"), "ě": (30, "TYVW")}  # on the right side of the capital with an arm


@pytest.mark.parametrize("weight,italic", MASTER_FONTS, ids=MASTER_IDS)
@pytest.mark.parametrize("char", list(CLEARANCE))
def test_marks_and_hooks_keep_a_gap_to_their_neighbours(weight, italic, char):
    s = shaper(weight, italic)
    floor, neighbours = CLEARANCE[char]
    tight = []
    for n in neighbours:
        for text in (n + char, char + n):
            try:
                gap = s.gap(text)
            except AssertionError:
                continue  # ligature or substitution
            if gap is not None and gap < floor:
                tight.append((text, gap))
    assert tight == []


@pytest.mark.parametrize("weight,italic", MASTER_FONTS, ids=MASTER_IDS)
@pytest.mark.parametrize("char", list(ARM_ONLY))
def test_caron_clears_the_arm_of_t_y_v_w(weight, italic, char):
    s = shaper(weight, italic)
    floor, neighbours = ARM_ONLY[char]
    tight = [(n + char, s.gap(n + char)) for n in neighbours if (s.gap(n + char) or floor) < floor]
    assert tight == []


@pytest.mark.parametrize("master", MASTERS)
def test_ss02_forms_of_fl_and_ldot_sit_in_the_groups_of_their_parts(master):
    """`fl.ss02` is left like `fl` and right like `l.ss02`; `ldot.ss02` is left like `l.ss02` and right like `ldot`."""
    font = source(master)

    def group(side, glyph):
        return [n for n, members in font.groups.items() if n.startswith(f"public.{side}.") and glyph in members]

    assert group("kern1", "fl.ss02") == group("kern1", "l.ss02") and group("kern2", "fl.ss02") == group("kern2", "fl")
    assert group("kern1", "ldot.ss02") == group("kern1", "ldot") and group("kern2", "ldot.ss02") == group("kern2", "l.ss02")
    assert group("kern1", "ldot.ss02.ss03") == group("kern1", "ldot.ss03")
    assert group("kern2", "ldot.ss02.ss03") == group("kern2", "ldot.ss03")
    assert group("kern1", "fl.ss02") and group("kern2", "ldot.ss02")


def accented_lowercase(font):
    """Encoded lowercase letters that decompose into a base letter and a mark."""
    found = []
    for glyph in font:
        if glyph.unicodes:
            char = chr(glyph.unicodes[0])
            if unicodedata.category(char) == "Ll" and len(unicodedata.normalize("NFD", char)) > 1:
                found.append(char)
    return found


@pytest.mark.parametrize("features", [{}, {"cv04": True}, {"ss03": True}, {"cv04": True, "ss03": True}], ids=["default", "cv04", "ss03", "cv04-ss03"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_accented_lowercase_clears_the_arm_of_t_v_w_y(weight, italic, features):
    """Pair exceptions between the T, V and Y kern1 groups and each accented lowercase keep at least 30 units of ink
    between the arm and the mark, at every weight (the masters aim at 40), with no features and with the
    single-storey `a` (`cv04`), the round dots (`ss03`) or both."""
    s = shaper(weight, italic)
    tight = []
    for left in "TVWYŤẂŶ":
        for right in accented_lowercase(source("Regular")):
            try:
                gap = s.gap(left + right, features)
            except AssertionError:
                continue  # ligature or substitution
            if gap is not None and gap < 30:
                tight.append((left + right, round(gap)))
    assert tight == []


ROMANIAN_RIGHT = "abcdefghijklmnopqrstuvwxyzăâșț"
HORN_CAPITALS = "ƠỜỚỞỠỢƯỪỨỬỮỰ"


def vietnamese_lowercase(font):
    """Basic Latin lowercase and the Vietnamese letters, the lowercase that follows Ơ and Ư in running text."""
    letters = set("abcdefghijklmnopqrstuvwxyz")
    for glyph in font:
        if glyph.unicodes:
            char = chr(glyph.unicodes[0])
            if unicodedata.category(char) == "Ll" and (char in "đăâêôơưàáãèéẽìíĩòóõùúũỳýỹ" or 0x1EA0 <= ord(char) <= 0x1EF9):
                letters.add(char)
    return sorted(letters)


@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_circumflex_i_and_horn_capitals_clear_the_lowercase_that_follows(weight, italic):
    """The circumflex of î (Romanian) and the horn of Ơ Ư and their accented forms (Vietnamese) closed on the next
    lowercase letter in the heavy weights of Public Sans; pair exceptions aim at 40 units and the test fails below 30."""
    s = shaper(weight, italic)
    tight = []
    texts = ["î" + r for r in ROMANIAN_RIGHT]
    texts += [left + r for left in HORN_CAPITALS for r in vietnamese_lowercase(source("Regular"))]
    for text in texts:
        try:
            gap = s.gap(text)
        except AssertionError:
            continue  # ligature or substitution
        if gap is not None and gap < 30:
            tight.append((text, round(gap)))
    assert tight == []


CLOSING_PUNCTUATION = ")]}?!'\"’”»›"


@pytest.mark.parametrize("features", [{}, {"ss03": True}], ids=["default", "ss03"])
@pytest.mark.parametrize("weight,italic", ALL_FONTS, ids=ALL_IDS)
def test_accented_i_clears_the_closing_punctuation_after_it(weight, italic, features):
    """The accent of í î ï ĩ ī ĭ ǐ ȉ ȋ ḯ reaches over the stem and closed on `) ] } ? ! ' " ’ ” » ›` in the heavy
    weights of Public Sans (`(sí)`, `¿sí?`). Glyph-to-glyph pair exceptions aim at 40 units; the test fails below 30."""
    s = shaper(weight, italic)
    tight = []
    lefts = [c for c in accented_lowercase(source("Regular")) if unicodedata.normalize("NFD", c)[0] == "i"]
    # typed ị and ɨ with a top mark shape as one glyph (`idotbelow_acutecomb` and the others)
    lefts += [base + mark for base in "ịɨ" for mark in "\u0301\u0300\u0302\u0304\u0303"]
    for left in lefts:
        for right in CLOSING_PUNCTUATION:
            try:
                gap = s.gap(left + right, features)
            except AssertionError:
                continue  # ligature or substitution
            if gap is not None and gap < 30:
                tight.append((left + right, round(gap)))
    assert tight == []
