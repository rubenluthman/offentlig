# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- [x] Audit every design and spacing decision before work on Offentlig Serif and Offentlig Mono starts, since they will reuse these rules (completed in 0.4.0; see [docs/design-decisions.md](docs/design-decisions.md) and `tests/test_diagonal_gaps.py`).
- [ ] Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md#releases)).
- [ ] The shape of the ogonek. Public-sans issue #158 names it without a target, so take one from a reference design, such as Libre Franklin (the source of Public Sans), and check it on the Polish and Lithuanian letters.
- [ ] Typed accents after `T V W Y` outside the covered set. The helper capitals cover grave, macron, tilde, breve and caron on the lowercase DIN 91379, Yoruba, Igbo and Lithuanian sequences; other marks on bases with no precomposed form (`Tc̏`, double grave, dieresis, candrabindu, ring) keep the 0.4.0 spacing and can collide, worst in Black.
- [ ] Survey the whole font for places where a contextual swap to a hidden helper glyph would fix a collision or a fit that kerning alone cannot, such as a shorter `T` crossbar before a tall accent, or `T Y` before `ä ö` in Black, where `Tö` is kerned 38 units looser than `To` and `Yö` 130 units looser than `Yo`. List each case with its measurements before drawing any. Helper forms that change how a letter looks go in `calt`, so apps can turn them off, unless that forces a compromise.
- [ ] Case-sensitive forms (`case`) for the hyphen, dashes, parentheses, brackets and `@`, which sit lower than the middle of the capitals and figures. Swap them in through `calt` between capitals or figures (`A–Ö`, `2026-11-18`), and raise the colon between figures (`12:30`).
- [x] Add the figure space (U+2007), punctuation space (U+2008), thin space (U+2009) and narrow no-break space (U+202F, used to group digits in Swedish and French numbers).
- [x] Name `cv01` – `cv06` in the font, as `ss01` – `ss03` already are, so apps such as the macOS Typography panel show what each one does. Done since #8 and #17: the font carries `cvParameters` (label, tooltip, sample text), and Core Text (`CTFontCopyFeatures`, the list behind the panel) returns them as the features Wider J, G without spur, Single-storey a, I with serifs and 1 with base, each with Off and On. `cv02` does not exist and `cv06` is the 1 with base.
- [ ] The ring on `Å` and the diaeresis on `ä ö`: measure their size, height and gap against the reference fonts before redrawing. The ring of `Å` reaches above the ascender used for line spacing.
- [ ] Joins in Bold to Black (the link of `g`, the crotches of `M N W`, the bowl joins of `a b d p q`): measure how dark they get against the reference fonts before thinning any or adding ink traps.
- [x] In Black, the narrow double grave on `ȉ` still overhangs the advance by 35 units more than the breve on `ĭ`.
- [x] Replace the single-pair kerning exceptions added for the narrow double grave with group kerning where the result is the same.
- [ ] Even out `make test`: one worker runs the longest tests alone at the end of the run.
- [ ] Review which alternates should become the default form, which would revisit decision F4 (alternates are opt-in). Do this after every other Offentlig Sans item above.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- [ ] Adapt IBM Plex Serif, weights 100 – 700.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Mono
<!-- vale HouseStyle.Headings = YES -->

- [ ] Adapt IBM Plex Mono, weights 100 – 700.

## Icebox

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- [ ] Cyrillic, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Cyrillic, to measure proportions from, and check whether issue #17 points to existing work. Reuse the letters Cyrillic shares with Latin, and build the lowercase letters shaped like small capitals from Offentlig's capitals, with the stroke weight corrected. For the rest, make a first draft: measure stem width, x-height, contrast, width and slant in the reference font and in Offentlig, apply those ratios to the reference font's letters as whole-letter changes, then redraw the curves and stroke ends in Offentlig's details. Check the reference font's licence first.
- [ ] Greek, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Greek, to measure proportions from. Reuse the capitals Greek shares with Latin, and draft the rest, above all the lowercase, the same way as Cyrillic: apply the measured ratios to the reference font's letters, then redraw them in Offentlig's details.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- [ ] A Black master of our own, extending the weight axis from 700 to 900 to match Offentlig Sans.
