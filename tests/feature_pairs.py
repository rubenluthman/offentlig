"""Pair rules with the alternate forms on: every pair that has a glyph the features change, at one static.

`test_plain_pairs.py` and `test_accent_pairs.py` hold every pair of characters with no feature, with `ss03` and with `cv04`.
The other features swap glyphs whose bearings differ from the default ones, so each pair with a swapped glyph on either side
is measured here, with the same two rules (plain pairs keep 30 units; a pair with an accented letter keeps the smaller of the
gap of the same pair with the base letters and 30 units, less 2). Pairs where neither glyph changes are the default pairs
and are not measured again.
"""
from functools import lru_cache

import numpy as np

from conftest import static_path
from pairs import PairTable
from test_accent_pairs import FLOOR, accent_violation, base_of, diaeresis_pair, encoded_texts, is_accented
from test_plain_pairs import plain_violation
from test_spacing import shaper, source, ufo_glyph_name

ALL_FEATURES = ["ss01", "ss02", "ss03", "cv01", "cv03", "cv04", "cv05", "cv06", "zero", "onum", "case"]
# Each alternate on its own, then the combinations where two alternates meet in one pair.
ALTERNATE_SETS = {
    **{name: {name: True} for name in ("ss01", "ss02", "cv01", "cv03", "cv04", "cv05", "cv06", "zero", "onum", "case")},
    "cv04+ss03": {"cv04": True, "ss03": True},
    "salt+ss03": {"salt": True, "ss03": True},
    "onum+zero+cv06": {"onum": True, "zero": True, "cv06": True},
    **{f"{name}+ss03": {name: True, "ss03": True} for name in ("ss01", "ss02", "cv01", "cv03", "cv05", "cv06", "zero", "onum", "case")},
    "all": {name: True for name in ALL_FEATURES},
    "all, lining figures": {name: True for name in ALL_FEATURES if name != "onum"},
}


class FeaturePairs:
    """The pair table of every encoded text at one static, shaped with one feature set, and which texts the features change."""

    def __init__(self, weight, italic, features, texts=None):
        """`texts`: the texts to measure (default: every encoded text); see `combination_texts` for the small set of a combination."""
        self.weight = weight
        self.italic = italic
        s = shaper(weight, italic)
        self.table = PairTable(static_path(weight, italic), features, texts if texts is not None else encoded_texts(weight, italic), shaper=s)
        t = self.table
        default = [s.shape(text) for text in t.texts]
        self.changed = np.array([len(d) != 1 or d[0][0] != gid for d, gid in zip(default, t.gids)])
        self.accented = np.array([is_accented(x) for x in t.texts])
        self.reference = np.array([t.index.get(base_of(x), -1) if a else i for i, (x, a) in enumerate(zip(t.texts, self.accented))])

    def pair_chunks(self, focus=(), size=20000):
        """Lists of at most `size` pairs, in the order of `pairs`: the pairs are never all in memory at once. `focus`: texts to add
        to the changed ones, "all", or "meeting" for the pairs whose two glyphs are both changed."""
        n = len(self.table.texts)
        if focus == "meeting":  # only pairs with a changed glyph on both sides: where two alternates meet
            changed, rows = self.changed, [int(a) for a in np.nonzero(self.changed)[0]]
        else:
            changed = np.ones(n, dtype=bool) if focus == "all" else self.changed | np.isin(self.table.texts, list(focus))
            rows = range(n)
        columns = [int(b) for b in np.nonzero(changed)[0]]
        chunk = []
        for a in rows:
            for b in range(n) if changed[a] and focus != "meeting" else columns:
                chunk.append((a, b))
                if len(chunk) >= size:
                    yield chunk
                    chunk = []
        if chunk:
            yield chunk

    def pairs(self, focus=()):
        """Indexes (left, right) of every pair with a changed glyph on either side (and with a text of `focus`)."""
        return [pair for chunk in self.pair_chunks(focus) for pair in chunk]

    def measure(self, pairs):
        """(gap, reference gap or inf, kerning) of each pair; gap is NaN where the pair is not two glyphs."""
        t = self.table
        kern = t.kerning_pairs(pairs)
        gap = t.gaps_pairs(pairs, kern)
        refs = [
            (int(self.reference[a]), int(self.reference[b])) if self.reference[a] >= 0 and self.reference[b] >= 0 else None
            for a, b in pairs
        ]
        todo = sorted({r for r in refs if r})
        ref_kern = t.kerning_pairs(todo)
        ref_gap = dict(zip(todo, t.gaps_pairs(todo, ref_kern)))
        ref = [ref_gap.get(r, np.inf) if r else np.inf for r in refs]
        ref = [np.inf if np.isnan(r) else r for r in ref]
        return gap, ref, kern

    def violations(self, focus=()):
        """List of (left index, right index, text of the pair, gap, reference gap, rule) for every pair that breaks a rule."""
        out = []
        for pairs in self.pair_chunks(focus):
            gap, ref, _ = self.measure(pairs)
            for (a, b), g, r in zip(pairs, gap, ref):
                if np.isnan(g):
                    continue
                ta, tb = self.table.texts[a], self.table.texts[b]
                if self.accented[a] or self.accented[b]:
                    found = accent_violation(ta, tb, self.accented[a], self.accented[b], g, r, self.weight, self.italic)
                    rule = "accent"
                else:
                    found = plain_violation(ta, tb, g)
                    rule = "plain"
                if found:
                    out.append((a, b, ta + tb, found[1], found[2] if rule == "accent" else None, rule))
        return out

    def requirement(self, a, b, ref):
        """(floor of the test, floor to fit to, aim) in units for a pair, or None where the pair is left out of the rules."""
        ta, tb = self.table.texts[a], self.table.texts[b]
        if self.accented[a] or self.accented[b]:
            probe = accent_violation(ta, tb, self.accented[a], self.accented[b], -1e9, ref, self.weight, self.italic)
            if probe is None:
                return None
            if diaeresis_pair(ta, tb, self.weight, self.italic):
                return 8, 8, 12
            if probe[2] is None:
                return FLOOR, FLOOR, 40
            return min(ref, FLOOR) - 2, min(ref, FLOOR), min(ref, 40)
        if plain_violation(ta, tb, -1e9) is None:
            return None
        return FLOOR, FLOOR, 40

    def glyph_names(self, index):
        """The source name of a shaped glyph; the built font uses production names (`Euro` for `euro`, `uni01E5` for `gstroke`)."""
        font, name = source("Regular"), self.table.glyph_name(index)
        base, dot, suffix = name.partition(".")
        if base in font:
            return name
        code = self.table.codepoint_of(base)
        return next((g.name for g in font if code in g.unicodes), base) + dot + suffix


@lru_cache(maxsize=None)
def changed_texts(weight, italic, feature):
    """The encoded texts that shape to something else with `feature` on alone."""
    s = shaper(weight, italic)
    return frozenset(t for t in encoded_texts(weight, italic) if s.shape(t, {feature: True}) != s.shape(t))


def combination_texts(weight, italic, features):
    """The texts to measure for a combination of alternates: every text one of the features changes (a text two features change
    is shaped with both on), and the base letters of the accented ones, which the accent rule compares against. Pairs of these
    with a changed glyph on both sides are the pairs in which two alternates can meet."""
    changed = set().union(*(changed_texts(weight, italic, f) for f in features))
    wanted = changed | {base_of(t) for t in changed if is_accented(t)}
    return [t for t in encoded_texts(weight, italic) if t in wanted]


def alternate_violations(weight, italic, name):
    """Pairs with a swapped glyph that break the plain or accent rule, as (pair text, gap, reference gap, rule)."""
    found = FeaturePairs(weight, italic, ALTERNATE_SETS[name]).violations()
    return [(text, gap, ref, rule) for _, _, text, gap, ref, rule in found]
