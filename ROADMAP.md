# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- [ ] The alternate-pair tests hold about 1 GB of pair lists per pytest worker. Work through the pairs in chunks, so each worker uses less memory and more workers can run at once.
- [x] Audit every design and spacing decision before work on Offentlig Serif and Offentlig Mono starts, since they will reuse these rules (completed in 0.4.0; see [docs/design-decisions.md](docs/design-decisions.md) and `tests/test_diagonal_gaps.py`).
- [ ] Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md#releases)).
- [ ] The shape of the ogonek. Public-sans issue #158 names it without a target, so take one from a reference design, such as Libre Franklin (the source of Public Sans), and check it on the Polish and Lithuanian letters.
- [x] Typed accents after `T V W Y` outside the covered set: left as they are. Measured on the 18 statics, 51 typed sequences on bases outside K19 still come within 28 units of `T V W Y F P` (`j̆ q̆ z̆ g̀ r̀ v̀ x̀ c̈ g̈ j̄ q̄ j̃`, the double grave on 13 bases), none of them an orthography; the worst overlap is 338 units in Black, against 396 in Public Sans. Twenty of them would take the existing swap with more bases and no new class.
- [x] Survey of places where a contextual swap to a hidden helper glyph fixes what kerning cannot: `T Y` before `ä ö` and the letters like them in the heavy weights are done (K20, `calt`). Left as they are: `T V W Y F P` before the narrow `i`, `j`, `r` with a mark (`Tîrgu`, `Tĩnh`; a cut of 115 – 160 units in Black), the double grave (260 – 360) and `è ò ờ` after `Y` and `T`.
- [x] Case-sensitive forms (`case`) for the hyphen, dashes, parentheses, brackets, `@` and the colon, swapped in through `calt` between capitals or figures (unreleased; see F4 and F18 in [docs/design-decisions.md](docs/design-decisions.md)). Other characters that sit low next to capitals (guillemets, `¡ ¿`, the slash, the bullet) are not covered.
- [x] Add the figure space (U+2007), punctuation space (U+2008), thin space (U+2009) and narrow no-break space (U+202F, used to group digits in Swedish and French numbers).
- [x] Name `cv01` – `cv06` in the font, as `ss01` – `ss03` already are, so apps such as the macOS Typography panel show what each one does. Done since #8 and #17: the font carries `cvParameters` (label, tooltip, sample text), and Core Text (`CTFontCopyFeatures`, the list behind the panel) returns them as the features Wider J, G without spur, Single-storey a, I with serifs and 1 with base, each with Off and On. `cv02` does not exist and `cv06` is the 1 with base.
- [ ] The ring on `Å` and the diaeresis on `ä ö`: measure their size, height and gap against the reference fonts before redrawing. The ring of `Å` reaches above the ascender used for line spacing.
- [ ] Joins in Bold to Black (the link of `g`, the crotches of `M N W`, the bowl joins of `a b d p q`): measure how dark they get against the reference fonts before thinning any or adding ink traps.
- [x] In Black, the narrow double grave on `ȉ` still overhangs the advance by 35 units more than the breve on `ĭ`.
- [x] Replace the single-pair kerning exceptions added for the narrow double grave with group kerning where the result is the same.
- [x] Even out `make test`: idle workers now take waiting tests (`--dist worksteal`), and the run uses three workers.
- [ ] Make the round dots of `ss03` the default and move the square dots to `ss03`, so Offentlig Sans uses the circular dot of IBM Plex, which Offentlig Serif and Mono will adapt. Widths stay the same.
- [ ] Pairs of `T V W Y` with the narrow `i` and a mark are looser than their gap needs (Regular `Tĩ` is 61 units looser than `Ti` at a gap of 92). Find the cause before changing any value.
- [ ] Case forms for the other characters that sit low next to capitals: guillemets, `¡ ¿`, the slash and the bullet.
- [ ] Fix `calt` bracket raising so parentheses and brackets never come out mismatched (`f1a8c0cb`): checking each bracket against only its own two neighbours raises one end and leaves the other low in ordinary text and times (`(9:00)`, `(born 1984)`, `(2026 edition)`, `(A-12)`, `(12-A)`), leaves both low on `(1-2)` and outer `((HEJ))`, and raises `]` in `(1]`. Either bound brackets to matching all-caps or figure runs (including `-`, `–` and `:`) or keep brackets in `case` only.
- [ ] Re-examine the Black and Black Italic `Y.arm` outline (`3a08b870`): shifting the top two points of the right arm straight left by 126 units (142 italic) without adjusting the crotch or top width steepens the inner edge by 12 degrees (61 to 73 degrees upright), widens the top stroke and pinches the crotch. Show before-and-after images against the comparison fonts and rebalance the arm or cap the cut.
- [ ] Extend `ccmp_Other_2` to swap `dblgravecomb` for `dblgravecomb.narrow` when `i` or `r` also has a mark below (`e94446ae`): `ị̏`, `į̏`, `ɨ̏` and `ṛ̏` currently shape with the full-width double grave.
- [ ] Sync documentation and minor test omissions from `v0.4.0` to `0.6.0` (`ff40a587`, `3a08b870`, `e94446ae`, `62373181`, `3bfd1e22`, `f1a8c0cb`): drop `(unreleased; ...)` on the completed case-forms line in `ROADMAP.md`; remove `ȉ ȑ` from the `test_diagonal_gaps.py` list in `ARCHITECTURE.md`; update `docs/design-decisions.md` F18 and `tests/test_dashes.py` docstring (no longer case-only `calt`); add a `docs/design-decisions.md` row for the four space characters; add the spaces and `case` feature to `README.md` and resolve the "no `calt`" em-dash wording; clarify the `0.5.1` `CHANGELOG.md` sentence ("The others"); and remove the unnecessary `if name != "emdash"` skip in `tests/test_case_forms.py`.
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
