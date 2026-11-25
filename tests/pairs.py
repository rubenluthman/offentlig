"""Whole-font pair measurements: kerning and ink gap of every pair of a list of texts at one static font.

`Shaper.gap` in test_spacing.py measures one pair; this does the same for hundreds of thousands. Texts are shaped in
batches (each pair followed by a space, which no pair kerns with) and the gaps are taken with numpy over 4-unit rows.
"""
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from test_spacing import Shaper

LOW, HIGH, STEP = -500, 2400, 4
ROWS = np.arange(LOW, HIGH, STEP)


class PairTable:
    def __init__(self, path, features, texts, shaper=None):
        """`texts`: strings that shape alone to one glyph; the others are dropped (`self.texts` keeps the survivors).
        `shaper`: a `Shaper` of the same font to share, so the outline rows of a glyph are measured once."""
        self.shaper = shaper or Shaper(path)
        self.features = dict(features or {}, kern=True)
        self.hmtx = TTFont(path)["hmtx"].metrics
        order = TTFont(path).getGlyphOrder()
        self.names = order
        self.texts, self.gids = [], []
        for text in texts:
            shaped = self.shaper.shape(text, features)
            if len(shaped) == 1:
                self.texts.append(text)
                self.gids.append(shaped[0][0])
        self.index = {t: i for i, t in enumerate(self.texts)}
        # (left, right) -> glyph id `calt` or `rclt` put in place of the first glyph, set by `kerning_pairs`
        self.first_shaped = {}
        self._rows = {}
        self.advance = np.array([self.shaper.shape(t, features)[0][1] for t in self.texts], dtype=np.float64)
        self.lmax = np.full((len(self.texts), len(ROWS)), -np.inf)
        self.rmin = np.full((len(self.texts), len(ROWS)), np.inf)
        for i, gid in enumerate(self.gids):
            ink = self.shaper.spans(gid)  # the same grid as ROWS
            self.lmax[i] = ink.hi
            self.rmin[i] = ink.lo

    def codepoint_of(self, name):
        """The code point the built font encodes `name` at, or None."""
        if not hasattr(self, "_codes"):
            self._codes = {n: c for c, n in TTFont(self.shaper.path).getBestCmap().items()}
        return self._codes.get(name)

    def first_rows(self, a, b):
        """(rightmost ink per row, advance) of the glyph shaped for the first glyph of the pair (a, b)."""
        gid = self.first_shaped.get((a, b))
        if gid is None:
            return self.lmax[a], self.advance[a]
        if gid not in self._rows:
            row = self.shaper.spans(gid).hi
            self._rows[gid] = (row, float(self.hmtx[self.names[gid]][0]))
        return self._rows[gid]

    def glyph_name(self, i):
        return self.names[self.gids[i]]

    def kerning(self, left, right, chunk=2000):
        """Matrix of the kerning of the first glyph for `left` x `right` (indexes into `self.texts`), NaN where the pair
        is not two glyphs (a ligature or a substitution of the second glyph). A first glyph that `calt` or `rclt` swapped
        is measured as shaped (`first_shaped`)."""
        out = np.empty((len(left), len(right)))
        rows = max(1, chunk // max(1, len(right)))  # a block of rows at a time: the list of all pairs is never built
        for start in range(0, len(left), rows):
            block = left[start : start + rows]
            out[start : start + len(block)] = np.array(self.kerning_pairs([(a, b) for a in block for b in right], chunk)).reshape(len(block), len(right))
        return out

    def kerning_pairs(self, pairs, chunk=2000):
        """List of the kerning of the first glyph of each (left, right) pair of indexes into `self.texts` (NaN as in `kerning`)."""
        out = []
        for start in range(0, len(pairs), chunk):
            part = pairs[start : start + chunk]
            text, offsets = "", []
            for a, b in part:
                offsets.append(len(text))
                text += self.texts[a] + self.texts[b] + " "
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(self.shaper.font, buf, self.features)
            infos, positions = buf.glyph_infos, buf.glyph_positions
            at = 0
            for n, (a, b) in enumerate(part):
                end = offsets[n + 1] if n + 1 < len(part) else len(text)
                members = []
                while at < len(infos) and infos[at].cluster < end:
                    members.append(at)
                    at += 1
                value = np.nan
                if len(members) == 3 and infos[members[1]].codepoint == self.gids[b]:
                    shaped = infos[members[0]].codepoint
                    if shaped != self.gids[a]:
                        self.first_shaped[(a, b)] = shaped
                    value = positions[members[0]].x_advance - self.hmtx[self.names[shaped]][0]
                out.append(value)
        return out

    def gaps(self, left, right, kern):
        """Matrix of the ink gap (inf where the glyphs share no row), with `kern` from `kerning`."""
        out = np.full((len(left), len(right)), np.inf)
        right_rows = self.rmin[right]
        for a, i in enumerate(left):
            out[a] = (right_rows - self.lmax[i]).min(axis=1)
        out = out + self.advance[left][:, None] + kern
        if self.first_shaped:  # pairs whose first glyph was swapped: their own ink and advance
            where_left, where_right = {i: n for n, i in enumerate(left)}, {j: n for n, j in enumerate(right)}
            for (a, b) in self.first_shaped:
                if a in where_left and b in where_right:
                    n, m = where_left[a], where_right[b]
                    rows, advance = self.first_rows(a, b)
                    out[n, m] = float((self.rmin[b] - rows).min()) + advance + kern[n, m]
        return out

    def gaps_pairs(self, pairs, kern):
        """List of the ink gap of each (left, right) pair of indexes (inf where the glyphs share no row), with `kern` from `kerning_pairs`."""
        out = []
        for (a, b), k in zip(pairs, kern):
            rows, advance = self.first_rows(a, b)
            out.append(float((self.rmin[b] - rows).min()) + advance + k)
        return out
