"""Stored `top` and `bottom` anchors of accented composites agree with what ufo2ft's anchor propagation gives.

A typed mark attaches to the stored anchor of the composite (`Gdotaccent.cv03` + U+0301). An alternate built on a
letter alternate that kept the base letter's `top` at letter height would put the typed mark on the existing accent.
The stored anchor must therefore sit where the propagated one does: the `top` of the last mark above the base.
"""
from pathlib import Path

import pytest
import ufoLib2
from ufo2ft.filters.propagateAnchors import anchors_traversing_components

SOURCES = Path(__file__).resolve().parent.parent / "sources"
UFOS = [f"OffentligSans-{w}{s}.ufo" for s in ("", "Italic") for w in ("Thin", "Regular", "Black")]
TOLERANCE = 1.0  # font units (2000 per em)
NAMES = ("top", "bottom")


def _categories(font):
    return font.lib.get("public.openTypeCategories", {})


def _propagate(font, name, done, categories, own=True):
    glyph = font[name]
    existing = [a for a in glyph.anchors] if own else []
    return anchors_traversing_components(
        name,
        existing,
        glyph.components,
        categories.get(name) == "mark",
        categories.get(name) == "ligature",
        done,
        {},
    )


def _done_anchors(font, categories):
    """Anchors of every glyph as the build sees them: stored anchors win, missing ones come from the components."""
    done, pending = {}, [g.name for g in font]
    counts = {}
    while pending:
        later = []
        for name in pending:
            glyph = font[name]
            if any(c.baseGlyph not in done for c in glyph.components if c.baseGlyph in font):
                later.append(name)
                continue
            done[name] = anchors_traversing_components(
                name, list(glyph.anchors), glyph.components,
                categories.get(name) == "mark", categories.get(name) == "ligature", done, counts,
            )
        assert len(later) < len(pending), "cyclic components"
        pending = later
    return done


def in_scope(font, glyph, categories):
    """Plain base-plus-mark composites: one base first, then marks only, no contours.

    Not in scope: ligatures (more than one base), glyphs that mix contours and components, glyphs whose first
    component is a mark (the o-horn and u-horn letters list the mark first), and composites whose extra components
    are not marks (`Ldot`).
    """
    parts = glyph.components
    if glyph.contours or len(parts) < 2:
        return False
    if categories.get(glyph.name) in ("mark", "ligature"):
        return False
    if categories.get(parts[0].baseGlyph) == "mark":
        return False
    return all(categories.get(c.baseGlyph) == "mark" for c in parts[1:])


# Glyphs left out although in scope. Each needs a one-line reason.
EXCLUDED = {
    "tcaron": "the caron stands beside the stem, so `top` sits above the caron (ink top) and not on the stem top (tests/test_mark_anchors.py)",
}


def drift(font):
    """(glyph, anchor name, stored y, propagated y, stored x, propagated x) for every anchor off by more than TOLERANCE."""
    categories = _categories(font)
    done = _done_anchors(font, categories)
    bad = []
    for glyph in font:
        if glyph.name in EXCLUDED or not in_scope(font, glyph, categories):
            continue
        propagated = {a.name: a for a in _propagate(font, glyph.name, done, categories, own=False)}
        stored = {a.name: a for a in glyph.anchors}
        for name in NAMES:
            if name not in propagated:
                continue
            want, have = propagated[name], stored.get(name)
            if have is None or abs(have.y - want.y) > TOLERANCE or abs(have.x - want.x) > TOLERANCE:
                bad.append((glyph.name, name, have and round(have.x, 1), have and round(have.y, 1), round(want.x, 1), round(want.y, 1)))
    return bad


@pytest.mark.parametrize("ufo", UFOS)
def test_stored_anchors_match_propagated_anchors(ufo):
    font = ufoLib2.Font.open(SOURCES / ufo)
    categories = _categories(font)
    assert sum(in_scope(font, g, categories) for g in font) > 300
    bad = drift(font)
    assert not bad, f"{ufo}: stored anchors off by more than {TOLERANCE} (glyph, anchor, stored x, y, propagated x, y): {bad}"


def _anchors(font, name):
    return {a.name: (a.x, a.y) for a in font[name].anchors}


def mark_offsets(font, glyph):
    """For each mark of a composite, how far it sits from the anchor of the preceding component it attaches to: (index, dx, dy)."""
    out = []
    for index, comp in enumerate(glyph.components[1:], start=1):
        mark = _anchors(font, comp.baseGlyph)
        attach = [k for k in mark if k.startswith("_")]
        if not attach:
            continue
        name = attach[0][1:]
        target = next((c for c in reversed(glyph.components[:index]) if name in _anchors(font, c.baseGlyph)), None)
        if target is None:
            continue
        tx, ty = _anchors(font, target.baseGlyph)[name]
        dx = comp.transformation[4] - (tx + target.transformation[4] - mark[attach[0]][0])
        dy = comp.transformation[5] - (ty + target.transformation[5] - mark[attach[0]][1])
        out.append((index, dx, dy))
    return out


MARK_TOLERANCE = 2.0  # font units

# `.ss03` glyphs left out of the offset check. Each needs a one-line reason.
SS03_EXCLUDED = {
    "candrabinducomb.ss03": "a dot centred in a breve: it has no anchor to attach to (tests/test_wagner_italic_marks.py checks it)",
}


@pytest.mark.parametrize("ufo", UFOS)
def test_ss03_marks_sit_on_their_anchors_or_where_the_plain_glyph_has_them(ufo):
    """In a `.ss03` composite each mark is on its anchor, or at the offset the plain (square-dot) glyph has it, within 2 units.

    A few plain glyphs keep a deliberate offset (the dots over the dotless i, the horn and breve in italic); the round-dot
    form keeps it. Anything else means the mark was left behind when the dot or the anchor moved.
    """
    font = ufoLib2.Font.open(SOURCES / ufo)
    bad, checked = [], 0
    for glyph in font:
        if not glyph.name.endswith(".ss03") or glyph.contours or len(glyph.components) < 2 or glyph.name in SS03_EXCLUDED:
            continue
        plain = font[glyph.name.removesuffix(".ss03")] if glyph.name.removesuffix(".ss03") in font else None
        reference = {i: (dx, dy) for i, dx, dy in mark_offsets(font, plain)} if plain is not None and len(plain.components) == len(glyph.components) else {}
        for index, dx, dy in mark_offsets(font, glyph):
            checked += 1
            if abs(dx) <= MARK_TOLERANCE and abs(dy) <= MARK_TOLERANCE:
                continue
            want = reference.get(index)
            if want is None or abs(dx - want[0]) > MARK_TOLERANCE or abs(dy - want[1]) > MARK_TOLERANCE:
                bad.append((glyph.name, glyph.components[index].baseGlyph, round(dx, 1), round(dy, 1), want and tuple(round(v, 1) for v in want)))
    assert checked > 100
    assert not bad, f"{ufo}: marks off their anchor and not as in the plain glyph (glyph, mark, dx, dy, plain offset): {bad}"


WIDTH_BASES = {"cv01": "J", "cv03": "G", "cv04": "a", "cv05": "I"}
WIDTH_TOLERANCE = 0.5  # font units


def _expected_width(font, name):
    """Width an alternate must have, against its plain glyph, or None when the rule does not apply.

    `X.cvNN` is as much wider than `X` as the alternate base is wider than the plain base:
    width(X.cvNN) = width(X) + width(base.cvNN) - width(base). An `.ss03` form keeps the width of its non-`.ss03` glyph.
    Deliberately different widths of the plain glyph (the accented italic a, `ď ľ ť`, `ő ű`) carry over, because the
    comparison is alternate against plain, not plain against base.
    """
    if name.endswith(".ss03"):
        plain = name.removesuffix(".ss03")
        return font[plain].width if plain in font else None
    stem, dot, tag = name.rpartition(".")
    if not dot or tag not in WIDTH_BASES:
        return None
    base = WIDTH_BASES[tag]
    if stem not in font or base not in font or f"{base}.{tag}" not in font:
        return None
    return font[stem].width + font[f"{base}.{tag}"].width - font[base].width


@pytest.mark.parametrize("ufo", UFOS)
def test_alternate_widths_follow_their_plain_glyph(ufo):
    """Every `X.cvNN` and `X.ss03` glyph is as wide as its plain glyph plus the width the alternate base adds, within 0.5 units.

    Not checked: the ligatures `IJ.*` (two letters, each with its own alternate form).
    """
    font = ufoLib2.Font.open(SOURCES / ufo)
    bad, checked = [], 0
    for glyph in font:
        if glyph.name.startswith("IJ"):
            continue
        want = _expected_width(font, glyph.name)
        if want is None:
            continue
        checked += 1
        if abs(glyph.width - want) > WIDTH_TOLERANCE:
            bad.append((glyph.name, round(glyph.width, 1), round(want, 1)))
    assert checked > 200
    assert not bad, f"{ufo}: width differs from the plain glyph plus the alternate base's extra width (glyph, width, expected): {bad}"
