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
    def __init__(self, path, features, texts):
        """`texts`: strings that shape alone to one glyph; the others are dropped (`self.texts` keeps the survivors)."""
        self.shaper = Shaper(path)
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
        self.advance = np.array([self.shaper.shape(t, features)[0][1] for t in self.texts], dtype=np.float64)
        ink = {gid: self.shaper.spans(gid) for gid in set(self.gids)}
        self.lmax = np.full((len(self.texts), len(ROWS)), -np.inf)
        self.rmin = np.full((len(self.texts), len(ROWS)), np.inf)
        for i, gid in enumerate(self.gids):
            for y, (lo, hi) in ink[gid].items():
                k = int((y - LOW) // STEP)
                self.lmax[i, k] = hi
                self.rmin[i, k] = lo

    def glyph_name(self, i):
        return self.names[self.gids[i]]

    def kerning(self, left, right, chunk=2000):
        """Matrix of the kerning of the first glyph for `left` x `right` (indexes into `self.texts`), NaN where the pair
        is not two glyphs (a ligature or a substitution)."""
        out = np.full((len(left), len(right)), np.nan)
        pairs = [(a, b) for a in range(len(left)) for b in range(len(right))]
        for start in range(0, len(pairs), chunk):
            part = pairs[start : start + chunk]
            text, offsets = "", []
            for a, b in part:
                offsets.append(len(text))
                text += self.texts[left[a]] + self.texts[right[b]] + " "
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
                if len(members) == 3 and infos[members[0]].codepoint == self.gids[left[a]] and infos[members[1]].codepoint == self.gids[right[b]]:
                    out[a, b] = positions[members[0]].x_advance - self.hmtx[self.names[self.gids[left[a]]]][0]
        return out

    def gaps(self, left, right, kern):
        """Matrix of the ink gap (inf where the glyphs share no row), with `kern` from `kerning`."""
        out = np.full((len(left), len(right)), np.inf)
        right_rows = self.rmin[right]
        for a, i in enumerate(left):
            out[a] = (right_rows - self.lmax[i]).min(axis=1)
        return out + self.advance[left][:, None] + kern
