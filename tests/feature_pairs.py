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
from test_accent_pairs import AIM, accent_violation, base_of, encoded_texts, is_accented
from test_plain_pairs import plain_violation
from test_spacing import LEFT_FOR_THE_ICEBOX, shaper, source, ufo_glyph_name

ALL_FEATURES = ["ss01", "ss02", "ss03", "cv01", "cv03", "cv04", "cv05", "cv06", "zero", "onum"]
# Each alternate on its own, then the combinations where two alternates meet in one pair.
ALTERNATE_SETS = {
    **{name: {name: True} for name in ("ss01", "ss02", "cv01", "cv03", "cv05", "cv06", "zero", "onum")},
    "cv04+ss03": {"cv04": True, "ss03": True},
    "salt+ss03": {"salt": True, "ss03": True},
    "onum+zero+cv06": {"onum": True, "zero": True, "cv06": True},
    "all": {name: True for name in ALL_FEATURES},
}


class FeaturePairs:
    """The pair table of every encoded text at one static, shaped with one feature set, and which texts the features change."""

    def __init__(self, weight, italic, features):
        s = shaper(weight, italic)
        self.table = PairTable(static_path(weight, italic), features, encoded_texts(weight, italic), shaper=s)
        t = self.table
        default = [s.shape(text) for text in t.texts]
        self.changed = np.array([len(d) != 1 or d[0][0] != gid for d, gid in zip(default, t.gids)])
        self.accented = np.array([is_accented(x) and x not in LEFT_FOR_THE_ICEBOX for x in t.texts])
        self.reference = np.array([t.index.get(base_of(x), -1) if a else i for i, (x, a) in enumerate(zip(t.texts, self.accented))])

    def pairs(self, focus=()):
        """Indexes (left, right) of every pair with a changed glyph on either side (and with a text of `focus`)."""
        n = len(self.table.texts)
        if focus == "all":
            return [(a, b) for a in range(n) for b in range(n)]
        changed = np.nonzero(self.changed | np.isin(self.table.texts, list(focus)))[0]
        pairs = {(int(a), b) for a in changed for b in range(n)} | {(a, int(b)) for b in changed for a in range(n)}
        return sorted(pairs)

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
        pairs = self.pairs(focus)
        gap, ref, _ = self.measure(pairs)
        out = []
        for (a, b), g, r in zip(pairs, gap, ref):
            if np.isnan(g):
                continue
            ta, tb = self.table.texts[a], self.table.texts[b]
            if self.accented[a] or self.accented[b]:
                found = accent_violation(ta, tb, self.accented[a], self.accented[b], g, r)
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
            probe = accent_violation(ta, tb, self.accented[a], self.accented[b], -1e9, ref)
            if probe is None:
                return None
            if probe[2] is None:
                return AIM, AIM, 40
            return min(ref, AIM) - 2, min(ref, AIM), min(ref, 40)
        if plain_violation(ta, tb, -1e9) is None:
            return None
        return AIM, AIM, 40

    def glyph_names(self, index):
        """The source name of a shaped glyph; the built font uses production names (`Euro` for `euro`, `uni01E5` for `gstroke`)."""
        font, name = source("Regular"), self.table.glyph_name(index)
        base, dot, suffix = name.partition(".")
        if base in font:
            return name
        code = self.table.codepoint_of(base)
        return next((g.name for g in font if code in g.unicodes), base) + dot + suffix


def alternate_violations(weight, italic, name):
    """Pairs with a swapped glyph that break the plain or accent rule, as (pair text, gap, reference gap, rule)."""
    found = FeaturePairs(weight, italic, ALTERNATE_SETS[name]).violations()
    return [(text, gap, ref, rule) for _, _, text, gap, ref, rule in found]
